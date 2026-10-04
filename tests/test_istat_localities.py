from __future__ import annotations

import importlib.util
import io
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "istat_localities.py"
SPEC = importlib.util.spec_from_file_location("istat_localities", MODULE_PATH)
localities = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = localities
SPEC.loader.exec_module(localities)


def fixture_zip() -> bytes:
    csv_text = (
        "NOME;TIPO_LOC;PRO_COM;POINT_X;POINT_Y\n"
        "Centro Test;1;48017;500000;4649776.22482\n"
        "Nucleo-Test;2;47017;500000;4871872.84\n"
        "Area Produttiva;3;47017;500000;4871872.84\n"
        "Case Sparse;4;47017;500000;4871872.84\n"
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("LocalitaPuntuali_21/Localita_2021_Point.csv", csv_text)
    return out.getvalue()


class LocalityParserTests(unittest.TestCase):
    def test_archive_keeps_only_residential_types(self):
        rows = localities.parse_localities_archive(fixture_zip())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "Centro Test")
        self.assertEqual(rows[0][1], 1)
        self.assertEqual(rows[0][2], "048017")
        self.assertEqual(rows[1][0], "Nucleo-Test")
        self.assertEqual(rows[1][1], 2)

    def test_utm32n_conversion(self):
        lat, lon = localities.utm32n_to_wgs84(500000, 4649776.22482)
        self.assertAlmostEqual(lat, 42.0, places=5)
        self.assertAlmostEqual(lon, 9.0, places=5)

    def test_search_normalization_ignores_punctuation_and_accents(self):
        self.assertEqual(
            localities.normalize_name("San-Barontò"),
            localities.normalize_name("san baronto"),
        )


if __name__ == "__main__":
    unittest.main()
