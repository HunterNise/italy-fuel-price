#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import math
import unicodedata
import urllib.request
import zipfile

ISTAT_LOCALITIES_URL = (
    "https://www.istat.it/storage/cartografia/basi_territoriali/2021/"
    "LocalitaPuntuali_21.zip"
)
ISTAT_LOCALITIES_LICENSE = "CC BY 4.0"
ISTAT_LOCALITIES_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ISTAT_LOCALITIES_REFERENCE_YEAR = 2021
RESIDENTIAL_TYPES = {"1", "2"}


class LocalityError(RuntimeError):
    pass


def download_localities(url: str = ISTAT_LOCALITIES_URL) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "italy-fuel-price locality builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _decode_csv(blob: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return blob.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise LocalityError("Could not decode ISTAT locality CSV")


def _dialect(text: str):
    sample = text[:32768]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,|\t")
    except csv.Error:
        class Semicolon(csv.excel):
            delimiter = ";"
        return Semicolon


def _parse_number(value: str) -> float:
    text = str(value or "").strip().replace(" ", "")
    if not text:
        raise ValueError("empty number")
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    return float(text)


def _code6(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(float(text))).zfill(6)
    except ValueError:
        return text


def normalize_name(value: str) -> str:
    text = "".join(
        ch
        for ch in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(ch) != "Mn"
    )
    text = text.casefold().replace("ß", "ss")
    chars = [ch if ch.isalnum() else " " for ch in text]
    return " ".join("".join(chars).split())


def utm32n_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    # The ISTAT BT2021 point-locality dataset is distributed in the national
    # UTM 32N cartographic reference. ETRS89/WGS84 differences are negligible
    # for this search-centering use case.
    a = 6378137.0
    ecc_sq = 0.0066943799901413165
    k0 = 0.9996
    ecc_prime_sq = ecc_sq / (1 - ecc_sq)
    e1 = (1 - math.sqrt(1 - ecc_sq)) / (1 + math.sqrt(1 - ecc_sq))

    x = easting - 500000.0
    y = northing
    m = y / k0
    mu = m / (
        a
        * (
            1
            - ecc_sq / 4
            - 3 * ecc_sq**2 / 64
            - 5 * ecc_sq**3 / 256
        )
    )

    j1 = 3 * e1 / 2 - 27 * e1**3 / 32
    j2 = 21 * e1**2 / 16 - 55 * e1**4 / 32
    j3 = 151 * e1**3 / 96
    j4 = 1097 * e1**4 / 512
    fp = (
        mu
        + j1 * math.sin(2 * mu)
        + j2 * math.sin(4 * mu)
        + j3 * math.sin(6 * mu)
        + j4 * math.sin(8 * mu)
    )

    sin_fp = math.sin(fp)
    cos_fp = math.cos(fp)
    tan_fp = math.tan(fp)
    c1 = ecc_prime_sq * cos_fp**2
    t1 = tan_fp**2
    n1 = a / math.sqrt(1 - ecc_sq * sin_fp**2)
    r1 = a * (1 - ecc_sq) / (1 - ecc_sq * sin_fp**2) ** 1.5
    d = x / (n1 * k0)

    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ecc_prime_sq) * d**4 / 24
        + (
            61
            + 90 * t1
            + 298 * c1
            + 45 * t1**2
            - 252 * ecc_prime_sq
            - 3 * c1**2
        )
        * d**6
        / 720
    )
    lon = (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (
            5
            - 2 * c1
            + 28 * t1
            - 3 * c1**2
            + 8 * ecc_prime_sq
            + 24 * t1**2
        )
        * d**5
        / 120
    ) / cos_fp

    return math.degrees(lat), 9.0 + math.degrees(lon)


def parse_localities_archive(blob: bytes) -> list[list]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        raise LocalityError("Invalid ISTAT locality ZIP") from exc

    csv_names = [
        name
        for name in zf.namelist()
        if name.lower().endswith(".csv") and "point" in name.lower()
    ]
    if len(csv_names) != 1:
        raise LocalityError(
            f"Expected one point-locality CSV in archive, found {csv_names}"
        )

    text = _decode_csv(zf.read(csv_names[0]))
    reader = csv.DictReader(io.StringIO(text), dialect=_dialect(text))
    if not reader.fieldnames:
        raise LocalityError("ISTAT locality CSV has no header")

    fields = {str(name).strip().upper(): name for name in reader.fieldnames}
    required = ("NOME", "TIPO_LOC", "PRO_COM", "POINT_X", "POINT_Y")
    missing = [name for name in required if name not in fields]
    if missing:
        raise LocalityError(f"ISTAT locality CSV missing fields: {', '.join(missing)}")

    rows = []
    seen = set()
    for raw in reader:
        name = str(raw.get(fields["NOME"]) or "").strip()
        locality_type = str(raw.get(fields["TIPO_LOC"]) or "").strip()
        if not name or locality_type not in RESIDENTIAL_TYPES:
            continue
        try:
            x = _parse_number(raw.get(fields["POINT_X"]) or "")
            y = _parse_number(raw.get(fields["POINT_Y"]) or "")
            lat, lon = utm32n_to_wgs84(x, y)
        except (TypeError, ValueError):
            continue
        if not (35 <= lat <= 48.5 and 5 <= lon <= 20):
            continue

        item = (
            name,
            int(locality_type),
            _code6(raw.get(fields["PRO_COM"]) or ""),
            round(lat, 6),
            round(lon, 6),
        )
        if item in seen:
            continue
        seen.add(item)
        rows.append(list(item))

    rows.sort(
        key=lambda item: (
            normalize_name(item[0]),
            item[1],
            item[2],
            item[3],
            item[4],
        )
    )
    return rows
