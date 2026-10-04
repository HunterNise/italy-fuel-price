#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TOOLS_DIR = str(Path(__file__).resolve().parent)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from istat_localities import (
    ISTAT_LOCALITIES_LICENSE,
    ISTAT_LOCALITIES_LICENSE_URL,
    ISTAT_LOCALITIES_REFERENCE_YEAR,
    ISTAT_LOCALITIES_URL,
    ISTAT_MUNICIPALITIES_2021_URL,
    LocalityError,
    attach_municipality_names,
    download_localities,
    download_municipalities_2021,
    parse_localities_archive,
    parse_municipalities_2021_archive,
)

SUPPORTED_FUELS = ("Benzina", "Gasolio", "GPL", "Metano")
GRID_SIZE_DEGREES = 0.5
HISTORY_WINDOW_DAYS = 7
SCHEMA_VERSION = 1
IODL_URL = "https://www.dati.gov.it/content/italian-open-data-license-v20"


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidationLimits:
    min_registry_stations: int = 20_000
    min_raw_price_rows: int = 70_000
    min_supported_stations: int = 18_000
    min_join_ratio: float = 0.97
    max_duplicate_supported_keys: int = 0


DEFAULT_LIMITS = ValidationLimits()


def find_repo_root(explicit: str | None = None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
    else:
        root = Path(__file__).resolve().parents[1]
    marker = root / "station_map" / "fuelmap" / "mimit.py"
    if not marker.exists():
        raise BuildError(f"Not an italy-fuel-price repository: {root}")
    return root


def import_mimit(repo_root: Path):
    station_map = str(repo_root / "station_map")
    if station_map not in sys.path:
        sys.path.insert(0, station_map)
    from fuelmap import mimit  # type: ignore
    from fuelmap.config import PRICE_URL, STATION_URL  # type: ignore

    return mimit, PRICE_URL, STATION_URL


def json_bytes(value, *, pretty: bool = False) -> bytes:
    kwargs = {"ensure_ascii": False, "sort_keys": False}
    if pretty:
        return (json.dumps(value, indent=2, **kwargs) + "\n").encode("utf-8")
    return (json.dumps(value, separators=(",", ":"), **kwargs) + "\n").encode("utf-8")


def write_json(path: Path, value, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value, pretty=pretty))


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def cell_indices(lat: float, lon: float, size: float = GRID_SIZE_DEGREES) -> tuple[int, int]:
    return math.floor(lat / size), math.floor(lon / size)


def cell_key(lat: float, lon: float, size: float = GRID_SIZE_DEGREES) -> str:
    i, j = cell_indices(lat, lon, size)
    return f"{i}_{j}"


def build_places(station_rows: list[tuple]) -> list[dict]:
    grouped: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for row in station_rows:
        _, _, comune, provincia, _, lat, lon, _, _ = row
        comune = str(comune).strip()
        provincia = str(provincia).strip()
        if comune:
            grouped[(comune, provincia)].append((float(lat), float(lon)))

    places = []
    ordered = sorted(
        grouped.items(),
        key=lambda item: (item[0][0].casefold(), item[0][1].casefold()),
    )
    for (comune, provincia), coords in ordered:
        lats = sorted(lat for lat, _ in coords)
        lons = sorted(lon for _, lon in coords)
        places.append(
            {
                "name": comune,
                "province": provincia,
                "lat": round(statistics.median(lats), 6),
                "lon": round(statistics.median(lons), 6),
                "station_count": len(coords),
            }
        )
    return places


def normalize_current(station_rows: list[tuple], price_rows: list[tuple]) -> tuple[list[dict], dict]:
    stations: dict[str, dict] = {}
    for row in station_rows:
        sid, address, comune, provincia, road_type, lat, lon, _registry_date, _captured = row
        sid = str(sid)
        stations[sid] = {
            "id": sid,
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
            "prices": [],
        }

    fuel_rank = {fuel: idx for idx, fuel in enumerate(SUPPORTED_FUELS)}
    price_map: dict[tuple[str, str, int], dict] = {}
    unsupported = defaultdict(int)
    duplicates = 0

    for sid, fuel, is_self, price, communicated, _observed, _captured in price_rows:
        sid = str(sid)
        fuel = str(fuel).strip()
        if fuel not in SUPPORTED_FUELS:
            unsupported[fuel] += 1
            continue
        key = (sid, fuel, int(is_self))
        if key in price_map:
            duplicates += 1
        price_map[key] = {
            "fuel": fuel,
            "self": bool(is_self),
            "price": float(price),
            "updated": str(communicated).strip(),
        }

    joined_price_rows = 0
    orphan_price_rows = 0
    for (sid, _fuel, _self), price in price_map.items():
        station = stations.get(sid)
        if station is None:
            orphan_price_rows += 1
            continue
        station["prices"].append(price)
        joined_price_rows += 1

    records = []
    for station in stations.values():
        if not station["prices"]:
            continue
        station["prices"].sort(
            key=lambda item: (fuel_rank[item["fuel"]], 1 if item["self"] else 0)
        )
        records.append(station)
    records.sort(key=lambda item: item["id"])

    counts = {
        "registry_stations": len(station_rows),
        "raw_price_rows": len(price_rows),
        "supported_price_keys": len(price_map),
        "joined_supported_price_rows": joined_price_rows,
        "orphan_supported_price_rows": orphan_price_rows,
        "stations_with_supported_prices": len(records),
        "duplicate_supported_keys": duplicates,
        "unsupported_fuel_rows": dict(
            sorted(unsupported.items(), key=lambda item: (-item[1], item[0]))
        ),
    }
    counts["join_ratio"] = (
        joined_price_rows / len(price_map) if price_map else 0.0
    )
    return records, counts


def validate_snapshot(counts: dict, limits: ValidationLimits = DEFAULT_LIMITS) -> None:
    failures = []
    if counts["registry_stations"] < limits.min_registry_stations:
        failures.append(
            f"registry station count {counts['registry_stations']:,} < {limits.min_registry_stations:,}"
        )
    if counts["raw_price_rows"] < limits.min_raw_price_rows:
        failures.append(
            f"raw price row count {counts['raw_price_rows']:,} < {limits.min_raw_price_rows:,}"
        )
    if counts["stations_with_supported_prices"] < limits.min_supported_stations:
        failures.append(
            "supported station count "
            f"{counts['stations_with_supported_prices']:,} < {limits.min_supported_stations:,}"
        )
    if counts["join_ratio"] < limits.min_join_ratio:
        failures.append(
            f"supported-price join ratio {counts['join_ratio']:.3%} < {limits.min_join_ratio:.1%}"
        )
    if counts["duplicate_supported_keys"] > limits.max_duplicate_supported_keys:
        failures.append(
            "duplicate supported station/fuel/service keys "
            f"{counts['duplicate_supported_keys']:,} > {limits.max_duplicate_supported_keys:,}"
        )
    if failures:
        raise BuildError("Snapshot validation failed: " + "; ".join(failures))


def prepare_output(path: Path, repo_root: Path) -> Path:
    path = path.expanduser().resolve()
    protected = {
        Path(path.anchor).resolve(),
        Path.home().resolve(),
        repo_root.resolve(),
        (repo_root / "station_map").resolve(),
        (repo_root / ".git").resolve(),
    }
    if path in protected or (path / ".git").exists():
        raise BuildError(f"Refusing to replace unsafe output directory: {path}")

    if path.exists():
        entries = list(path.iterdir())
        if entries:
            metadata_path = path / "metadata.json"
            try:
                previous = json.loads(metadata_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise BuildError(
                    f"Refusing to replace non-builder output directory {path}; "
                    "remove it explicitly first"
                ) from exc
            if previous.get("schema_version") != SCHEMA_VERSION:
                raise BuildError(
                    f"Refusing to replace output with unknown schema: {path}"
                )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_current_cells(output: Path, records: list[dict]) -> list[str]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for station in records:
        grouped[cell_key(station["lat"], station["lon"])].append(station)

    cell_keys = sorted(grouped, key=lambda key: tuple(int(x) for x in key.split("_", 1)))
    for key in cell_keys:
        write_json(
            output / "cells" / f"{key}.json",
            {
                "schema_version": SCHEMA_VERSION,
                "cell": key,
                "stations": grouped[key],
            },
        )
    return cell_keys


def snapshot_for_history(records: list[dict]) -> dict[str, dict[str, float]]:
    snapshot: dict[str, dict[str, float]] = {}
    for station in records:
        combos = {}
        for item in station["prices"]:
            suffix = 1 if item["self"] else 0
            combos[f"{item['fuel']}:{suffix}"] = item["price"]
        if combos:
            snapshot[station["id"]] = combos
    return snapshot


def empty_history_state(window_days: int = HISTORY_WINDOW_DAYS) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "window_days": window_days,
        "snapshots": {},
    }


def load_history_state(path: Path | None, window_days: int = HISTORY_WINDOW_DAYS) -> dict:
    if path is None or not path.exists():
        return empty_history_state(window_days)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BuildError(f"Could not read history state {path}: {exc}") from exc
    if value.get("schema_version") != SCHEMA_VERSION:
        raise BuildError(f"Unsupported history-state schema in {path}")
    snapshots = value.get("snapshots")
    if not isinstance(snapshots, dict):
        raise BuildError(f"Invalid history-state snapshots in {path}")
    return {
        "schema_version": SCHEMA_VERSION,
        "window_days": window_days,
        "snapshots": snapshots,
    }


def update_history_state(
    state: dict,
    price_date: str,
    records: list[dict],
    window_days: int = HISTORY_WINDOW_DAYS,
) -> dict:
    current = date.fromisoformat(price_date)
    snapshots = dict(state.get("snapshots") or {})
    if snapshots:
        latest_existing = max(date.fromisoformat(value) for value in snapshots)
        if current < latest_existing:
            raise BuildError(
                f"Current MIMIT snapshot {current} is older than retained history {latest_existing}"
            )

    snapshots[price_date] = snapshot_for_history(records)
    cutoff = current - timedelta(days=window_days - 1)
    kept = {
        key: snapshots[key]
        for key in sorted(snapshots)
        if cutoff <= date.fromisoformat(key) <= current
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "window_days": window_days,
        "snapshots": kept,
    }


def history_axis(price_date: str, window_days: int = HISTORY_WINDOW_DAYS) -> list[str]:
    end = date.fromisoformat(price_date)
    start = end - timedelta(days=window_days - 1)
    return [(start + timedelta(days=i)).isoformat() for i in range(window_days)]


def build_history_cells(
    state: dict,
    current_records: list[dict],
    price_date: str,
    window_days: int = HISTORY_WINDOW_DAYS,
) -> tuple[dict[str, dict], dict]:
    days = history_axis(price_date, window_days)
    day_index = {day: idx for idx, day in enumerate(days)}
    current_by_id = {station["id"]: station for station in current_records}
    station_history: dict[str, dict[str, list[float | None]]] = defaultdict(dict)
    snapshots = state.get("snapshots") or {}

    for day in days:
        snapshot = snapshots.get(day)
        if not snapshot:
            continue
        idx = day_index[day]
        for sid, combos in snapshot.items():
            if sid not in current_by_id:
                continue
            for combo, price in combos.items():
                values = station_history[sid].setdefault(combo, [None] * window_days)
                values[idx] = float(price)

    cells: dict[str, dict[str, dict[str, list[float | None]]]] = defaultdict(dict)
    for sid, combos in station_history.items():
        station = current_by_id[sid]
        key = cell_key(station["lat"], station["lon"])
        cells[key][sid] = combos

    output_cells = {
        key: {
            "schema_version": SCHEMA_VERSION,
            "cell": key,
            "stations": cells[key],
        }
        for key in sorted(cells, key=lambda value: tuple(int(x) for x in value.split("_", 1)))
    }
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "window_days": window_days,
        "end_date": price_date,
        "days": days,
        "available_snapshot_dates": [day for day in days if day in snapshots],
        "cells": list(output_cells),
    }
    return output_cells, metadata


def write_history(output: Path, state: dict, records: list[dict], price_date: str) -> dict:
    cells, metadata = build_history_cells(state, records, price_date)
    write_json(output / "history" / "metadata.json", metadata, pretty=True)
    for key, value in cells.items():
        write_json(output / "history" / "cells" / f"{key}.json", value)
    return metadata


def load_sources(args, repo_root: Path):
    mimit, price_url, station_url = import_mimit(repo_root)
    if bool(args.registry_file) != bool(args.price_file):
        raise BuildError("Pass both --registry-file and --price-file, or neither")

    if args.registry_file:
        registry_blob = Path(args.registry_file).expanduser().read_bytes()
        price_blob = Path(args.price_file).expanduser().read_bytes()
    else:
        registry_blob = mimit.download(station_url)
        price_blob = mimit.download(price_url)

    registry_date, station_rows = mimit.parse_registry(registry_blob)
    price_date, price_rows, _captured = mimit.parse_prices(price_blob)
    return {
        "mimit": mimit,
        "station_url": station_url,
        "price_url": price_url,
        "registry_blob": registry_blob,
        "price_blob": price_blob,
        "registry_date": registry_date,
        "price_date": price_date,
        "station_rows": station_rows,
        "price_rows": price_rows,
    }


def load_locality_source(args):
    if args.localities_file:
        if not args.municipalities_2021_file:
            raise BuildError(
                "Pass --municipalities-2021-file with --localities-file so "
                "2021 PRO_COM codes can be resolved against the same vintage"
            )
        blob = Path(args.localities_file).expanduser().read_bytes()
        municipalities_blob = (
            Path(args.municipalities_2021_file).expanduser().read_bytes()
        )
    elif args.download_localities:
        if args.municipalities_2021_file:
            raise BuildError(
                "--municipalities-2021-file is only used with --localities-file"
            )
        blob = download_localities()
        municipalities_blob = download_municipalities_2021()
    else:
        if args.municipalities_2021_file:
            raise BuildError(
                "--municipalities-2021-file requires --localities-file"
            )
        return None

    try:
        rows = parse_localities_archive(blob)
        municipalities = parse_municipalities_2021_archive(municipalities_blob)
        rows = attach_municipality_names(rows, municipalities)
    except LocalityError as exc:
        raise BuildError(str(exc)) from exc
    if len(rows) < 50_000:
        raise BuildError(
            f"ISTAT residential-locality count {len(rows):,} is unexpectedly small"
        )
    return {
        "blob": blob,
        "municipalities_blob": municipalities_blob,
        "municipality_count": len(municipalities),
        "rows": rows,
    }


def build(args) -> dict:
    repo_root = find_repo_root(args.repo_root)
    source = load_sources(args, repo_root)
    locality_source = load_locality_source(args)
    records, counts = normalize_current(source["station_rows"], source["price_rows"])
    validate_snapshot(counts)

    requested_output = Path(args.output).expanduser().resolve()
    history_enabled = args.history_state_output is not None
    state_path = Path(args.history_state).expanduser().resolve() if args.history_state else None
    state_output = (
        Path(args.history_state_output).expanduser().resolve()
        if args.history_state_output
        else None
    )
    for state_candidate in (state_path, state_output):
        if state_candidate is not None and (
            state_candidate == requested_output or requested_output in state_candidate.parents
        ):
            raise BuildError(
                "History state must live outside the public output directory"
            )

    state = load_history_state(state_path) if history_enabled else None
    output = prepare_output(requested_output, repo_root)
    current_cells = write_current_cells(output, records)
    places = build_places(source["station_rows"])
    write_json(
        output / "places.json",
        {
            "schema_version": SCHEMA_VERSION,
            "registry_date": source["registry_date"],
            "places": places,
        },
    )

    if locality_source:
        write_json(
            output / "localities.json",
            {
                "schema_version": SCHEMA_VERSION,
                "reference_year": ISTAT_LOCALITIES_REFERENCE_YEAR,
                "fields": ["name", "type", "pro_com", "municipality", "lat", "lon"],
                "localities": locality_source["rows"],
            },
        )

    history_metadata = None
    if history_enabled:
        assert state is not None and state_output is not None
        state = update_history_state(state, source["price_date"], records)
        history_metadata = write_history(output, state, records, source["price_date"])
        write_json(state_output, state)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_files = {
        "registry": {
            "bytes": len(source["registry_blob"]),
            "sha256": sha256(source["registry_blob"]),
        },
        "prices": {
            "bytes": len(source["price_blob"]),
            "sha256": sha256(source["price_blob"]),
        },
    }
    locality_metadata = {
        "enabled": locality_source is not None,
        "count": len(locality_source["rows"]) if locality_source else 0,
        "path": "localities.json" if locality_source else None,
        "reference_year": (
            ISTAT_LOCALITIES_REFERENCE_YEAR if locality_source else None
        ),
        "source_url": ISTAT_LOCALITIES_URL if locality_source else None,
        "municipality_source_url": (
            ISTAT_MUNICIPALITIES_2021_URL if locality_source else None
        ),
        "municipality_count": (
            locality_source["municipality_count"] if locality_source else 0
        ),
        "municipality_reference_date": (
            "2021-12-31" if locality_source else None
        ),
        "license": ISTAT_LOCALITIES_LICENSE if locality_source else None,
        "license_url": ISTAT_LOCALITIES_LICENSE_URL if locality_source else None,
    }
    if locality_source:
        source_files["localities"] = {
            "bytes": len(locality_source["blob"]),
            "sha256": sha256(locality_source["blob"]),
        }
        source_files["municipalities_2021"] = {
            "bytes": len(locality_source["municipalities_blob"]),
            "sha256": sha256(locality_source["municipalities_blob"]),
        }

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "source": {
            "name": "MIMIT fuel-price open data",
            "registry_url": source["station_url"],
            "price_url": source["price_url"],
            "license": "IODL-2.0",
            "license_url": IODL_URL,
        },
        "registry_date": source["registry_date"],
        "price_date": source["price_date"],
        "source_files": source_files,
        "grid": {
            "size_degrees": GRID_SIZE_DEGREES,
            "cell_key": "floor(lat / size)_floor(lon / size)",
            "cells": current_cells,
        },
        "counts": counts,
        "places": {
            "count": len(places),
            "path": "places.json",
        },
        "localities": locality_metadata,
        "history": {
            "enabled": history_enabled,
            "window_days": HISTORY_WINDOW_DAYS if history_enabled else 0,
            "metadata_path": "history/metadata.json" if history_enabled else None,
            "available_snapshot_dates": (
                history_metadata["available_snapshot_dates"] if history_metadata else []
            ),
        },
    }
    write_json(output / "metadata.json", metadata, pretty=True)
    return metadata


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Build validated static station data for the GitHub Pages frontend."
    )
    ap.add_argument("--repo-root", help="Repository root; normally auto-detected.")
    ap.add_argument("--output", required=True, help="Generated data directory; replaced by this command.")
    ap.add_argument("--registry-file", help="Use this cached MIMIT registry CSV instead of downloading.")
    ap.add_argument("--price-file", help="Use this cached MIMIT price CSV instead of downloading.")
    localities = ap.add_mutually_exclusive_group()
    localities.add_argument("--localities-file", help="Use this cached ISTAT LocalitaPuntuali_21.zip for static locality search.")
    localities.add_argument("--download-localities", action="store_true", help="Download the official ISTAT 2021 point-locality and 31-Dec-2021 municipality archives and build localities.json.")
    ap.add_argument("--municipalities-2021-file", help="Cached ISTAT Limiti2021_g.zip; required with --localities-file for same-vintage municipality labels.")
    ap.add_argument("--history-state", help="Previous rolling-history JSON state; missing path starts fresh.")
    ap.add_argument("--history-state-output", help="Write updated rolling-history state here and generate public 7-day history.")
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        metadata = build(args)
    except (BuildError, ValueError, OSError) as exc:
        print(f"build_web_data: {exc}", file=sys.stderr)
        return 2

    counts = metadata["counts"]
    print(
        "Built static data: "
        f"{counts['stations_with_supported_prices']:,} stations, "
        f"{counts['joined_supported_price_rows']:,} supported prices, "
        f"{len(metadata['grid']['cells']):,} current cells, "
        f"{metadata['places']['count']:,} places"
        + (
            f", {metadata['localities']['count']:,} localities"
            if metadata["localities"]["enabled"]
            else ""
        )
    )
    print(
        f"MIMIT registry {metadata['registry_date']} · prices {metadata['price_date']} · "
        f"join {counts['join_ratio']:.2%}"
    )
    if metadata["history"]["enabled"]:
        dates = metadata["history"]["available_snapshot_dates"]
        print(f"Rolling history snapshots: {', '.join(dates) if dates else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
