from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "fetch_web_sources.py"

# The fetcher imports istat_localities from tools/. Make that importable before
# executing the module in this unit-test context.
TOOLS = str(ROOT / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

SPEC = importlib.util.spec_from_file_location("fetch_web_sources", MODULE_PATH)
fetcher = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = fetcher
SPEC.loader.exec_module(fetcher)


class SourceBundleTests(unittest.TestCase):
    def test_write_bundle_records_hashes_and_exact_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            manifest = fetcher.write_bundle(
                output,
                registry_blob=b"registry",
                price_blob=b"prices",
                locality_blob=b"localities",
                municipality_blob=b"municipalities",
                source_urls={
                    "anagrafica_impianti_attivi.csv": "https://example/registry",
                    "prezzo_alle_8.csv": "https://example/prices",
                    "LocalitaPuntuali_21.zip": "https://example/localities",
                    "Limiti2021_g.zip": "https://example/municipalities",
                },
            )
            expected = {
                fetcher.CACHE_MARKER,
                "anagrafica_impianti_attivi.csv",
                "prezzo_alle_8.csv",
                "LocalitaPuntuali_21.zip",
                "Limiti2021_g.zip",
            }
            self.assertEqual(
                {path.name for path in output.iterdir()},
                expected,
            )
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(
                manifest["files"]["prezzo_alle_8.csv"]["bytes"],
                len(b"prices"),
            )
            stored = json.loads(
                (output / fetcher.CACHE_MARKER).read_text(encoding="utf-8")
            )
            self.assertEqual(stored["files"], manifest["files"])

    def test_prepare_output_refuses_unowned_nonempty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            (repo / "station_map" / "fuelmap").mkdir(parents=True)
            target = base / "sources"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(fetcher.SourceFetchError):
                fetcher.prepare_output(target, repo)
            self.assertTrue((target / "keep.txt").is_file())

    def test_prepare_output_replaces_previous_source_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            (repo / "station_map" / "fuelmap").mkdir(parents=True)
            target = base / "sources"
            target.mkdir()
            (target / fetcher.CACHE_MARKER).write_text(
                '{"schema_version":1}\n',
                encoding="utf-8",
            )
            (target / "old.bin").write_bytes(b"old")
            fetcher.prepare_output(target, repo)
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
