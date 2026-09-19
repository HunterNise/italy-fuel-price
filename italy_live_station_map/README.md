# Italy live station-price map — local CSV backend

This version does **not** use the fragile public search API.

Instead it downloads the two official daily MIMIT CSVs:

* `anagrafica_impianti_attivi.csv` — station ID + latitude/longitude + address
* `prezzo_alle_8.csv` — station ID + fuel + price + self/served + communication timestamp

The server stores them in SQLite and joins them locally by `idImpianto`.

## Run from anywhere

You no longer need to `cd` into the package.

From the parent directory:

```bash
./italy_live_station_map/run.sh
```

Or:

```bash
python3 italy_live_station_map/serve_map.py
```

Or with an absolute path:

```bash
python3 /path/to/italy_live_station_map/serve_map.py
```

`run.sh` resolves its own directory, so the current shell working directory does
not matter.

Windows:

```bat
italy_live_station_map\run.bat
```

Then open:

```text
http://127.0.0.1:8000
```

## First synchronization

The first map request attempts to download the official MIMIT station registry
and current daily price file automatically.

You can also do it explicitly:

```bash
python3 italy_live_station_map/sync_current.py
```

That saves the raw files under `cache/` and imports them into:

```text
data/station_history.sqlite
```

If a later network refresh fails, the map continues using the last successful
local snapshot and displays a warning.

## Why this is more robust

The previous version depended on an undocumented/public search endpoint returning
JSON. That endpoint can return an empty/non-JSON response.

This version only needs the two official downloadable CSV files. Radius filtering
and station-price joins happen entirely on your machine.

## Map features

* Petrol / diesel / GPL / methane
* Self-service / served
* Radius 1–25 km
* Price labels directly on station dots
* Green→red coloring relative to the local price distribution
* Minimum / median / maximum in the current radius
* Click map to recenter
* Browser geolocation if you permit it
* No ratings, reviews or station-business rankings
* Technical station ID retained for data joins/history
* 30/90-day station sparkline
* Missing historical dates remain gaps; no interpolation

## Historical station prices

The current daily snapshot is retained in the SQLite database each time you
synchronize on a new date.

For completed historical quarters:

```bash
python3 italy_live_station_map/history_index.py download-and-index 2026 2
```

To inspect what has been indexed:

```bash
python3 italy_live_station_map/history_index.py coverage
```

Quarterly archives can be large. They are not bundled with this package.

## Files

```text
index.html
serve_map.py
sync_current.py
history_index.py
run.sh
run.bat
data/station_history.sqlite
cache/
```

The package is standalone and does not depend on the previous national
fuel-price toolkit.
