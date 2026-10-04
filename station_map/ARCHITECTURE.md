# Architecture

The station map is a small dependency-light local application. The same browser
UI can also use generated static data through a provider boundary, without
changing the local persistence model.

## Browser and local application

```text
station_map/
├── index.html
├── static/
│   ├── runtime-config.js
│   ├── data-provider.js
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
- `runtime-config.js` selects the browser data mode; the tracked default is
  `local`.
- `data-provider.js` adapts either local `/api/*` routes or generated static
  data to one browser-facing interface.
- `app.js` owns browser map behavior, ranking, filtering, history UI,
  preferences, and localization without depending directly on the data source.

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

## Browser data providers

The local provider preserves the existing API behavior:

```text
getStations  → /api/stations
getHistory   → /api/history
searchPlaces → /api/geocode
syncCurrent  → /api/sync
```

Its capabilities expose current sync plus 7/30/90-day local history.

The static provider reads generated files directly:

```text
getStations  → data/metadata.json + relevant 0.5° cells
getHistory   → data/history/metadata.json + one history cell
searchPlaces → data/places.json + optional data/localities.json
syncCurrent  → unsupported
```

It computes exact Haversine distance in the browser after loading the geographic
cells intersecting the query bounding box. Static history is limited to the
generated rolling seven-day window. Static place search uses the generated
municipality index and, when enabled, a lazy-loaded ISTAT 2021 residential
locality index rather than a public geocoding service.

The UI reads provider capabilities: unsupported sync controls are hidden and
history buttons reflect the provider's available day windows.

## Static-data build

Repository-level static-data generation is implemented in:

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
- optional ISTAT 2021 inhabited-centre/nucleus search index;
- optional seven-calendar-day rolling history state;
- missing history dates remain missing/null rather than interpolated;
- history state must live outside the public generated-data directory;
- validation rejects suspiciously small or poorly joined source snapshots.

Generated web datasets, raw downloaded CSVs, and rolling-history state are build
artifacts rather than source-controlled files.

The allowlisted static-site assembly and GitHub Pages deployment workflow are
not yet implemented. Planned work belongs in [`ROADMAP.md`](../ROADMAP.md).

## Architecture boundary

The local application and static deployment mode remain peers that share
parsing, data semantics, and browser behavior where practical. The local SQLite
application does not depend on Pages build state, and the static provider does
not depend on a long-running Python server.

If browser code later grows enough to justify another split, separate it by
behavior or provider responsibility rather than introducing a JavaScript
framework solely for file organization.
