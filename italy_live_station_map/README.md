# Italy live station-price map v7

Standalone interactive map for official MIMIT station-level fuel-price data.

## Start it from anywhere

```bash
./italy_live_station_map/run.sh
```

or:

```bash
python3 italy_live_station_map/serve_map.py
```

Then open:

```text
http://127.0.0.1:8000
```

The ranking panel is now docked outside the map viewport instead of floating over
it. On a narrow/mobile viewport it becomes a separate lower pane.

## Current data

The app downloads and locally joins the two official MIMIT daily CSV files:

* `anagrafica_impianti_attivi.csv`
* `prezzo_alle_8.csv`

The latest raw copies overwrite the two files in `cache/`; they do not accumulate.

`data/station_history.sqlite` retains one row per station/fuel/service/date and
therefore builds history only when distinct daily snapshots have actually been
captured or historical archives have explicitly been imported.

## Recent history: fast, local, no surprise downloads

Station popups now offer:

* 1 day
* 3 days
* 7 days
* 30 days
* 90 days

These buttons only query the local SQLite database. They never start a quarterly
archive download.

`Sync current snapshot` downloads **only the newest official daily snapshot**.
If the database has only one snapshot date, a 7-day view will honestly say
`1/7 days available`. Keep synchronizing on later days to build recent history.

While the server is running it checks for a new current snapshot at most every
six hours. Change this with:

```bash
python3 serve_map.py --auto-sync-hours 3
```

or disable periodic refresh:

```bash
python3 serve_map.py --auto-sync-hours 0
```

Completed quarterly archives remain optional:

```bash
python3 history_index.py download-and-index 2026 2
```

## Location search

The toolbar has a place search limited to Italy. Searches are sent through the
local Python server to OpenStreetMap Nominatim; only explicit searches trigger a
request.

## Navigation and shortcuts

Visible movement buttons are included on the lower-left map edge.

Keyboard:

* `W` / `↑`: north
* `A` / `←`: west
* `S` / `↓`: south
* `D` / `→`: east
* `+` / `-`: zoom
* `0`: recenter on selected search point
* `R`: refresh map
* `L`: browser location
* `/`: focus location search
* `H` or `?`: help
* `Esc`: close popup/help/search results

Keyboard map commands are ignored while typing in an input/select box.

## Languages

Use the little flag button:

* `🇮🇹 IT` switches to Italian
* `🇬🇧 EN` switches to English

The choice is stored in browser local storage.

## Price colors

The old continuous green/red scale has been replaced by five discrete bands:

1. dark blue
2. sky blue
3. yellow
4. orange
5. vermillion

The bands span the 5th–95th percentile price range of the currently visible
stations. Exact prices remain printed above every marker, so color is a quick
visual cue rather than the only encoding.

## Search radius and ranking

The faded dashed circle is the actual search radius.

The docked ranking panel shows current price, straight-line distance, price
difference from the local median, visible-set percentile, freshness, and
fill-size-adjusted savings.

Distance is still straight-line distance, not route/detour distance.

## History caveat

MIMIT publishes the current station snapshot daily, while its historical archive
is grouped by completed quarters. Therefore a newly installed copy cannot
reconstruct earlier days in the still-open quarter merely by pressing Sync.
Missing dates remain missing; nothing is silently interpolated.
