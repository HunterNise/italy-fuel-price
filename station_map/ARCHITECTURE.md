# Architecture

Current version: **0.8.2**

The project deliberately stays small and dependency-light, but its responsibilities
are now separated so future routing and analytics features do not have to grow
inside one server script.

## Layout

```text
station_map/
├── index.html                # HTML shell only
├── static/
│   ├── styles.css            # UI/layout
│   └── app.js                # browser behavior, map, ranking, i18n
├── fuelmap/
│   ├── version.py            # single machine-readable version source
│   ├── config.py             # paths, upstream URLs, timeouts
│   ├── db.py                 # SQLite schema and all persistent-data access
│   ├── mimit.py              # MIMIT CSV download/parsing/current sync
│   ├── services.py           # nearby search, history, geocoding, auto-sync
│   └── server.py             # HTTP routes and command-line server
├── serve_map.py              # backward-compatible thin launcher
├── sync_current.py           # current-snapshot CLI
├── history_index.py          # optional quarterly-history importer
├── data/
│   └── station_history.sqlite
└── cache/                    # replaceable downloaded files
```

## Data-flow invariants

1. **Current nationwide data are replaceable.** `current_prices` contains only
   the latest nationwide MIMIT snapshot.
2. **History is explicit.** `prices` stores tracked/local station history and
   deliberately imported archive data. Missing dates are never interpolated.
3. **Sync is atomic.** Both MIMIT CSVs are downloaded and parsed before the
   registry/current-price tables are replaced in one SQLite transaction.
4. **Cache is disposable.** Deleting `cache/` must not remove the local history.
5. **User history is upgrade-safe.** Code upgrades should not overwrite
   `data/station_history.sqlite`.
6. **Database concurrency is modest but real.** SQLite runs in WAL mode with a
   busy timeout because the HTTP server is threaded.
7. **The browser does not talk directly to MIMIT.** External data access stays
   behind the local HTTP server.

## Assessment

The structure is appropriate for the current scope. It is intentionally not a
web framework: the project has one local user, a small HTTP API, static frontend
assets and SQLite.

The next point where another architectural change becomes justified is
**route-aware trip planning**. That feature should get its own service/module
(e.g. `fuelmap/routing.py`) rather than being added to `services.py`, because it
will introduce a new external provider, route geometry, detour calculations and
vehicle-cost assumptions.

Likewise, if the browser code grows substantially beyond the current feature
set, the next frontend split should be by behavior (`map.js`, `ranking.js`,
`history.js`, `i18n.js`) rather than introducing a JavaScript framework merely
for file organization.
