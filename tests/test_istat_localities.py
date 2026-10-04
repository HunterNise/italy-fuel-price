from __future__ import annotations

import importlib.util
import io
import struct
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


def fixture_localities_zip() -> bytes:
    csv_text = (
        "NOME;TIPO_LOC;PRO_COM;POINT_X;POINT_Y\n"
        "Lido di Ostia;1;58091;500000;4649776.22482\n"
        "Acilia-Castel Fusano-Ostia Antica;1;58091;500000;4649776.22482\n"
        "Area Produttiva;3;58091;500000;4649776.22482\n"
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("LocalitaPuntuali_21/Localita_2021_Point.csv", csv_text)
    return out.getvalue()


def make_dbf(fields: list[tuple[str, str, int, int]], rows: list[list[str]]) -> bytes:
    header_length = 32 + 32 * len(fields) + 1
    record_length = 1 + sum(length for _name, _kind, length, _decimals in fields)
    header = bytearray(header_length)
    header[0] = 0x03
    struct.pack_into("<I", header, 4, len(rows))
    struct.pack_into("<H", header, 8, header_length)
    struct.pack_into("<H", header, 10, record_length)
    offset = 32
    for name, kind, length, decimals in fields:
        desc = bytearray(32)
        raw_name = name.encode("ascii")[:10]
        desc[0 : len(raw_name)] = raw_name
        desc[11] = ord(kind)
        desc[16] = length
        desc[17] = decimals
        header[offset : offset + 32] = desc
        offset += 32
    header[-1] = 0x0D

    records = bytearray()
    for row in rows:
        record = bytearray(b" " * record_length)
        record[0] = 0x20
        pos = 1
        for value, (_name, kind, length, _decimals) in zip(row, fields):
            encoded = str(value).encode("utf-8")
            if kind == "N":
                encoded = encoded.rjust(length, b" ")
            else:
                encoded = encoded.ljust(length, b" ")
            record[pos : pos + length] = encoded[:length]
            pos += length
        records.extend(record)
    return bytes(header + records + b"\x1A")


def fixture_boundaries_zip() -> bytes:
    municipality_dbf = make_dbf(
        [
            ("PRO_COM", "N", 6, 0),
            ("COMUNE", "C", 40, 0),
        ],
        [
            ["58091", "Roma"],
            ["59032", "Latina"],
        ]
        + [[str(100000 + i), f"Comune {i}"] for i in range(7500)],
    )
    province_dbf = make_dbf(
        [
            ("COD_PROV", "N", 3, 0),
            ("DEN_UTS", "C", 40, 0),
        ],
        [["58", "Roma"]],
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Limiti01012021_g/Com01012021_g_WGS84.dbf", municipality_dbf)
        zf.writestr("Limiti01012021_g/ProvCM01012021_g_WGS84.dbf", province_dbf)
    return out.getvalue()


class LocalityParserTests(unittest.TestCase):
    def test_archive_keeps_only_residential_types(self):
        rows = localities.parse_localities_archive(fixture_localities_zip())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "Acilia-Castel Fusano-Ostia Antica")
        self.assertEqual(rows[1][0], "Lido di Ostia")
        self.assertEqual(rows[1][2], "058091")

    def test_utm32n_conversion(self):
        lat, lon = localities.utm32n_to_wgs84(500000, 4649776.22482)
        self.assertAlmostEqual(lat, 42.0, places=5)
        self.assertAlmostEqual(lon, 9.0, places=5)

    def test_search_normalization_ignores_punctuation_and_accents(self):
        self.assertEqual(
            localities.normalize_name("Lido-di-Ostia"),
            localities.normalize_name("lido di ostia"),
        )

    def test_municipality_lookup_reads_same_vintage_pro_com_labels(self):
        lookup = localities.parse_municipalities_2021_archive(
            fixture_boundaries_zip()
        )
        self.assertEqual(lookup["058091"], "Roma")
        self.assertEqual(lookup["059032"], "Latina")

    def test_localities_are_enriched_with_parent_municipality(self):
        rows = localities.parse_localities_archive(fixture_localities_zip())
        lookup = localities.parse_municipalities_2021_archive(
            fixture_boundaries_zip()
        )
        enriched = localities.attach_municipality_names(rows, lookup)
        by_name = {row[0]: row for row in enriched}
        self.assertEqual(by_name["Lido di Ostia"][3], "Roma")
        self.assertEqual(by_name["Acilia-Castel Fusano-Ostia Antica"][3], "Roma")


if __name__ == "__main__":
    unittest.main()
