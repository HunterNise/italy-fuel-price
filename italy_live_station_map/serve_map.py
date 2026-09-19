#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent

NEW_API = "https://carburanti.mise.gov.it/ospzApi/search/zone"
OLD_API = "https://carburanti.mise.gov.it/OssPrezziSearch/ricerca/position"

FUEL_IDS = {
    "Benzina": "1",
    "Gasolio": "2",
    "GPL": "3",
    "Metano": "4",
}

def _post_json(url: str, obj: dict, timeout: float = 20):
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ItalyFuelPriceMap/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _post_form(url: str, fields: dict, timeout: float = 20):
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "ItalyFuelPriceMap/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _as_float(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

def _normalize(raw, fuel: str, want_self: bool):
    arr = raw.get("array") if isinstance(raw, dict) else None
    if arr is None and isinstance(raw, list):
        arr = raw
    if arr is None:
        arr = raw.get("results", []) if isinstance(raw, dict) else []

    out = []
    for s in arr or []:
        lat = _as_float(s.get("lat"))
        lon = _as_float(s.get("lon", s.get("lng")))
        if lat is None or lon is None:
            continue

        prices = s.get("carburanti") or s.get("fuels") or []
        selected = []
        for p in prices:
            carb = str(p.get("carb", p.get("fuel", ""))).strip()
            if carb.lower() != fuel.lower():
                continue
            try:
                is_self = bool(int(p.get("isSelf", p.get("self", 0))))
            except Exception:
                is_self = bool(p.get("isSelf", p.get("self", False)))
            if is_self != want_self:
                continue
            price = _as_float(p.get("prezzo", p.get("price")))
            if price is not None:
                selected.append(price)

        if not selected:
            continue

        # There should normally be one matching record. Use the lowest if duplicates occur.
        price = min(selected)
        out.append({
            "id": s.get("id"),
            "lat": lat,
            "lon": lon,
            "address": s.get("addr", s.get("address", "")),
            "updated": s.get("dIns", s.get("updated", "")),
            "fuel": fuel,
            "isSelf": want_self,
            "price": price,
        })
    return out

def fetch_live(lat: float, lon: float, radius: float, fuel: str, want_self: bool):
    errors = []

    # Current public endpoint documented in a recent implementation article.
    try:
        raw = _post_json(
            NEW_API,
            {"points": [{"lat": str(lat), "lng": str(lon)}], "radius": radius},
        )
        rows = _normalize(raw, fuel, want_self)
        if rows:
            return rows, "MIMIT ospzApi/search/zone"
        errors.append("new API returned no matching stations")
    except Exception as e:
        errors.append(f"new API: {e}")

    # Older documented Osservaprezzi API as a fallback.
    try:
        carb = f"{FUEL_IDS.get(fuel, '2')}-x"
        raw = _post_form(
            OLD_API,
            {
                "pointsListStr": f"{lat}-{lon}#",
                "carb": carb,
                "ordPrice": "asc",
            },
        )
        rows = _normalize(raw, fuel, want_self)
        if rows:
            return rows, "MIMIT OssPrezziSearch/ricerca/position"
        errors.append("old API returned no matching stations")
    except Exception as e:
        errors.append(f"old API: {e}")

    raise RuntimeError(" ; ".join(errors))

def demo_rows(lat: float, lon: float, radius: float, fuel: str, want_self: bool):
    # Synthetic only, for testing the UI without network.
    rng = random.Random(17 + hash((fuel, want_self)) % 1000)
    base = {"Benzina": 2.15, "Gasolio": 2.33, "GPL": 0.75, "Metano": 2.02}.get(fuel, 2.0)
    rows=[]
    for i in range(28):
        angle = rng.random()*2*math.pi
        dist = radius*math.sqrt(rng.random())*0.0087
        dx = dist*math.cos(angle)/max(math.cos(math.radians(lat)), .3)
        dy = dist*math.sin(angle)
        rows.append({
            "id": f"DEMO-{i+1:03d}",
            "lat": lat+dy,
            "lon": lon+dx,
            "address": "Synthetic demo point — not a real station",
            "updated": "",
            "fuel": fuel,
            "isSelf": want_self,
            "price": round(base + rng.uniform(-.08,.08), 3),
        })
    return rows

class Handler(SimpleHTTPRequestHandler):
    demo = False

    def translate_path(self, path):
        # Always serve files from the package directory.
        old = super().translate_path(path)
        rel = Path(old).relative_to(Path.cwd())
        return str(HERE / rel)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/stations":
            q = urllib.parse.parse_qs(u.query)
            try:
                lat = float(q.get("lat", ["43.9303"])[0])
                lon = float(q.get("lon", ["10.9079"])[0])
                radius = max(1.0, min(10.0, float(q.get("radius", ["5"])[0])))
                fuel = q.get("fuel", ["Gasolio"])[0]
                want_self = q.get("self", ["1"])[0] == "1"

                if self.demo:
                    rows = demo_rows(lat, lon, radius, fuel, want_self)
                    backend = "synthetic demo"
                else:
                    rows, backend = fetch_live(lat, lon, radius, fuel, want_self)

                self._json(200, {"ok": True, "stations": rows, "backend": backend})
            except Exception as e:
                self._json(502, {"ok": False, "error": str(e)})
            return

        if u.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _json(self, status, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

def main():
    p = argparse.ArgumentParser(description="Serve the live Italian fuel-station price map.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--demo", action="store_true", help="Use synthetic data to test UI without MIMIT access.")
    args = p.parse_args()

    Handler.demo = args.demo
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    mode = "DEMO synthetic data" if args.demo else "LIVE MIMIT data"
    print(f"Serving {mode} at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
