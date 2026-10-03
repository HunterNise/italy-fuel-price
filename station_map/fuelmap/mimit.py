from __future__ import annotations

import csv
import io
import re
import threading
import urllib.request
from datetime import datetime

from . import __version__
from . import db
from .config import CACHE, HTTP_TIMEOUT_SECONDS, PRICE_URL, STATION_URL

ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SYNC_LOCK = threading.Lock()


def parse_extract_date(first_line: str) -> str:
    m = ISO_DATE.search(first_line or "")
    if not m:
        raise ValueError(
            "Could not parse extraction date from the first CSV line: "
            + repr(first_line[:200])
        )
    return m.group(1)


def download(
    url: str,
    timeout: float = HTTP_TIMEOUT_SECONDS,
    accept: str = "text/csv,*/*;q=0.8",
) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"ItalyFuelPriceMap/{__version__}",
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def csv_reader(blob: bytes):
    txt = io.TextIOWrapper(
        io.BytesIO(blob), encoding="utf-8-sig", errors="replace", newline=""
    )
    first = txt.readline()
    extraction_date = parse_extract_date(first)
    delimiter = "|" if extraction_date >= "2026-02-10" else ";"
    return extraction_date, csv.DictReader(txt, delimiter=delimiter)


def _field_map(reader):
    return {str(x).strip().lower(): x for x in (reader.fieldnames or [])}


def _first_field(fields, *names):
    for name in names:
        if name in fields:
            return fields[name]
    return None


def _fnum(value):
    try:
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return None


def parse_registry(blob: bytes) -> tuple[str, list[tuple]]:
    extraction, reader = csv_reader(blob)
    fields = _field_map(reader)

    id_col = _first_field(fields, "idimpianto")
    addr_col = _first_field(fields, "indirizzo")
    comune_col = _first_field(fields, "comune")
    provincia_col = _first_field(fields, "provincia")
    lat_col = _first_field(fields, "latitudine", "latitude", "lat")
    lon_col = _first_field(fields, "longitudine", "longitude", "lon", "lng")
    road_col = _first_field(fields, "tipo impianto", "tipo_impianto", "tipoimpianto")

    required = [id_col, addr_col, comune_col, provincia_col, lat_col, lon_col]
    if any(x is None for x in required):
        raise ValueError("Unexpected station-registry header: " + repr(reader.fieldnames))

    captured_at = datetime.now().isoformat(timespec="seconds")
    rows = []
    for row in reader:
        station_id = str(row.get(id_col, "")).strip()
        lat = _fnum(row.get(lat_col))
        lon = _fnum(row.get(lon_col))
        if not station_id or lat is None or lon is None:
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        rows.append(
            (
                station_id,
                str(row.get(addr_col, "")).strip(),
                str(row.get(comune_col, "")).strip(),
                str(row.get(provincia_col, "")).strip(),
                str(row.get(road_col, "")).strip() if road_col else "",
                lat,
                lon,
                extraction,
                captured_at,
            )
        )
    return extraction, rows


def parse_prices(blob: bytes) -> tuple[str, list[tuple], str]:
    extraction, reader = csv_reader(blob)
    fields = _field_map(reader)

    id_col = _first_field(fields, "idimpianto")
    fuel_col = _first_field(fields, "desccarburante")
    price_col = _first_field(fields, "prezzo")
    self_col = _first_field(fields, "isself")
    communicated_col = _first_field(fields, "dtcomu")

    required = [id_col, fuel_col, price_col, self_col, communicated_col]
    if any(x is None for x in required):
        raise ValueError("Unexpected price-file header: " + repr(reader.fieldnames))

    captured_at = datetime.now().isoformat(timespec="seconds")
    rows = []
    for row in reader:
        station_id = str(row.get(id_col, "")).strip()
        fuel = str(row.get(fuel_col, "")).strip()
        price = _fnum(row.get(price_col))
        try:
            is_self = int(str(row.get(self_col, "")).strip())
        except Exception:
            continue
        if not station_id or not fuel or price is None or is_self not in (0, 1):
            continue
        rows.append(
            (
                station_id,
                fuel,
                is_self,
                price,
                str(row.get(communicated_col, "")).strip(),
                extraction,
                captured_at,
            )
        )
    return extraction, rows, captured_at


def sync_current(save_raw: bool = True) -> dict:
    """
    Download both official current CSVs, parse both successfully, then commit
    the registry and prices together as one SQLite transaction.
    """
    db.init_db()
    CACHE.mkdir(parents=True, exist_ok=True)

    with SYNC_LOCK:
        registry_blob = download(STATION_URL)
        price_blob = download(PRICE_URL)

        registry_date, station_rows = parse_registry(registry_blob)
        price_date, price_rows, captured_at = parse_prices(price_blob)

        # Raw cache is only updated after both files parsed successfully.
        if save_raw:
            (CACHE / "anagrafica_impianti_attivi.csv").write_bytes(registry_blob)
            (CACHE / "prezzo_alle_8.csv").write_bytes(price_blob)

        db.commit_snapshot(
            registry_date,
            station_rows,
            price_date,
            price_rows,
            captured_at,
        )

    return {
        "registry_date": registry_date,
        "price_date": price_date,
        "stations": len(station_rows),
        "price_rows": len(price_rows),
    }
