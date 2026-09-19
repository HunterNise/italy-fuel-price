#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "data" / "station_history.sqlite"

NEW_API = "https://carburanti.mise.gov.it/ospzApi/search/zone"
OLD_API = "https://carburanti.mise.gov.it/OssPrezziSearch/ricerca/position"

FUEL_IDS = {"Benzina":"1","Gasolio":"2","GPL":"3","Metano":"4"}

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
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
      )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_prices_lookup ON prices(station_id,fuel,is_self,observed_date)")
    con.commit()
    con.close()

def _post_json(url, obj, timeout=20):
    req = urllib.request.Request(
        url, data=json.dumps(obj).encode(), method="POST",
        headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"ItalyFuelPriceMap/2.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _post_form(url, fields, timeout=20):
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(fields).encode(), method="POST",
        headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json","User-Agent":"ItalyFuelPriceMap/2.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _as_float(x):
    try: return float(str(x).replace(",", "."))
    except Exception: return None

def _normalize(raw, fuel, want_self):
    arr = raw.get("array") if isinstance(raw, dict) else None
    if arr is None and isinstance(raw, list): arr = raw
    if arr is None: arr = raw.get("results", []) if isinstance(raw, dict) else []

    out=[]
    for s in arr or []:
        lat=_as_float(s.get("lat")); lon=_as_float(s.get("lon",s.get("lng")))
        if lat is None or lon is None: continue
        matches=[]
        for p in (s.get("carburanti") or s.get("fuels") or []):
            carb=str(p.get("carb",p.get("fuel",""))).strip()
            if carb.lower()!=fuel.lower(): continue
            try: is_self=bool(int(p.get("isSelf",p.get("self",0))))
            except Exception: is_self=bool(p.get("isSelf",p.get("self",False)))
            if is_self!=want_self: continue
            pr=_as_float(p.get("prezzo",p.get("price")))
            if pr is not None:
                matches.append((pr,p.get("dtComu",p.get("updated",""))))
        if not matches: continue
        pr, updated=min(matches,key=lambda x:x[0])
        out.append({
            "id":str(s.get("id","")),
            "lat":lat,"lon":lon,
            "address":s.get("addr",s.get("address","")),
            "updated":updated or s.get("dIns",""),
            "fuel":fuel,"isSelf":want_self,"price":pr,
        })
    return out

def fetch_live(lat, lon, radius, fuel, want_self):
    errors=[]
    try:
        raw=_post_json(NEW_API,{"points":[{"lat":str(lat),"lng":str(lon)}],"radius":radius})
        rows=_normalize(raw,fuel,want_self)
        if rows: return rows,"MIMIT ospzApi/search/zone"
        errors.append("new API returned no matching stations")
    except Exception as e: errors.append(f"new API: {e}")
    try:
        raw=_post_form(OLD_API,{"pointsListStr":f"{lat}-{lon}#","carb":f"{FUEL_IDS.get(fuel,'2')}-x","ordPrice":"asc"})
        rows=_normalize(raw,fuel,want_self)
        if rows: return rows,"MIMIT OssPrezziSearch/ricerca/position"
        errors.append("old API returned no matching stations")
    except Exception as e: errors.append(f"old API: {e}")
    raise RuntimeError(" ; ".join(errors))

def demo_rows(lat,lon,radius,fuel,want_self):
    rng=random.Random(17+sum(ord(c) for c in fuel)+int(want_self))
    base={"Benzina":2.15,"Gasolio":2.33,"GPL":0.75,"Metano":2.02}.get(fuel,2.0)
    rows=[]
    for i in range(28):
        angle=rng.random()*2*math.pi
        dist=radius*math.sqrt(rng.random())*0.0087
        dx=dist*math.cos(angle)/max(math.cos(math.radians(lat)),.3)
        dy=dist*math.sin(angle)
        rows.append({"id":f"DEMO-{i+1:03d}","lat":lat+dy,"lon":lon+dx,
                     "address":"Synthetic demo point — not a real station","updated":"",
                     "fuel":fuel,"isSelf":want_self,"price":round(base+rng.uniform(-.08,.08),3)})
    return rows

def record_capture(rows, source):
    """Rolling local history. This is a capture, not a substitute for the official 08:00 archive."""
    if not rows: return
    init_db()
    today=date.today().isoformat()
    now=datetime.now().isoformat(timespec="seconds")
    payload=[(r["id"],today,r["fuel"],1 if r["isSelf"] else 0,float(r["price"]),
              str(r.get("updated","")),source,now) for r in rows if r.get("id")]
    con=sqlite3.connect(DB_PATH)
    con.executemany("""
      INSERT OR REPLACE INTO prices
      (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
      VALUES(?,?,?,?,?,?,?,?)
    """,payload)
    con.commit(); con.close()

def history(station_id,fuel,want_self,days):
    init_db()
    end=date.today()
    start=end-timedelta(days=days-1)
    con=sqlite3.connect(DB_PATH)
    rows=con.execute("""
      SELECT observed_date,price,source,communicated_at
      FROM prices
      WHERE station_id=? AND fuel=? AND is_self=? AND observed_date BETWEEN ? AND ?
      ORDER BY observed_date, source
    """,(station_id,fuel,1 if want_self else 0,start.isoformat(),end.isoformat())).fetchall()
    con.close()

    precedence={"mimit_08_archive":0,"mimit_08_current":1,"live_api_capture":2,"synthetic_demo":9}
    by_date={}
    for d,p,src,comm in rows:
        item={"date":d,"price":p,"source":src,"communicated_at":comm}
        if d not in by_date or precedence.get(src,5)<precedence.get(by_date[d]["source"],5):
            by_date[d]=item
    data=[by_date[d] for d in sorted(by_date)]
    expected=days
    return {
        "points":data,
        "requested_days":days,
        "observed_days":len(data),
        "missing_days":max(0,expected-len(data)),
        "start":start.isoformat(),
        "end":end.isoformat(),
        "interpolated":False,
    }

class Handler(SimpleHTTPRequestHandler):
    demo=False

    def translate_path(self,path):
        raw=super().translate_path(path)
        try: rel=Path(raw).relative_to(Path.cwd())
        except Exception: rel=Path(urllib.parse.urlparse(path).path.lstrip("/"))
        return str(HERE/rel)

    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        q=urllib.parse.parse_qs(u.query)

        if u.path=="/api/stations":
            try:
                lat=float(q.get("lat",["43.9303"])[0]); lon=float(q.get("lon",["10.9079"])[0])
                radius=max(1,min(10,float(q.get("radius",["5"])[0])))
                fuel=q.get("fuel",["Gasolio"])[0]; want_self=q.get("self",["1"])[0]=="1"
                if self.demo:
                    rows=demo_rows(lat,lon,radius,fuel,want_self); backend="synthetic demo"
                    record_capture(rows,"synthetic_demo")
                else:
                    rows,backend=fetch_live(lat,lon,radius,fuel,want_self)
                    record_capture(rows,"live_api_capture")
                self._json(200,{"ok":True,"stations":rows,"backend":backend})
            except Exception as e: self._json(502,{"ok":False,"error":str(e)})
            return

        if u.path=="/api/history":
            try:
                sid=q.get("id",[""])[0]; fuel=q.get("fuel",["Gasolio"])[0]
                want_self=q.get("self",["1"])[0]=="1"
                days=max(7,min(365,int(q.get("days",["30"])[0])))
                self._json(200,{"ok":True,**history(sid,fuel,want_self,days)})
            except Exception as e: self._json(500,{"ok":False,"error":str(e)})
            return

        if u.path=="/": self.path="/index.html"
        return super().do_GET()

    def _json(self,status,obj):
        b=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",default="127.0.0.1")
    p.add_argument("--port",type=int,default=8000)
    p.add_argument("--demo",action="store_true")
    args=p.parse_args()
    init_db()
    Handler.demo=args.demo
    srv=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f"Serving {'DEMO' if args.demo else 'LIVE'} map at http://{args.host}:{args.port}")
    print(f"History DB: {DB_PATH}")
    print("Press Ctrl+C to stop.")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__=="__main__":
    main()
