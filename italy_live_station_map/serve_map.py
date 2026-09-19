#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "data" / "station_history.sqlite"
CACHE = HERE / "cache"

PRICE_URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
STATION_URL = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SYNC_LOCK = threading.Lock()
SYNC_RETRY_SECONDS = 6 * 60 * 60


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS stations(
      station_id TEXT PRIMARY KEY,
      address TEXT,
      comune TEXT,
      provincia TEXT,
      road_type TEXT,
      lat REAL,
      lon REAL,
      registry_date TEXT,
      captured_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_stations_latlon ON stations(lat, lon);

    -- Only the newest nationwide snapshot lives here.
    CREATE TABLE IF NOT EXISTS current_prices(
      station_id TEXT NOT NULL,
      fuel TEXT NOT NULL,
      is_self INTEGER NOT NULL,
      price REAL NOT NULL,
      communicated_at TEXT,
      observed_date TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      PRIMARY KEY(station_id, fuel, is_self)
    );
    CREATE INDEX IF NOT EXISTS idx_current_prices_lookup
      ON current_prices(fuel,is_self,observed_date);

    -- Historical rows are retained only for tracked/local stations
    -- plus explicit quarterly-archive imports.
    CREATE TABLE IF NOT EXISTS prices(
      station_id TEXT NOT NULL,
      observed_date TEXT NOT NULL,
      fuel TEXT NOT NULL,
      is_self INTEGER NOT NULL,
      price REAL NOT NULL,
      communicated_at TEXT,
      source TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      PRIMARY KEY(station_id, observed_date, fuel, is_self, source)
    );
    CREATE INDEX IF NOT EXISTS idx_prices_lookup
      ON prices(station_id, fuel, is_self, observed_date);

    CREATE TABLE IF NOT EXISTS tracked_stations(
      station_id TEXT PRIMARY KEY,
      first_seen TEXT NOT NULL,
      last_seen TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sync_state(
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
    """)
    con.commit()
    con.close()


def parse_extract_date(first_line: str) -> str:
    m = ISO_DATE.search(first_line or "")
    if not m:
        raise ValueError(
            "Could not parse extraction date from the first CSV line: "
            + repr(first_line[:200])
        )
    return m.group(1)


def download(url: str, timeout: float = 90, accept: str = "text/csv,*/*;q=0.8") -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ItalyFuelPriceMap/8.0",
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def csv_reader(blob: bytes):
    txt = io.TextIOWrapper(
        io.BytesIO(blob), encoding="utf-8-sig", errors="replace", newline=""
    )
    first = txt.readline()
    extraction_date = parse_extract_date(first)
    delimiter = "|" if extraction_date >= "2026-02-10" else ";"
    return extraction_date, csv.DictReader(txt, delimiter=delimiter)


def field_map(reader):
    return {str(x).strip().lower(): x for x in (reader.fieldnames or [])}


def first_field(fields, *names):
    for name in names:
        if name in fields:
            return fields[name]
    return None


def fnum(x):
    try:
        return float(str(x).strip().replace(",", "."))
    except Exception:
        return None


def ingest_registry(blob: bytes):
    extraction, reader = csv_reader(blob)
    fields = field_map(reader)
    id_col = first_field(fields, "idimpianto")
    addr_col = first_field(fields, "indirizzo")
    comune_col = first_field(fields, "comune")
    provincia_col = first_field(fields, "provincia")
    lat_col = first_field(fields, "latitudine", "latitude", "lat")
    lon_col = first_field(fields, "longitudine", "longitude", "lon", "lng")
    road_col = first_field(fields, "tipo impianto", "tipo_impianto", "tipoimpianto")
    required = [id_col, addr_col, comune_col, provincia_col, lat_col, lon_col]
    if any(x is None for x in required):
        raise ValueError("Unexpected station-registry header: " + repr(reader.fieldnames))

    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for r in reader:
        station_id = str(r.get(id_col, "")).strip()
        lat, lon = fnum(r.get(lat_col)), fnum(r.get(lon_col))
        if not station_id or lat is None or lon is None:
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        rows.append((
            station_id,
            str(r.get(addr_col, "")).strip(),
            str(r.get(comune_col, "")).strip(),
            str(r.get(provincia_col, "")).strip(),
            str(r.get(road_col, "")).strip() if road_col else "",
            lat, lon, extraction, now
        ))

    con = sqlite3.connect(DB)
    con.execute("DELETE FROM stations")
    con.executemany("""
      INSERT INTO stations
      (station_id,address,comune,provincia,road_type,lat,lon,registry_date,captured_at)
      VALUES(?,?,?,?,?,?,?,?,?)
    """, rows)
    con.execute("INSERT OR REPLACE INTO sync_state(key,value) VALUES('registry_date',?)", (extraction,))
    con.commit()
    con.close()
    return extraction, len(rows)


def ingest_prices(blob: bytes):
    extraction, reader = csv_reader(blob)
    fields = field_map(reader)
    id_col = first_field(fields, "idimpianto")
    fuel_col = first_field(fields, "desccarburante")
    price_col = first_field(fields, "prezzo")
    self_col = first_field(fields, "isself")
    communicated_col = first_field(fields, "dtcomu")
    required = [id_col, fuel_col, price_col, self_col, communicated_col]
    if any(x is None for x in required):
        raise ValueError("Unexpected price-file header: " + repr(reader.fieldnames))

    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for r in reader:
        station_id = str(r.get(id_col, "")).strip()
        fuel = str(r.get(fuel_col, "")).strip()
        price = fnum(r.get(price_col))
        try:
            is_self = int(str(r.get(self_col, "")).strip())
        except Exception:
            continue
        if not station_id or not fuel or price is None or is_self not in (0, 1):
            continue
        rows.append((
            station_id, fuel, is_self, price,
            str(r.get(communicated_col, "")).strip(),
            extraction, now
        ))

    con = sqlite3.connect(DB)
    con.execute("DELETE FROM current_prices")
    con.executemany("""
      INSERT INTO current_prices
      (station_id,fuel,is_self,price,communicated_at,observed_date,captured_at)
      VALUES(?,?,?,?,?,?,?)
    """, rows)

    # Retain history only for already-tracked stations.
    con.execute("""
      INSERT OR REPLACE INTO prices
      (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
      SELECT c.station_id,c.observed_date,c.fuel,c.is_self,c.price,c.communicated_at,
             'mimit_08_tracked',c.captured_at
      FROM current_prices c
      JOIN tracked_stations t ON t.station_id=c.station_id
    """)

    con.execute("INSERT OR REPLACE INTO sync_state(key,value) VALUES('price_date',?)", (extraction,))
    con.execute("INSERT OR REPLACE INTO sync_state(key,value) VALUES('last_sync',?)", (now,))
    con.commit()
    con.close()
    return extraction, len(rows)


def sync_current(save_raw: bool = True):
    init_db()
    CACHE.mkdir(parents=True, exist_ok=True)
    with SYNC_LOCK:
        registry_blob = download(STATION_URL)
        price_blob = download(PRICE_URL)
        if save_raw:
            (CACHE / "anagrafica_impianti_attivi.csv").write_bytes(registry_blob)
            (CACHE / "prezzo_alle_8.csv").write_bytes(price_blob)
        registry_date, nstations = ingest_registry(registry_blob)
        price_date, nprices = ingest_prices(price_blob)
    return {
        "registry_date": registry_date,
        "price_date": price_date,
        "stations": nstations,
        "price_rows": nprices,
    }


def _parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except Exception:
        return None


def sync_state():
    init_db()
    con = sqlite3.connect(DB)
    state = dict(con.execute("SELECT key,value FROM sync_state").fetchall())
    state["station_rows"] = con.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
    state["current_price_rows"] = con.execute("SELECT COUNT(*) FROM current_prices").fetchone()[0]
    hist = con.execute("SELECT MIN(observed_date),MAX(observed_date),COUNT(DISTINCT observed_date) FROM prices").fetchone()
    state["history_start"] = hist[0]
    state["history_end"] = hist[1]
    state["history_days"] = hist[2] or 0
    state["tracked_station_rows"] = con.execute("SELECT COUNT(*) FROM tracked_stations").fetchone()[0]
    con.close()
    return state


def ensure_current():
    init_db()
    state = sync_state()
    warning = None
    need_data = (
        not state.get("price_date")
        or not state.get("registry_date")
        or state.get("station_rows", 0) == 0
        or state.get("current_price_rows", 0) == 0
    )
    last_sync = _parse_iso_datetime(state.get("last_sync"))
    refresh_due = last_sync is None or (datetime.now() - last_sync).total_seconds() >= SYNC_RETRY_SECONDS
    if need_data or refresh_due:
        try:
            sync_current(save_raw=True)
        except Exception as e:
            warning = f"Live MIMIT CSV refresh failed; using cache if available: {e}"
        state = sync_state()

    if (
        not state.get("price_date")
        or not state.get("registry_date")
        or state.get("station_rows", 0) == 0
        or state.get("current_price_rows", 0) == 0
    ):
        raise RuntimeError(
            (warning + " ; " if warning else "")
            + "No cached MIMIT snapshot is available. Run `python3 sync_current.py` while online."
        )
    return state, warning


def haversine_km(lat1, lon1, lat2, lon2):
    earth = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dlat/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
    return 2*earth*math.asin(math.sqrt(h))


def track_station_ids(station_ids):
    station_ids = [str(x) for x in station_ids if str(x)]
    if not station_ids:
        return
    now = datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    con.executemany("""
      INSERT INTO tracked_stations(station_id,first_seen,last_seen)
      VALUES(?,?,?)
      ON CONFLICT(station_id) DO UPDATE SET last_seen=excluded.last_seen
    """, [(sid, now, now) for sid in station_ids])

    # Capture the current day's prices immediately for newly viewed stations.
    con.execute("""
      INSERT OR REPLACE INTO prices
      (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
      SELECT c.station_id,c.observed_date,c.fuel,c.is_self,c.price,c.communicated_at,
             'mimit_08_tracked',c.captured_at
      FROM current_prices c
      JOIN tracked_stations t ON t.station_id=c.station_id
    """)
    con.commit()
    con.close()


def nearby(lat, lon, radius, fuel, want_self):
    state, warning = ensure_current()
    dlat = radius/111.0
    dlon = radius/(111.0*max(0.2, math.cos(math.radians(lat))))
    con = sqlite3.connect(DB)
    rows = con.execute("""
      SELECT s.station_id,s.lat,s.lon,s.address,s.comune,s.provincia,s.road_type,
             p.price,p.communicated_at,p.observed_date
      FROM stations s
      JOIN current_prices p ON p.station_id=s.station_id
      WHERE lower(p.fuel)=lower(?)
        AND p.is_self=?
        AND s.lat BETWEEN ? AND ?
        AND s.lon BETWEEN ? AND ?
    """, (
        fuel, 1 if want_self else 0,
        lat-dlat, lat+dlat, lon-dlon, lon+dlon
    )).fetchall()
    con.close()

    out = []
    for sid,slat,slon,address,comune,provincia,road_type,price,communicated,observed in rows:
        distance = haversine_km(lat,lon,slat,slon)
        if distance <= radius:
            out.append({
                "id":sid,"lat":slat,"lon":slon,
                "address":", ".join(x for x in [address,comune,provincia] if x),
                "road_type":road_type,"price":price,"updated":communicated,
                "observed_date":observed,"fuel":fuel,"isSelf":want_self,
                "distance_km":round(distance,3)
            })

    # Anything actually viewed becomes lightweight rolling-history scope.
    track_station_ids([x["id"] for x in out])

    out.sort(key=lambda x:(x["price"],x["distance_km"]))
    state = sync_state()
    return out, state, warning


def history(station_id, fuel, want_self, days):
    init_db()
    con = sqlite3.connect(DB)
    latest = con.execute("""
      SELECT MAX(observed_date) FROM prices
      WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
    """, (station_id,fuel,1 if want_self else 0)).fetchone()[0]

    if not latest:
        con.close()
        return {
            "points":[],"requested_days":days,"observed_days":0,"missing_days":days,
            "start":None,"end":None,"available_total_days":0,
            "available_start":None,"available_end":None,"interpolated":False
        }

    end = date.fromisoformat(latest)
    start = end - timedelta(days=days-1)
    rows = con.execute("""
      SELECT observed_date,price,source,communicated_at
      FROM prices
      WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
        AND observed_date BETWEEN ? AND ?
      ORDER BY observed_date
    """, (station_id,fuel,1 if want_self else 0,start.isoformat(),end.isoformat())).fetchall()

    overall = con.execute("""
      SELECT MIN(observed_date),MAX(observed_date),COUNT(DISTINCT observed_date)
      FROM prices
      WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
    """, (station_id,fuel,1 if want_self else 0)).fetchone()
    con.close()

    precedence = {"mimit_08_archive":0,"mimit_08_tracked":1,"mimit_08_current":1}
    by_date = {}
    for observed,price,source,communicated in rows:
        item={"date":observed,"price":price,"source":source,"communicated_at":communicated}
        if observed not in by_date or precedence.get(source,9)<precedence.get(by_date[observed]["source"],9):
            by_date[observed]=item

    points=[by_date[k] for k in sorted(by_date)]
    return {
        "points":points,
        "requested_days":days,
        "observed_days":len(points),
        "missing_days":max(0,days-len(points)),
        "start":start.isoformat(),"end":end.isoformat(),
        "available_total_days":overall[2] or 0,
        "available_start":overall[0],"available_end":overall[1],
        "interpolated":False
    }


def geocode(query, lang="en"):
    query=(query or "").strip()
    if not query:
        return []
    params=urllib.parse.urlencode({
        "q":query,"format":"jsonv2","limit":6,"countrycodes":"it",
        "addressdetails":1,"accept-language":lang
    })
    req=urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent":"ItalyFuelPriceMap/8.0 local-map-search","Accept":"application/json"}
    )
    with urllib.request.urlopen(req,timeout=20) as r:
        raw=json.loads(r.read().decode("utf-8"))
    out=[]
    for item in raw:
        try:
            lat=float(item["lat"]);lon=float(item["lon"])
        except Exception:
            continue
        out.append({
            "display_name":item.get("display_name",""),
            "lat":lat,"lon":lon,"type":item.get("type",""),
            "boundingbox":item.get("boundingbox") or []
        })
    return out


def auto_sync_loop(hours):
    if hours <= 0:
        return
    interval=max(1800,int(hours*3600))
    while True:
        time.sleep(interval)
        try:
            sync_current(save_raw=True)
            print("[auto-sync] current MIMIT snapshot refreshed",flush=True)
        except Exception as e:
            print(f"[auto-sync] refresh failed: {e}",flush=True)


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        relative=Path(urllib.parse.urlparse(path).path.lstrip("/"))
        return str((HERE/relative).resolve())

    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        q=urllib.parse.parse_qs(u.query)

        if u.path=="/api/stations":
            try:
                lat=float(q.get("lat",["43.9303"])[0])
                lon=float(q.get("lon",["10.9079"])[0])
                radius=max(1.0,min(25.0,float(q.get("radius",["5"])[0])))
                fuel=q.get("fuel",["Gasolio"])[0]
                want_self=q.get("self",["1"])[0]=="1"
                rows,state,warning=nearby(lat,lon,radius,fuel,want_self)
                self._json(200,{
                    "ok":True,"stations":rows,
                    "backend":"MIMIT current CSVs + local filtered history",
                    "price_date":state.get("price_date"),
                    "registry_date":state.get("registry_date"),
                    "history_days":state.get("history_days",0),
                    "history_start":state.get("history_start"),
                    "history_end":state.get("history_end"),
                    "tracked_station_rows":state.get("tracked_station_rows",0),
                    "warning":warning
                })
            except Exception as e:
                self._json(502,{"ok":False,"error":str(e)})
            return

        if u.path=="/api/history":
            try:
                sid=q.get("id",[""])[0]
                fuel=q.get("fuel",["Gasolio"])[0]
                want_self=q.get("self",["1"])[0]=="1"
                days=max(1,min(365,int(q.get("days",["7"])[0])))
                self._json(200,{"ok":True,**history(sid,fuel,want_self,days)})
            except Exception as e:
                self._json(500,{"ok":False,"error":str(e)})
            return

        if u.path=="/api/geocode":
            try:
                self._json(200,{"ok":True,"results":geocode(q.get("q",[""])[0],q.get("lang",["en"])[0])})
            except Exception as e:
                self._json(502,{"ok":False,"error":str(e)})
            return

        if u.path=="/api/sync":
            try:
                result=sync_current(save_raw=True)
                self._json(200,{"ok":True,**result,**sync_state()})
            except Exception as e:
                self._json(502,{"ok":False,"error":str(e)})
            return

        if u.path=="/api/state":
            self._json(200,{"ok":True,**sync_state()})
            return

        if u.path=="/":
            self.path="/index.html"
        return super().do_GET()

    def _json(self,status,obj):
        data=json.dumps(obj,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    p=argparse.ArgumentParser(description="Serve the local MIMIT station-price map.")
    p.add_argument("--host",default="127.0.0.1")
    p.add_argument("--port",type=int,default=8000)
    p.add_argument("--sync-first",action="store_true")
    p.add_argument("--auto-sync-hours",type=float,default=6.0)
    args=p.parse_args()

    init_db()
    if args.sync_first:
        print("Synchronized:",sync_current(save_raw=True))

    if args.auto_sync_hours>0:
        threading.Thread(target=auto_sync_loop,args=(args.auto_sync_hours,),daemon=True).start()

    server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f"Serving map at http://{args.host}:{args.port}")
    print(f"Package directory: {HERE}")
    print(f"SQLite database:   {DB}")
    print("The nationwide table keeps only the newest snapshot.")
    print("Rolling history is retained only for stations in areas you actually view.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__=="__main__":
    main()
