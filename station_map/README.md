# Italy live station-price map

**Version 0.10.2**

A local interactive map for Italian fuel-station prices using official MIMIT
station and price data.

## Run

From the repository root:

```bash
./station_map/run.sh
```

or:

```bash
python3 station_map/serve_map.py
```

Then open `http://127.0.0.1:8000`.

Check the installed version:

```bash
python3 station_map/serve_map.py --version
```

Repository-wide build/test and development commands are documented in
[`DEVELOPMENT.md`](../DEVELOPMENT.md).

## Structure and storage

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for module responsibilities and the
current static-data build boundary.

The important persistent local path is:

```text
data/station_history.sqlite
```

The `cache/` directory is disposable. Code-only upgrades should leave both
`data/` and `cache/` alone unless a migration explicitly says otherwise.

The local data model includes:

- `stations`: current station registry and coordinates;
- `current_prices`: latest nationwide MIMIT snapshot only;
- `tracked_stations`: stations in areas you have viewed;
- `prices`: retained local history for tracked stations plus explicit archive
  imports;
- `sync_state`: latest sync metadata.

Missing history is never silently interpolated.

## Current sync

```bash
python3 station_map/sync_current.py
```

The server can also refresh periodically:

```bash
python3 station_map/serve_map.py --auto-sync-hours 6
```

Repeated syncs of the same official snapshot date do not create duplicate
history days.

## Historical archives

Completed quarterly MIMIT archives remain optional:

```bash
python3 station_map/history_index.py download-and-index 2026 2
```

Inspect stored history:

```bash
python3 station_map/history_index.py coverage
```

## Current UI behavior

The browser remembers the selected location/centre, fuel, service mode, search
radius, fill size, freshness, ranking sort/limit, optional price/distance
filters, and panel collapsed states.

`Show` controls the display limit (`all`, `50`, `25`, `10`) for the map,
ranking, and histogram together. Maximum price and maximum distance are separate
combinable constraints in the Filters popover.

The processing order is:

```text
radius/fuel/mode/freshness
  → optional filters
  → sort
  → Show
  → map + ranking + histogram
```

Clicking a marker or ranking row selects the same station in both views. On
desktop, station details remain in the Leaflet popup. On screens up to 820 px,
station details replace the lower ranking content inside the same bottom sheet,
with explicit Back and Hide controls. Opening mobile station details
temporarily compacts the top controls so the map and station card remain
reachable.

The mobile results sheet prioritizes ranking rows over explanatory text:
secondary ranking copy/footer are omitted, the price-distribution chart is
collapsed by default, and the top status/stats are shortened because price
range remains visible in the map legend. Touch-map controls are reduced to fit
radius and recenter; normal pan/zoom uses touch gestures. Swipe/drag sheet
gestures are not part of 0.10.0.

Price labels become persistent at closer zoom levels or when only a small
number of stations is shown. The `⛶` control centres the selected search point
and fits the complete active radius.

The `?` button opens a responsive **Help & about** dialog. The Guide tab shows
keyboard shortcuts at the end on desktop and mirrors that structure with touch
controls at the end on narrow screens. The About tab reports the running app
version and provider mode plus the latest loaded snapshot/registry dates,
generated timestamp when available, refresh policy, primary source/licence
links, and a prominent GitHub project button. The dialog traps keyboard focus
while open and returns focus to the control that opened it.

## Version history

[`CHANGELOG.md`](CHANGELOG.md) records effective station-map version history.
Future work belongs in [`ROADMAP.md`](../ROADMAP.md).

The map's machine-readable version source is `fuelmap/version.py`.
