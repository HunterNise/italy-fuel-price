# Italy live station-price map v8

## What changed

* Navigation pad moved to the lower-right edge of the map, above the Leaflet attribution.
* Docking/undocking the ranking panel now calls Leaflet `invalidateSize()`, so the map redraws immediately instead of leaving a grey strip.
* The histogram always uses **all currently filtered stations**. The `Show 10/20/50` selector limits only ranking rows; the UI now says this explicitly.
* Language button shows the **current** language, using inline SVG flags so it does not depend on emoji-font support.
* Help shortcuts use two columns on desktop.
* History popup now offers only `7d`, `30d`, `90d`.
* Nationwide current prices are stored only in `current_prices`; rolling historical rows are retained only for stations in areas you actually view.
* No interpolation is used.

## History: how it actually works

MIMIT publishes a current daily `prezzo_alle_8.csv`. The map downloads that file
when you sync. It is one snapshot date, not a seven-day bundle.

So if you install the map today:

```text
local history: 1 snapshot day
```

and pressing `7d` correctly shows:

```text
1/7 days available
```

Pressing Sync again on the same MIMIT snapshot date does not create a second day.

When you view an area, the station IDs in that result set become "tracked".
On later days, when a new official snapshot is synchronized, the new prices for
those tracked station IDs are copied into the local history table. Therefore the
7-day chart fills naturally over successive daily snapshots without storing
nationwide history.

This keeps disk use small:

* `current_prices`: latest nationwide snapshot only;
* `prices`: rolling history only for stations you have viewed;
* explicit quarterly archive imports, if you choose to run them.

MIMIT's public historical archive is grouped by completed quarters. At the time
of this version, the published archive reaches Q2 2026, so there is no listed
official Q3 bundle to instantly backfill the previous week of September.

## Upgrade note

If you already have a v7 SQLite database, keep it if you want its captured
history. v8 adds tables without requiring you to delete the existing `prices`
table. A fresh sync fills the new `current_prices` table.

If you do not care about the one-day history captured so far, replacing the whole
folder is simpler.

## Start

```bash
./italy_live_station_map/run.sh
```

or:

```bash
python3 italy_live_station_map/serve_map.py
```
