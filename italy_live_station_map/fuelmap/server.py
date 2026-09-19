from __future__ import annotations

import argparse
import json
import threading
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from . import __version__
from . import db, mimit, services
from .config import DB, ROOT


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """Serve only files contained inside the project root."""
        relative = Path(urllib.parse.urlparse(path).path.lstrip("/"))
        candidate = (ROOT / relative).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            return str(ROOT / "__not_found__")
        return str(candidate)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)

        if url.path == "/api/stations":
            try:
                lat = float(query.get("lat", ["43.9303"])[0])
                lon = float(query.get("lon", ["10.9079"])[0])
                radius = max(1.0, min(25.0, float(query.get("radius", ["5"])[0])))
                fuel = query.get("fuel", ["Benzina"])[0]
                want_self = query.get("self", ["1"])[0] == "1"

                rows, state, warning = services.nearby(
                    lat, lon, radius, fuel, want_self
                )
                self._json(
                    200,
                    {
                        "ok": True,
                        "version": __version__,
                        "stations": rows,
                        "backend": "MIMIT current CSVs + local filtered history",
                        "price_date": state.get("price_date"),
                        "registry_date": state.get("registry_date"),
                        "history_days": state.get("history_days", 0),
                        "history_start": state.get("history_start"),
                        "history_end": state.get("history_end"),
                        "tracked_station_rows": state.get("tracked_station_rows", 0),
                        "warning": warning,
                    },
                )
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
            return

        if url.path == "/api/history":
            try:
                station_id = query.get("id", [""])[0]
                fuel = query.get("fuel", ["Benzina"])[0]
                want_self = query.get("self", ["1"])[0] == "1"
                days = max(1, min(365, int(query.get("days", ["7"])[0])))
                self._json(
                    200,
                    {
                        "ok": True,
                        "version": __version__,
                        **services.history(station_id, fuel, want_self, days),
                    },
                )
            except Exception as exc:
                self._json(500, {"ok": False, "error": str(exc)})
            return

        if url.path == "/api/geocode":
            try:
                self._json(
                    200,
                    {
                        "ok": True,
                        "version": __version__,
                        "results": services.geocode(
                            query.get("q", [""])[0],
                            query.get("lang", ["en"])[0],
                        ),
                    },
                )
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
            return

        if url.path == "/api/sync":
            try:
                result = mimit.sync_current(save_raw=True)
                self._json(
                    200,
                    {
                        "ok": True,
                        "version": __version__,
                        **result,
                        **db.sync_state(),
                    },
                )
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
            return

        if url.path == "/api/state":
            self._json(
                200,
                {"ok": True, "version": __version__, **db.sync_state()},
            )
            return

        if url.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def _json(self, status, payload):
        """Write JSON, treating a closed browser socket as a normal disconnect."""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # The browser navigated, reloaded, or superseded this request after
            # the server had already done the work. This is not a backend 5xx.
            self.close_connection = True
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Serve the local MIMIT station-price map."
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--sync-first", action="store_true")
    parser.add_argument("--auto-sync-hours", type=float, default=6.0)
    args = parser.parse_args()

    db.init_db()

    if args.sync_first:
        print("Synchronized:", mimit.sync_current(save_raw=True))

    if args.auto_sync_hours > 0:
        threading.Thread(
            target=services.auto_sync_loop,
            args=(args.auto_sync_hours,),
            daemon=True,
        ).start()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Italy Fuel Price Map {__version__}")
    print(f"Serving map at http://{args.host}:{args.port}")
    print(f"Package directory: {ROOT}")
    print(f"SQLite database:   {DB}")
    print("The nationwide table keeps only the newest snapshot.")
    print("Rolling history is retained only for stations in areas you actually view.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
