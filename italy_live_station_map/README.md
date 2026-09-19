# Live Italian fuel-station price map — with station history

This package is **standalone**. It does not need to be placed beside the earlier
national fuel-price toolkit.

The earlier toolkit contains national statistical series. Station sparklines
require a different key: MIMIT `idImpianto`, followed through daily station
snapshots. For that reason this map maintains its own SQLite database:

```text
data/station_history.sqlite
```

## Start the map

```bash
python serve_map.py
```

Open:

```text
http://127.0.0.1:8000
```

The map records the live station results that you view, so it begins building a
rolling local history automatically.

## 30/90-day station history

Click a station and choose `30d` or `90d`.

The sparkline:
* uses only observations actually present in the local database;
* does **not interpolate gaps**;
* breaks the plotted line when dates are missing;
* tells you how many requested days are available/missing.

Initially the database can be sparse. There are two ways to fill it.

### 1. Capture the official current 08:00 snapshot every day

```bash
python history_index.py capture-current
```

Optionally keep the raw CSV too:

```bash
python history_index.py capture-current --save-raw
```

This is the best way to build the ongoing current-quarter history. MIMIT
publishes the daily file with prices in force at 08:00 on the day preceding
publication.

You can schedule this command once per day with cron / Task Scheduler.

### 2. Index completed historical quarters

For example:

```bash
python history_index.py download-and-index 2026 2
```

or separately:

```bash
python history_index.py download-quarter 2026 2
python history_index.py index-archive cache/2026_2_tr.tar.gz
```

The quarterly files are large, so they are not bundled. `history_index.py`
streams the CSV files from the `.tar.gz` and stores only:

* station ID
* observation date
* fuel
* self/served
* price
* communication timestamp
* provenance

in SQLite.

Check coverage:

```bash
python history_index.py coverage
```

## Current-quarter limitation

MIMIT's public historical archive is grouped by completed quarterly releases.
At the time this package was prepared, the page exposed completed archives
through Q2 2026. Therefore a fresh installation cannot magically reconstruct
every station's July–September 2026 daily history from the quarterly archive.

The package is explicit about that:
* completed quarters can be indexed;
* today's official snapshot can be captured;
* future daily captures accumulate locally;
* missing dates stay missing and are shown as gaps.

## Data format

MIMIT documents the daily price file as:

```text
idImpianto
descCarburante
prezzo
isSelf
dtComu
```

Line 1 contains the extraction date and line 2 contains the actual CSV header.

Delimiter:
* `;` through 9 February 2026
* `|` from 10 February 2026

`history_index.py` detects this from the extraction date.

## Live map features

* Petrol / diesel / GPL / methane
* Self-service / served
* 1–10 km radius
* Click map to recenter
* Optional browser geolocation
* Current price labels directly on the map
* Green→red relative local-price coloring
* Minimum / median / maximum summary
* 30/90-day station sparkline
* No ratings, reviews, brand cards or business-ranking data

## Basemap

Leaflet + OpenStreetMap. No Google Maps API key is required.

## Demo

```bash
python serve_map.py --demo
```

This uses synthetic stations to test the interface. Synthetic points are stored
with source `synthetic_demo` and should not be used for analysis.
