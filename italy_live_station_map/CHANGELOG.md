# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The releases below **0.8.2 are reconstructed from the iterative development
history**. The earlier `v1`…`v8` ZIP names were development labels rather than
formal semantic-version tags. Semver becomes the canonical version scheme from
0.8.2 onward.

## [Unreleased]

### Planned
- Evaluate route-aware fuel-stop planning without coupling it to the station-map core.

## [0.8.2] - 2026-09-19

### Changed
- Refactored the monolithic Python server into `fuelmap/` modules for
  configuration, persistence, MIMIT ingestion, services and HTTP serving.
- Split the single-file frontend into `index.html`, `static/styles.css` and
  `static/app.js`.
- Kept `serve_map.py`, `sync_current.py`, `history_index.py`, `run.sh` and
  `run.bat` backward-compatible as entry points.
- Made current MIMIT registry + price replacement atomic: both files are parsed
  successfully before one SQLite transaction updates the live snapshot.
- Enabled SQLite WAL mode and a busy timeout for threaded-server concurrency.
- Restricted static-file serving to paths inside the project root.
- Added `--version` to the server and archive-index commands.

### Added
- `ARCHITECTURE.md`.
- Machine-readable version source in `fuelmap/version.py`.
- Formal semantic-version changelog.

## [0.8.1] - 2026-09-19

### Changed
- Petrol became the default fuel.
- Raised the relative-price legend slightly to reduce marker overlap.
- Improved keyboard-shortcut box sizing.
- Reworked the help dialog into a practical map-use guide.

## [0.8.0] - 2026-09-19

### Changed
- Reworked history storage so nationwide current prices are kept only as the
  newest snapshot while rolling history is retained for stations in viewed areas.
- Reduced station-history controls to 7/30/90-day views.
- Clarified that histogram counts all filtered stations while `Show` only limits
  ranking rows.
- Fixed Leaflet resize after docking/undocking the ranking panel.
- Improved flag rendering with inline SVGs.
- Reworked help layout into two shortcut columns.
- Repositioned map navigation controls.

## [0.7.0] - 2026-09-19

### Added
- Docked ranking layout.
- Italian/English localization.
- Location search.
- Keyboard shortcuts and visible pan/zoom controls.
- Help dialog.
- Discrete price-color bands.
- Fast local station-history controls.

## [0.6.0] - 2026-09-19

### Added
- Local price-distribution histogram.
- Visible-set price percentiles in station ranking.

## [0.5.0] - 2026-09-19

### Added
- Fill-size-adjusted savings.
- Price freshness display and stale-price filtering.

## [0.4.0] - 2026-09-19

### Added
- Faded search-radius overlay.
- Ranked nearby-stations side panel.
- Price, distance, local-median difference and fill-savings display.

## [0.3.0] - 2026-09-19

### Changed
- Replaced the unreliable station-search API backend with the official MIMIT
  station-registry and daily-price CSVs joined locally by station ID.
- Made launch scripts independent of the shell's working directory.

### Added
- Local caching of the two current official MIMIT CSVs.

## [0.2.0] - 2026-09-19

### Added
- SQLite-backed station history.
- 30/90-day station sparklines.
- Optional quarterly historical-archive downloader/indexer.

## [0.1.0] - 2026-09-19

### Added
- Initial interactive Leaflet/OpenStreetMap station-price prototype.
- Fuel/service/radius controls and price-colored station markers.
- First live-data attempt using public MIMIT station-search endpoints.
