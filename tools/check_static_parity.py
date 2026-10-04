#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROBES = (
    ("Roma", 41.9028, 12.4964, 8.0, "Benzina", True),
    ("Milano", 45.4642, 9.1900, 8.0, "Benzina", True),
    ("Napoli", 40.8518, 14.2681, 8.0, "Gasolio", True),
    ("Torino", 45.0703, 7.6869, 8.0, "Benzina", False),
    ("Bologna", 44.4949, 11.3426, 8.0, "Gasolio", False),
)


class ParityError(RuntimeError):
    pass


@dataclass(frozen=True)
class Probe:
    name: str
    lat: float
    lon: float
    radius: float
    fuel: str
    self_service: bool


def import_builder(repo_root: Path):
    path = repo_root / "tools" / "build_web_data.py"
    spec = importlib.util.spec_from_file_location("parity_build_web_data", path)
    if spec is None or spec.loader is None:
        raise ParityError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def import_services(repo_root: Path):
    station_map = str(repo_root / "station_map")
    if station_map not in sys.path:
        sys.path.insert(0, station_map)
    from fuelmap import services
    return services


def find_repo_root(explicit: str | None = None) -> Path:
    root = (
        Path(explicit).expanduser().resolve()
        if explicit
        else Path(__file__).resolve().parents[1]
    )
    if not (root / "station_map" / "fuelmap" / "services.py").is_file():
        raise ParityError(f"Not an italy-fuel-price repository: {root}")
    return root


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ParityError(f"Could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ParityError(f"Expected JSON object: {path}")
    return value


def canonical(item: dict) -> tuple:
    return (
        str(item["id"]),
        round(float(item["lat"]), 6),
        round(float(item["lon"]), 6),
        str(item.get("address") or ""),
        str(item.get("road_type") or ""),
        round(float(item["price"]), 6),
        str(item.get("updated") or ""),
        str(item.get("observed_date") or ""),
        str(item["fuel"]),
        bool(item["isSelf"]),
        round(float(item["distance_km"]), 3),
    )


def direct_results(
    station_rows: list[tuple],
    price_rows: list[tuple],
    probe: Probe,
    services,
) -> list[dict]:
    stations = {}
    for row in station_rows:
        (
            sid,
            address,
            comune,
            provincia,
            road_type,
            lat,
            lon,
            _registry_date,
            _captured,
        ) = row
        stations[str(sid)] = {
            "lat": float(lat),
            "lon": float(lon),
            "address": ", ".join(
                value
                for value in (
                    str(address).strip(),
                    str(comune).strip(),
                    str(provincia).strip(),
                )
                if value
            ),
            "road_type": str(road_type).strip(),
        }

    selected_prices = {}
    for row in price_rows:
        (
            sid,
            fuel,
            is_self,
            price,
            communicated,
            observed,
            _captured,
        ) = row
        if str(fuel).strip().casefold() != probe.fuel.casefold():
            continue
        if bool(int(is_self)) != probe.self_service:
            continue
        key = str(sid)
        if key in selected_prices:
            raise ParityError(
                f"{probe.name}: duplicate local price key for station {key}, "
                f"{probe.fuel}, self={probe.self_service}"
            )
        selected_prices[key] = {
            "price": float(price),
            "updated": str(communicated).strip(),
            "observed_date": str(observed).strip(),
        }

    out = []
    for sid, price in selected_prices.items():
        station = stations.get(sid)
        if station is None:
            continue
        distance = services.haversine_km(
            probe.lat,
            probe.lon,
            station["lat"],
            station["lon"],
        )
        if distance > probe.radius:
            continue
        out.append(
            {
                "id": sid,
                "lat": station["lat"],
                "lon": station["lon"],
                "address": station["address"],
                "road_type": station["road_type"],
                "price": price["price"],
                "updated": price["updated"],
                "observed_date": price["observed_date"],
                "fuel": probe.fuel,
                "isSelf": probe.self_service,
                "distance_km": round(distance, 3),
            }
        )
    out.sort(key=lambda item: (item["price"], item["distance_km"]))
    return out


def bbox_cell_keys(
    lat: float,
    lon: float,
    radius: float,
    size: float,
    available: set[str],
) -> list[str]:
    dlat = radius / 111.0
    dlon = radius / (111.0 * max(0.2, math.cos(math.radians(lat))))
    imin = math.floor((lat - dlat) / size)
    imax = math.floor((lat + dlat) / size)
    jmin = math.floor((lon - dlon) / size)
    jmax = math.floor((lon + dlon) / size)
    keys = []
    for i in range(imin, imax + 1):
        for j in range(jmin, jmax + 1):
            key = f"{i}_{j}"
            if key in available:
                keys.append(key)
    return keys


def static_results(data_dir: Path, probe: Probe, services) -> list[dict]:
    metadata = load_json(data_dir / "metadata.json")
    grid = metadata.get("grid") or {}
    size = float(grid.get("size_degrees") or 0.5)
    available = {str(key) for key in grid.get("cells") or []}
    keys = bbox_cell_keys(
        probe.lat, probe.lon, probe.radius, size, available
    )
    out = []
    for key in keys:
        payload = load_json(data_dir / "cells" / f"{key}.json")
        for station in payload.get("stations") or []:
            price = next(
                (
                    item
                    for item in station.get("prices") or []
                    if item.get("fuel") == probe.fuel
                    and bool(item.get("self")) == probe.self_service
                ),
                None,
            )
            if price is None:
                continue
            distance = services.haversine_km(
                probe.lat,
                probe.lon,
                float(station["lat"]),
                float(station["lon"]),
            )
            if distance > probe.radius:
                continue
            out.append(
                {
                    "id": str(station["id"]),
                    "lat": float(station["lat"]),
                    "lon": float(station["lon"]),
                    "address": station.get("address") or "",
                    "road_type": station.get("road_type") or "",
                    "price": float(price["price"]),
                    "updated": price.get("updated") or "",
                    "observed_date": metadata.get("price_date") or "",
                    "fuel": probe.fuel,
                    "isSelf": probe.self_service,
                    "distance_km": round(distance, 3),
                }
            )
    out.sort(key=lambda item: (item["price"], item["distance_km"]))
    return out


def boundary_probes(records: list[dict], count: int = 4) -> list[Probe]:
    candidates = []
    for station in records:
        lat = float(station["lat"])
        lon = float(station["lon"])
        lat_edge = round(lat * 2) / 2
        lon_edge = round(lon * 2) / 2
        lat_delta = abs(lat - lat_edge)
        lon_delta = abs(lon - lon_edge)
        edge_delta = min(lat_delta, lon_delta)
        if edge_delta > 0.03:
            continue
        if not station.get("prices"):
            continue
        price = station["prices"][0]
        candidates.append(
            (
                edge_delta,
                str(station["id"]),
                Probe(
                    name=f"grid-edge-{station['id']}",
                    lat=lat_edge if lat_delta <= lon_delta else lat,
                    lon=lon if lat_delta <= lon_delta else lon_edge,
                    radius=7.0,
                    fuel=str(price["fuel"]),
                    self_service=bool(price["self"]),
                ),
            )
        )
    candidates.sort(key=lambda item: (item[0], item[1]))
    selected = []
    seen_cells = set()
    for _delta, _sid, probe in candidates:
        signature = (round(probe.lat * 2), round(probe.lon * 2))
        if signature in seen_cells:
            continue
        seen_cells.add(signature)
        selected.append(probe)
        if len(selected) >= count:
            break
    if not selected:
        raise ParityError("Could not derive any populated grid-boundary probes")
    return selected


def compare_probe(
    station_rows: list[tuple],
    price_rows: list[tuple],
    data_dir: Path,
    probe: Probe,
    services,
) -> dict:
    local = direct_results(station_rows, price_rows, probe, services)
    static = static_results(data_dir, probe, services)
    local_c = [canonical(item) for item in local]
    static_c = [canonical(item) for item in static]
    if local_c != static_c:
        local_set = set(local_c)
        static_set = set(static_c)
        only_local = sorted(local_set - static_set)[:5]
        only_static = sorted(static_set - local_set)[:5]
        raise ParityError(
            f"{probe.name}: parity mismatch "
            f"(local={len(local_c)}, static={len(static_c)}); "
            f"only-local={only_local!r}; only-static={only_static!r}"
        )
    return {
        "name": probe.name,
        "stations": len(local_c),
        "fuel": probe.fuel,
        "self": probe.self_service,
        "radius_km": probe.radius,
    }


def run_check(
    repo_root: Path,
    registry_file: Path,
    price_file: Path,
    data_dir: Path,
) -> list[dict]:
    builder = import_builder(repo_root)
    services = import_services(repo_root)

    registry_blob = registry_file.read_bytes()
    price_blob = price_file.read_bytes()
    mimit, _price_url, _station_url = builder.import_mimit(repo_root)
    registry_date, station_rows = mimit.parse_registry(registry_blob)
    price_date, price_rows, _captured = mimit.parse_prices(price_blob)
    records, counts = builder.normalize_current(station_rows, price_rows)
    builder.validate_snapshot(counts)

    metadata = load_json(data_dir / "metadata.json")
    if metadata.get("registry_date") != registry_date:
        raise ParityError(
            "Generated data registry date does not match supplied registry file"
        )
    if metadata.get("price_date") != price_date:
        raise ParityError(
            "Generated data price date does not match supplied price file"
        )

    probes = [Probe(*item) for item in DEFAULT_PROBES]
    probes.extend(boundary_probes(records))
    return [
        compare_probe(station_rows, price_rows, data_dir, probe, services)
        for probe in probes
    ]


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Compare local current-snapshot semantics with generated static cells."
    )
    ap.add_argument("--repo-root", help="Repository root; normally auto-detected.")
    ap.add_argument("--registry-file", required=True)
    ap.add_argument("--price-file", required=True)
    ap.add_argument("--data-dir", required=True)
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        results = run_check(
            find_repo_root(args.repo_root),
            Path(args.registry_file).expanduser().resolve(),
            Path(args.price_file).expanduser().resolve(),
            Path(args.data_dir).expanduser().resolve(),
        )
    except (ParityError, OSError) as exc:
        print(f"error: {exc}")
        return 2

    print("Static/local station parity: OK")
    for item in results:
        mode = "self" if item["self"] else "served"
        print(
            f"- {item['name']}: {item['stations']} stations, "
            f"{item['fuel']} {mode}, {item['radius_km']:g} km"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
