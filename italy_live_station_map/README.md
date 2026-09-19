# Italy live station-price map

**Version 0.8.5**

A local interactive map for Italian fuel-station prices using official MIMIT
station and price data.

## Start

From any directory:

```bash
./italy_live_station_map/run.sh
```

or:

```bash
python3 italy_live_station_map/serve_map.py
```

Then open `http://127.0.0.1:8000`.

Check the installed version:

```bash
python3 italy_live_station_map/serve_map.py --version
```

## Project structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for the backend/frontend split, storage
invariants and extension points.

The important persistent path is:

```text
data/station_history.sqlite
```

The `cache/` directory is disposable. Code-only upgrades should leave both
`data/` and `cache/` alone unless a migration explicitly says otherwise.

## Data model

- `stations`: current station registry and coordinates.
- `current_prices`: latest nationwide MIMIT snapshot only.
- `tracked_stations`: stations in areas you have viewed.
- `prices`: retained local history for tracked stations plus explicit archive imports.
- `sync_state`: latest sync metadata.

No missing history is silently interpolated.

## Current sync

```bash
python3 italy_live_station_map/sync_current.py
```

The server can also refresh periodically:

```bash
python3 italy_live_station_map/serve_map.py --auto-sync-hours 6
```

Repeated syncs of the same official snapshot date do not create duplicate history days.

## Historical archives

Completed quarterly MIMIT archives remain optional:

```bash
python3 italy_live_station_map/history_index.py download-and-index 2026 2
```

Inspect stored history:

```bash
python3 italy_live_station_map/history_index.py coverage
```

## Versioning

The project follows semantic versioning from **0.8.2** onward.

- patch (`0.8.x`): fixes/refactors without changing expected user workflows;
- minor (`0.x.0`): new functionality or a meaningful behavior/data-model change;
- `1.0.0`: reserved for a stable public interface/configuration and mature upgrade path.

See [CHANGELOG.md](CHANGELOG.md) for the reconstructed earlier milestones and
future releases.

## UI state and compact view

The browser remembers the selected location/centre, fuel, service mode, search
radius, fill size, freshness, ranking sort/limit and panel collapsed states.

The collapsed top panel is a compact screenshot-oriented context card. It keeps
the location plus fuel/service/radius/freshness/fill summary, with the
language/help/expand controls underneath.

`Show` is the single station-visibility control. Its default is `all`; selecting
50, 25 or 10 limits the **ranking, map markers and histogram together** according
to the current sort order.

Price labels are automatic: they remain permanently visible at closer zoom
levels or when no more than 12 stations are shown; otherwise they appear on
hover.

The `⛶` button in the map navigation cluster centres the selected search point
and chooses the tightest zoom that fits the complete radius circle in the map
viewport.

Clicking a marker or ranking row selects the same station in both views. The
selected map marker is brought above nearby markers and receives a subtle halo.


## 0.8.5 request-handling fix

Browser reloads or rapidly superseded map requests can close an HTTP socket after
the local server has already finished the station query. These disconnects are
now ignored as normal client cancellation rather than logged as backend 502
errors. Identical station requests are also deduplicated while in flight.
