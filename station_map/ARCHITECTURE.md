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
locality index rather than a public geocoding service. Locality `PRO_COM` values
are resolved against ISTAT's 31 December 2021 municipality layer so parent
municipality labels use the same territorial vintage as the locality data.

The UI reads provider capabilities: unsupported sync controls are hidden and
history buttons reflect the provider's available day windows. In static mode,
the main snapshot status also compares the MIMIT `price_date` with the current
calendar date in `Europe/Rome`: today/yesterday is shown as current, while two
or more days behind is visibly marked stale. This makes a missed deployment or
old upstream snapshot visible without changing the local-mode status behavior.

## Static-data build

Repository-level static-data generation is implemented in:

```text
tools/build_web_data.py          validated static-data builder
tools/build_static_site.py       allowlisted Pages-site assembler
tools/check_static_parity.py     static/local current-query parity checker
tools/fetch_web_sources.py       coherent deployment source-bundle downloader
tools/restore_history_artifact.py  cross-run Pages history-state restore
tests/test_build_web_data.py     builder/grid/history tests
tests/test_build_static_site.py  site allowlist/safety tests
tests/test_static_parity.py      synthetic cross-cell parity tests
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

## Static-site assembly

`tools/build_static_site.py` assembles the deployable browser site from an
explicit allowlist. It copies only `index.html`, the browser application/provider
files, vendored Leaflet public assets, and the generated JSON files declared by
the static-data metadata.

The assembler generates a static-mode `runtime-config.js`, writes `.nojekyll`,
checks that the browser asset cache-busting version matches
`fuelmap/version.py`, and rejects unexpected generated-data files. Python source,
SQLite databases, raw CSV/ZIP inputs, local cache/data directories, and rolling
history state are therefore outside the Pages artifact by construction rather
than by a broad copy followed by exclusions.

`tools/check_static_parity.py` provides a real-snapshot integration check between
the local current-query semantics and generated static cells. It uses
representative national probes plus populated 0.5° cell-edge probes and compares
the complete normalized result tuples. Synthetic cross-cell cases run in the
normal unit suite.

## GitHub Pages deployment

`.github/workflows/pages.yml` builds and deploys the public Pages artifact. A
single source bundle is downloaded first; the static-data builder and
static/local parity checker then consume those exact cached files before the
allowlisted site is assembled and uploaded.

The build job has read-only repository/Pages access plus `actions: write`,
which is required to restore and refresh its rolling history artifact. The
separate deployment job receives only the `pages: write` and OIDC
`id-token: write` permissions required by GitHub Pages. The uploaded Pages
artifact explicitly includes hidden generated site files such as `.nojekyll`.

Before each static-data build, `tools/restore_history_artifact.py` queries the
repository Actions-artifact API for the newest non-expired
`pages-history-state` artifact, validates its seven-day history-state schema,
and restores it when available. The data builder updates/prunes that state and
the workflow uploads the refreshed JSON again with 30-day artifact retention.
The state is never copied into `_site` and is never committed.

Because this is a public repository, Actions artifacts must be treated as
non-sensitive rather than secret storage. The retained state contains only
derived public MIMIT snapshot data, so that visibility is acceptable here.

The workflow defines one daily refresh at 09:15 in the `Europe/Rome` timezone.
GitHub applies the schedule only from the default branch, so this scheduled
trigger becomes active when the workflow reaches `main`. The initial timing
choice follows the 2026-10-05 publication sample, where the price file changed
between 08:40 and 08:50 Rome and the registry caught up between 08:50 and
09:00. There is no fallback run yet; later measurements can justify moving the
time or adding a fallback if needed.

While this feature branch is being verified, the workflow contains a narrow
push bootstrap that matches only changes to the workflow file on
`feat/static-provider`. Scheduled workflows and manual dispatch depend on the
workflow being present on the default branch; the bootstrap must be removed
before the final merge.

## Architecture boundary

The local application and static deployment mode remain peers that share
parsing, data semantics, and browser behavior where practical. The local SQLite
application does not depend on Pages build state, and the static provider does
not depend on a long-running Python server.

If browser code later grows enough to justify another split, separate it by
behavior or provider responsibility rather than introducing a JavaScript
framework solely for file organization.
