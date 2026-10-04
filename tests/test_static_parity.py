from __future__ import annotations

import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "check_static_parity.py"
SPEC = importlib.util.spec_from_file_location("check_static_parity", MODULE_PATH)
parity = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = parity
SPEC.loader.exec_module(parity)


class ServicesStub:
    @staticmethod
    def haversine_km(lat1, lon1, lat2, lon2):
        earth = 6371.0088
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        h = (
            math.sin(dlat / 2) ** 2
            + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        )
        return 2 * earth * math.asin(math.sqrt(h))


def record(sid, lat, lon, price=1.8, fuel="Benzina", self_service=True):
    return {
        "id": str(sid),
        "lat": lat,
        "lon": lon,
        "address": f"Via {sid}, Roma, RM",
        "road_type": "",
        "prices": [
            {
                "fuel": fuel,
                "self": self_service,
                "price": price,
                "updated": "04/10/2026 07:30:00",
            }
        ],
    }


def raw_rows(records):
    stations = []
    prices = []
    for item in records:
        address, comune, provincia = item["address"].rsplit(", ", 2)
        stations.append(
            (
                item["id"],
                address,
                comune,
                provincia,
                item.get("road_type") or "",
                item["lat"],
                item["lon"],
                "2026-10-04",
                "2026-10-04T08:30:00",
            )
        )
        for price in item["prices"]:
            prices.append(
                (
                    item["id"],
                    price["fuel"],
                    1 if price["self"] else 0,
                    price["price"],
                    price["updated"],
                    "2026-10-04",
                    "2026-10-04T08:30:00",
                )
            )
    return stations, prices


def write_data(root: Path, records: list[dict], cell_func):
    cells = {}
    for item in records:
        key = cell_func(item["lat"], item["lon"])
        cells.setdefault(key, []).append(item)
    (root / "cells").mkdir(parents=True)
    for key, rows in cells.items():
        (root / "cells" / f"{key}.json").write_text(
            json.dumps({"schema_version": 1, "cell": key, "stations": rows}),
            encoding="utf-8",
        )
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "price_date": "2026-10-04",
                "grid": {
                    "size_degrees": 0.5,
                    "cells": sorted(cells),
                },
            }
        ),
        encoding="utf-8",
    )


class ParityTests(unittest.TestCase):
    def test_static_query_matches_direct_query_across_cell_boundary(self):
        records = [
            record("west", 41.999, 12.499, 1.79),
            record("east", 42.001, 12.501, 1.81),
            record("far", 42.3, 12.8, 1.70),
        ]
        probe = parity.Probe(
            "boundary", 42.0, 12.5, 2.0, "Benzina", True
        )
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            write_data(
                data,
                records,
                lambda lat, lon: f"{math.floor(lat / .5)}_{math.floor(lon / .5)}",
            )
            station_rows, price_rows = raw_rows(records)
            local = parity.direct_results(
                station_rows, price_rows, probe, ServicesStub
            )
            static = parity.static_results(data, probe, ServicesStub)
            self.assertEqual(
                [parity.canonical(x) for x in local],
                [parity.canonical(x) for x in static],
            )
            self.assertEqual([x["id"] for x in static], ["west", "east"])

    def test_missing_neighbor_cell_causes_detectable_mismatch(self):
        records = [
            record("west", 41.999, 12.499, 1.79),
            record("east", 42.001, 12.501, 1.81),
        ]
        probe = parity.Probe(
            "boundary", 42.0, 12.5, 2.0, "Benzina", True
        )
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            write_data(
                data,
                records,
                lambda lat, lon: f"{math.floor(lat / .5)}_{math.floor(lon / .5)}",
            )
            east_key = f"{math.floor(42.001/.5)}_{math.floor(12.501/.5)}"
            (data / "cells" / f"{east_key}.json").unlink()
            meta = json.loads((data / "metadata.json").read_text())
            meta["grid"]["cells"].remove(east_key)
            (data / "metadata.json").write_text(json.dumps(meta))
            with self.assertRaises(parity.ParityError):
                station_rows, price_rows = raw_rows(records)
                parity.compare_probe(
                    station_rows,
                    price_rows,
                    data,
                    probe,
                    ServicesStub,
                )

    def test_fuel_and_service_mode_filter_match(self):
        records = [
            record("petrol-self", 41.9028, 12.4964, 1.80),
            record(
                "diesel-self",
                41.9030,
                12.4966,
                1.70,
                fuel="Gasolio",
                self_service=True,
            ),
            record(
                "petrol-served",
                41.9032,
                12.4968,
                1.95,
                fuel="Benzina",
                self_service=False,
            ),
        ]
        probe = parity.Probe("Roma", 41.9028, 12.4964, 3, "Benzina", True)
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            write_data(
                data,
                records,
                lambda lat, lon: f"{math.floor(lat / .5)}_{math.floor(lon / .5)}",
            )
            station_rows, price_rows = raw_rows(records)
            result = parity.compare_probe(
                station_rows, price_rows, data, probe, ServicesStub
            )
            self.assertEqual(result["stations"], 1)

    def test_boundary_probe_generation_uses_populated_edges(self):
        records = [
            record("1", 42.001, 12.24),
            record("2", 44.499, 11.10),
            record("3", 45.25, 9.25),
        ]
        probes = parity.boundary_probes(records, count=2)
        self.assertEqual(len(probes), 2)
        self.assertTrue(any(abs(p.lat * 2 - round(p.lat * 2)) < 1e-9 or
                            abs(p.lon * 2 - round(p.lon * 2)) < 1e-9
                            for p in probes))


if __name__ == "__main__":
    unittest.main()
