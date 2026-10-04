# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the station map uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This file records effective station-map version history. Git tags are reserved
for selected stable milestones and do not need to exist for every entry.

The versions below **0.8.2 are reconstructed from the iterative development
history**. The earlier `v1`…`v8` ZIP names were development labels rather than
formal semantic-version tags. SemVer becomes the canonical station-map version
scheme from 0.8.2 onward.

## [0.9.4] - 2026-10-04

### Added
- Added a validated GitHub Pages deployment workflow that builds live public data, checks static/local station parity, assembles the allowlisted site, and deploys the Pages artifact.
- Added a source-bundle helper so the data build and parity check use the exact same downloaded MIMIT/ISTAT snapshot files.

### Changed
- Pages artifact upload explicitly includes generated dotfiles such as `.nojekyll` and the site-build manifest.
- The first feature-branch deployment uses a narrow workflow-file push bootstrap because manual `workflow_dispatch` is only available after the workflow exists on the default branch.

## [0.9.3] - 2026-10-04

### Added
- Added an allowlisted static-site assembler for the GitHub Pages artifact.
- Added validation that generated public data contain exactly the files declared by their metadata.

### Changed
- Static-site builds generate the static browser runtime configuration and `.nojekyll` instead of copying the tracked local runtime configuration.
- Site assembly now rejects unexpected generated-data files and private/source artifact types before publication.

## [0.9.2] - 2026-10-04

### Added
- Added a same-vintage ISTAT 31 December 2021 municipality lookup for static locality search.

### Changed
- Locality results now show their parent municipality name, such as `Lido di Ostia — Roma`, instead of exposing `PRO_COM` as the normal disambiguator.
- Cached locality builds now require the matching 2021 administrative-boundaries archive so locality and municipality labels use the same territorial snapshot.

## [0.9.1] - 2026-10-04

### Added
- Added optional static place search across the official ISTAT 2021 residential point-locality dataset, covering inhabited centres and inhabited nuclei in addition to municipalities.

### Changed
- Static place search now ignores punctuation differences such as spaces and hyphens and combines municipality/locality matches with deterministic ranking.
- Locality data are generated as a separate lazy-loaded public index so they do not increase the initial page payload.

## [0.9.0] - 2026-10-04

### Added
- Added a browser data-provider layer so the map can use either the existing local API or generated static data.
- Added a static provider that loads only the required 0.5° station cells, searches the generated municipality index, and exposes the generated seven-day price history.
- Added provider capabilities so unsupported controls, such as manual sync and longer history windows, are hidden automatically in static mode.

### Changed
- Decoupled the frontend from direct `/api/*` requests while preserving the existing local Python/SQLite behavior.
- Added English and Italian status/help text for the static-data mode.

## [0.8.11] - 2026-10-03

### Changed
- Use Rome as the default map location when no browser preference exists.
- Preserve the last visited location in browser `localStorage`.
- Complete migration from legacy preference keys and remove them afterward.

### Fixed
- Clearing the current preference state no longer restores an older location from a legacy preference key.


## [0.8.10] - 2026-09-19

### Changed
- Made the collapsed top context card shrink to its content instead of reserving a fixed width.
- Restored comfortable vertical padding and line spacing in the collapsed card.
- Kept the expanded-panel subtitle on the same line as the title with explicit spacing.
- Moved Filters onto the Sort/Show control row with a subtle separator.
- Removed obsolete Leaflet-scale positioning CSS left over from pre-custom-scale versions.

## [0.8.9] - 2026-09-19

### Changed
- Replaced the Leaflet scale with a custom bottom-left scale directly above the price legend.
- Reworked the collapsed context card into three explicit lines: location; fuel/mode/radius/fill; freshness/stale/shown.
- Reduced collapsed-card width and vertical spacing.
- Restored `Show` to display-limit semantics only (`all`, `50`, `25`, `10`).
- Added a separate Filters popover with combinable maximum-price and maximum-distance sliders.
- Added compact active-filter chips and an active-filter count.
- Filtering order is now: radius/fuel/mode/freshness -> optional filters -> sort -> Show -> map/ranking/histogram.
- Migrates 0.8.8 threshold-mode preferences into the new filter model.

## [0.8.8] - 2026-09-19

### Changed
- Restored the station summary chips in the expanded top panel.
- The collapsed context card remains compact and keeps only its two-line summary.

## [0.8.7] - 2026-09-19

### Changed
- Reduced the compact top context card and rewrote its summary as two dense lines.
- Removed duplicate top-panel station-count and price-range chips; those values already live in the ranking panel and map legend.
- Compact summary now places freshness and stale-price count on its second line.
- Moved the Leaflet distance scale directly above the price legend, left-aligned.
- Extended `Show` with two threshold modes: maximum price and maximum straight-line distance.
- Threshold modes expose one dynamic slider and keep map markers, ranking rows and histogram on the same shown subset.
- Threshold values are persisted with the other browser UI preferences.

## [0.8.6] - 2026-09-19

### Fixed
- Disabled HTTP caching for the local application shell (`/`, `index.html`, and `static/`) so overwritten UI patches are loaded immediately instead of being hidden behind `304 Not Modified` responses.
- Ignore `If-Modified-Since` / `If-None-Match` for local UI assets, preventing a browser from continuing to render an older interface after an upgrade.
- Added the application version as a cache-busting query string on `styles.css` and `app.js`.

### Clarified
- Browser `localStorage` still intentionally retains user UI preferences; this is separate from static-file caching and does not retain old application code.

## [0.8.5] - 2026-09-19

### Fixed
- Treat browser-side socket disconnects (`BrokenPipeError` / connection reset) as normal request cancellation instead of reporting a misleading HTTP 502 and traceback.
- Suppress duplicate identical `/api/stations` requests while the first matching request is still in flight.

### Changed
- No database, cache, history, ranking, or MIMIT synchronization behavior changed.

## [0.8.4] - 2026-09-19

### Changed
- Simplified the top control panel by removing the label-density and fit-radius controls.
- Compact/collapsed top panel is smaller; language/help/expand buttons move below the title/context summary.
- `Show` is now the single visibility control: the map markers, ranking rows and histogram always use the same shown station subset.
- `Show` defaults to `all`; old 0.8.3 browser preferences are migrated while resetting only this visibility default.
- Histogram now describes the shown subset rather than hidden stations.
- Savings and price percentiles continue to use the broader freshness-filtered local population as their reference.
- Price labels are automatic: persistent at closer zoom levels or when at most 12 stations are shown, hover-only otherwise.
- Fit-radius moved into the map navigation pad as a maximize control and now keeps the search point centered while choosing the tightest zoom that fits the radius.
- Selected stations use a soft halo and are brought to the front instead of receiving a thick square-like outline.

## [0.8.3] - 2026-09-19

### Added
- Price-label density modes: all, cheapest ~30%, or hover-only, with automatic full labels at close zoom.
- Bidirectional station selection between map markers and ranking rows.
- Fit-to-radius control.
- Persistent UI preferences for map centre/location label, fuel, service mode, radius, fill size, freshness, ranking options, label mode and collapsed-panel states.
- Context summary in the collapsed top panel so screenshots retain location and active settings.

### Changed
- Moved the relative-price legend back into the bottom-left corner and placed the Leaflet distance scale immediately beside it.
- Collapsed top controls now shrink into a compact contextual card instead of an empty title bar.
- Ranking addresses are visually compacted to reduce vertical noise.
- Help text now documents label-density and station-selection behavior.

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
