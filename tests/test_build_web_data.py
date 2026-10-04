from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_web_data.py"
SPEC = importlib.util.spec_from_file_location("build_web_data", MODULE_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def station_row(
    sid: str,
    lat: float,
    lon: float,
    address: str = "Via Test",
    comune: str = "Test",
    provincia: str = "TT",
):
    return (
        sid,
        address,
        comune,
        provincia,
        "",
        lat,
        lon,
        "2026-10-03",
        "2026-10-04T08:30:00",
    )


def price_row(
    sid: str,
    fuel: str,
    self_flag: int,
    price: float,
    observed: str = "2026-10-03",
):
    return (
        sid,
        fuel,
        self_flag,
        price,
        "03/10/2026 07:30:00",
        observed,
        "2026-10-04T08:30:00",
    )


class GridTests(unittest.TestCase):
    def test_half_degree_cell_keys_are_stable_at_boundaries(self):
        self.assertEqual(builder.cell_key(43.5, 11.0), "87_22")
        self.assertEqual(builder.cell_key(43.7499, 11.2499), "87_22")
        self.assertEqual(builder.cell_key(43.75, 11.25), "87_22")
        self.assertEqual(builder.cell_key(44.0, 11.5), "88_23")


class NormalizationTests(unittest.TestCase):
    def test_supported_rows_join_and_unsupported_fuels_are_counted(self):
        stations = [
            station_row("1", 43.7, 11.2, comune="Firenze", provincia="FI"),
            station_row("2", 45.4, 9.2, comune="Milano", provincia="MI"),
        ]
        prices = [
            price_row("1", "Benzina", 1, 1.80),
            price_row("1", "Gasolio", 0, 1.70),
            price_row("2", "GPL", 1, 0.75),
            price_row("2", "GNL", 1, 1.10),
            price_row("999", "Benzina", 1, 1.90),
        ]

        records, counts = builder.normalize_current(stations, prices)

        self.assertEqual([item["id"] for item in records], ["1", "2"])
        self.assertEqual(counts["supported_price_keys"], 4)
        self.assertEqual(counts["joined_supported_price_rows"], 3)
        self.assertEqual(counts["orphan_supported_price_rows"], 1)
        self.assertEqual(counts["unsupported_fuel_rows"], {"GNL": 1})
        self.assertAlmostEqual(counts["join_ratio"], 0.75)
        self.assertEqual(records[0]["address"], "Via Test, Firenze, FI")

    def test_duplicate_supported_keys_fail_default_validation(self):
        stations = [station_row(str(i), 43.0 + i / 10000, 11.0) for i in range(20_001)]
        prices = []
        for i in range(18_001):
            sid = str(i)
            prices.extend(
                [
                    price_row(sid, "Benzina", 1, 1.80),
                    price_row(sid, "Gasolio", 1, 1.70),
                    price_row(sid, "GPL", 1, 0.75),
                    price_row(sid, "Metano", 1, 1.30),
                ]
            )
        prices.append(price_row("0", "Benzina", 1, 1.81))
        records, counts = builder.normalize_current(stations, prices)
        self.assertEqual(len(records), 18_001)
        self.assertEqual(counts["duplicate_supported_keys"], 1)
        with self.assertRaises(builder.BuildError):
            builder.validate_snapshot(counts)


class PlaceTests(unittest.TestCase):
    def test_place_coordinate_uses_median_station_position(self):
        rows = [
            station_row("1", 43.0, 11.0, comune="Alpha", provincia="AA"),
            station_row("2", 43.2, 11.2, comune="Alpha", provincia="AA"),
            station_row("3", 50.0, 20.0, comune="Alpha", provincia="AA"),
        ]
        places = builder.build_places(rows)
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]["lat"], 43.2)
        self.assertEqual(places[0]["lon"], 11.2)
        self.assertEqual(places[0]["station_count"], 3)


class HistoryTests(unittest.TestCase):
    def _records(self, price: float):
        return [
            {
                "id": "1",
                "lat": 43.7,
                "lon": 11.2,
                "address": "Via Test, Firenze, FI",
                "road_type": "",
                "prices": [
                    {
                        "fuel": "Benzina",
                        "self": True,
                        "price": price,
                        "updated": "",
                    }
                ],
            }
        ]

    def test_same_day_update_is_idempotent(self):
        state = builder.empty_history_state()
        state = builder.update_history_state(state, "2026-10-03", self._records(1.80))
        state = builder.update_history_state(state, "2026-10-03", self._records(1.81))
        self.assertEqual(list(state["snapshots"]), ["2026-10-03"])
        self.assertEqual(
            state["snapshots"]["2026-10-03"]["1"]["Benzina:1"],
            1.81,
        )

    def test_history_prunes_to_seven_calendar_days(self):
        state = builder.empty_history_state()
        for day in range(1, 9):
            observed = f"2026-10-{day:02d}"
            state = builder.update_history_state(state, observed, self._records(1.70 + day / 100))

        self.assertEqual(
            list(state["snapshots"]),
            [
                "2026-10-02",
                "2026-10-03",
                "2026-10-04",
                "2026-10-05",
                "2026-10-06",
                "2026-10-07",
                "2026-10-08",
            ],
        )

    def test_missing_days_remain_null_in_public_history(self):
        state = builder.empty_history_state()
        state = builder.update_history_state(state, "2026-10-01", self._records(1.80))
        state = builder.update_history_state(state, "2026-10-03", self._records(1.82))
        cells, metadata = builder.build_history_cells(
            state,
            self._records(1.82),
            "2026-10-03",
        )

        key = builder.cell_key(43.7, 11.2)
        values = cells[key]["stations"]["1"]["Benzina:1"]
        self.assertEqual(metadata["available_snapshot_dates"], ["2026-10-01", "2026-10-03"])
        self.assertIsNone(values[-2])
        self.assertEqual(values[-3], 1.80)
        self.assertEqual(values[-1], 1.82)

    def test_older_source_snapshot_cannot_replace_newer_history(self):
        state = builder.empty_history_state()
        state = builder.update_history_state(state, "2026-10-03", self._records(1.80))
        with self.assertRaises(builder.BuildError):
            builder.update_history_state(state, "2026-10-02", self._records(1.79))


class OutputTests(unittest.TestCase):
    def test_current_output_contains_only_expected_cell_files(self):
        records = [
            {
                "id": "1",
                "lat": 43.7,
                "lon": 11.2,
                "address": "A",
                "road_type": "",
                "prices": [],
            },
            {
                "id": "2",
                "lat": 45.4,
                "lon": 9.2,
                "address": "B",
                "road_type": "",
                "prices": [],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keys = builder.write_current_cells(root, records)
            self.assertEqual(len(keys), 2)
            files = sorted(path.name for path in (root / "cells").glob("*.json"))
            self.assertEqual(files, sorted(f"{key}.json" for key in keys))
            payload = json.loads((root / "cells" / files[0]).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)


class OutputSafetyTests(unittest.TestCase):
    def test_prepare_output_refuses_non_builder_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            target = base / "target"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(builder.BuildError):
                builder.prepare_output(target, repo)
            self.assertTrue((target / "keep.txt").exists())

    def test_prepare_output_replaces_previous_builder_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            target = base / "target"
            target.mkdir()
            (target / "metadata.json").write_text(
                json.dumps({"schema_version": 1}), encoding="utf-8"
            )
            (target / "old.json").write_text("{}", encoding="utf-8")
            builder.prepare_output(target, repo)
            self.assertTrue(target.exists())
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
