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


## Freshness and fill-size controls

The current version adds two ranking-quality controls:

### Fill size

Use the `Fill` slider (10–100 L) to change the savings calculation. A station
that is 4 cents/litre below the local median corresponds to:

* €0.80 saved on 20 L
* €2.00 saved on 50 L
* €3.20 saved on 80 L

The selected fill size changes the side-panel savings immediately.

### Price freshness

MIMIT rows include a communication timestamp (`dtComu`). The map parses that
timestamp and displays the approximate age of each station's current price.

The `Freshness` selector can hide prices older than 1, 2, 3, 5 or 7 days.
Default: 3 days.

Freshness is shown in each ranked row and station popup. Observations older than
3 days receive a visible `stale` badge when they are not filtered out.

No missing date or missing freshness value is silently fabricated. If a
communication timestamp cannot be parsed, that station is excluded by a finite
freshness filter and remains visible only when `Freshness = all`.


## Price percentile and distribution

The ranking panel now includes a small histogram of the currently visible
station prices. The histogram is recalculated whenever you change:

* center point;
* radius;
* fuel;
* self-service / served mode;
* freshness filter.

The dashed vertical line in the mini-chart marks the visible-station median.
The panel also reports the total price spread in cents/litre.

Each ranked station shows a percentile-style statement such as:

```text
cheaper than 84% of visible stations
```

This is computed directly from the current filtered station set. Lower prices
are better, so the percentage is the share of visible stations with a strictly
higher price. Equal-price ties are not counted as more expensive.

This is intentionally descriptive rather than a composite score: the price
percentile does not incorporate distance, freshness or detour cost.
