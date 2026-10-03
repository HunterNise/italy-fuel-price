from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "station_history.sqlite"
CACHE = ROOT / "cache"

PRICE_URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
STATION_URL = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

SYNC_RETRY_SECONDS = 6 * 60 * 60
HTTP_TIMEOUT_SECONDS = 90
GEOCODE_TIMEOUT_SECONDS = 20
