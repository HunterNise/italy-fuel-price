# Architecture

The station map is a small dependency-light local application. The repository
also contains a static-data build path that reuses the same MIMIT parser as
groundwork for GitHub Pages without changing the local persistence model.

## Local application

```text
station_map/
├── index.html
├── static/
│   ├── styles.css
│   ├── app.js
│   └── vendor/leaflet/
├── fuelmap/
│   ├── version.py
│   ├── config.py
│   ├── db.py
│   ├── mimit.py
│   ├── services.py
│   └── server.py
├── serve_map.py
├── sync_current.py
├── history_index.py
├── data/
│   └── station_history.sqlite
└── cache/
```

Responsibilities are separated as follows:

- `mimit.py` downloads and parses current MIMIT data.
- `db.py` owns the SQLite schema and persistent data access.
- `services.py` owns nearby search, history, geocoding, and auto-sync.
- `server.py` exposes local HTTP routes and serves the frontend shell.
- `static/app.js` owns browser map behavior, ranking, filtering, history UI,
  preferences, and localization.

## Local data invariants

1. **Current nationwide data are replaceable.** `current_prices` contains only
   the latest nationwide MIMIT snapshot.
2. **History is explicit.** `prices` stores tracked/local station history and
   deliberately imported archive data. Missing dates are never interpolated.
3. **Sync is atomic.** Both MIMIT current CSVs are downloaded and parsed before
   registry/current-price tables are replaced in one SQLite transaction.
4. **Cache is disposable.** Deleting `cache/` must not remove local history.
5. **User history is upgrade-safe.** Code upgrades should not overwrite
   `data/station_history.sqlite`.
6. **Database concurrency is modest but real.** SQLite uses WAL mode with a busy
   timeout because the HTTP server is threaded.
7. **The local browser does not fetch current MIMIT data directly.** External
   current-data access stays behind the local HTTP server.

## Static-data build

Repository-level static-data groundwork is implemented in:

```text
tools/build_web_data.py          validated static-data builder
tests/test_build_web_data.py     builder/grid/history tests
.github/workflows/check.yml      network-independent repository checks
```

The builder can download current MIMIT CSVs or consume explicit cached files. It
reuses `station_map/fuelmap/mimit.py` rather than maintaining a second parser.

Current generated-data decisions are:

- supported fuels: Benzina, Gasolio, GPL, Metano;
- 0.5° geographic current-data cells;
- generated municipality/place index using median station coordinates;
- optional seven-calendar-day rolling history state;
- missing history dates remain missing/null rather than interpolated;
- history state must live outside the public generated-data directory;
- validation rejects suspiciously small or poorly joined source snapshots.

Generated web datasets, raw downloaded CSVs, and rolling-history state are build
artifacts rather than source-controlled files.

The browser static provider and GitHub Pages deployment workflow are not yet
implemented. Planned work belongs in [`ROADMAP.md`](../ROADMAP.md).

## Architecture boundary

The local application and static deployment mode should remain peers that share
parsing, data semantics, and browser behavior where practical. The local SQLite
application must not depend on Pages build state, and the static site must not
depend on a long-running Python server.

If browser code later grows enough to justify another split, separate it by
behavior or data-provider responsibility rather than introducing a JavaScript
framework solely for file organization.
