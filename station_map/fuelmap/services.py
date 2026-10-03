from __future__ import annotations

import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime

from . import __version__
from . import db, mimit
from .config import GEOCODE_TIMEOUT_SECONDS, NOMINATIM_URL, SYNC_RETRY_SECONDS


def _parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except Exception:
        return None


def ensure_current() -> tuple[dict, str | None]:
    state = db.sync_state()
    warning = None

    need_data = (
        not state.get("price_date")
        or not state.get("registry_date")
        or state.get("station_rows", 0) == 0
        or state.get("current_price_rows", 0) == 0
    )
    last_sync = _parse_iso_datetime(state.get("last_sync"))
    refresh_due = (
        last_sync is None
        or (datetime.now() - last_sync).total_seconds() >= SYNC_RETRY_SECONDS
    )

    if need_data or refresh_due:
        try:
            mimit.sync_current(save_raw=True)
        except Exception as exc:
            warning = f"Live MIMIT CSV refresh failed; using cache if available: {exc}"
        state = db.sync_state()

    if (
        not state.get("price_date")
        or not state.get("registry_date")
        or state.get("station_rows", 0) == 0
        or state.get("current_price_rows", 0) == 0
    ):
        raise RuntimeError(
            (warning + " ; " if warning else "")
            + "No cached MIMIT snapshot is available. "
              "Run `python3 sync_current.py` while online."
        )
    return state, warning


def haversine_km(lat1, lon1, lat2, lon2):
    earth = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * earth * math.asin(math.sqrt(h))


def nearby(lat, lon, radius, fuel, want_self):
    state, warning = ensure_current()

    dlat = radius / 111.0
    dlon = radius / (111.0 * max(0.2, math.cos(math.radians(lat))))
    rows = db.nearby_candidates(
        fuel,
        want_self,
        lat - dlat,
        lat + dlat,
        lon - dlon,
        lon + dlon,
    )

    out = []
    for (
        sid,
        slat,
        slon,
        address,
        comune,
        provincia,
        road_type,
        price,
        communicated,
        observed,
    ) in rows:
        distance = haversine_km(lat, lon, slat, slon)
        if distance <= radius:
            out.append(
                {
                    "id": sid,
                    "lat": slat,
                    "lon": slon,
                    "address": ", ".join(
                        x for x in [address, comune, provincia] if x
                    ),
                    "road_type": road_type,
                    "price": price,
                    "updated": communicated,
                    "observed_date": observed,
                    "fuel": fuel,
                    "isSelf": want_self,
                    "distance_km": round(distance, 3),
                }
            )

    db.track_station_ids(x["id"] for x in out)
    out.sort(key=lambda x: (x["price"], x["distance_km"]))
    return out, db.sync_state(), warning


def history(station_id, fuel, want_self, days):
    return db.station_history(station_id, fuel, want_self, days)


def geocode(query: str, lang: str = "en"):
    query = (query or "").strip()
    if not query:
        return []

    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "limit": 6,
            "countrycodes": "it",
            "addressdetails": 1,
            "accept-language": lang,
        }
    )
    req = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={
            "User-Agent": f"ItalyFuelPriceMap/{__version__} local-map-search",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=GEOCODE_TIMEOUT_SECONDS) as response:
        raw = json.loads(response.read().decode("utf-8"))

    out = []
    for item in raw:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except Exception:
            continue
        out.append(
            {
                "display_name": item.get("display_name", ""),
                "lat": lat,
                "lon": lon,
                "type": item.get("type", ""),
                "boundingbox": item.get("boundingbox") or [],
            }
        )
    return out


def auto_sync_loop(hours: float):
    if hours <= 0:
        return
    interval = max(1800, int(hours * 3600))
    while True:
        time.sleep(interval)
        try:
            mimit.sync_current(save_raw=True)
            print("[auto-sync] current MIMIT snapshot refreshed", flush=True)
        except Exception as exc:
            print(f"[auto-sync] refresh failed: {exc}", flush=True)
