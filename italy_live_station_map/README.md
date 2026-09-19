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


## Radius overlay and ranked station panel

The map now draws the selected search radius as a light, semi-transparent,
dashed circle around the selected point.

A side panel ranks stations without using brand, ratings or reviews. By default:

1. lower current price first;
2. distance is used only as a tie-breaker.

The panel shows:

* current price;
* straight-line distance from the selected map point;
* price difference from the current local median;
* estimated savings/cost relative to that median for a 50-litre fill.

You can also sort the panel by straight-line distance or by savings versus the
local median. Clicking a ranked row pans to the station and opens its popup.

Important: distance is currently **great-circle/straight-line distance**, not
driving distance or detour time. Therefore it should not yet be used to decide
whether a cheaper station is actually worth a detour.

A later trip-planning version should use route distance/time and compare the
fuel saved against the detour cost rather than ranking on price alone.
