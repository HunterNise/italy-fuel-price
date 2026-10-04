# Italy Fuel Price

Tools for exploring and analysing Italian road-fuel prices using public data,
with a preference for primary and official sources.

The repository contains two related components:

- [`station_map/`](station_map/) — an interactive map of current Italian
  fuel-station prices, with a local Python/SQLite mode and browser support for
  generated static data.
- [`analysis/`](analysis/) — a reproducible toolkit for national and historical
  fuel-price analysis and price decomposition.

## Start here

- [`DEVELOPMENT.md`](DEVELOPMENT.md) — build, run, test, branch, and release
  workflow.
- [`station_map/README.md`](station_map/README.md) — current local station-map
  usage.
- [`analysis/README.md`](analysis/README.md) — analysis toolkit usage and data
  semantics.
- [`ROADMAP.md`](ROADMAP.md) — future ideas and planned work.
- [`DATA_SOURCES_AND_LICENSES.md`](DATA_SOURCES_AND_LICENSES.md) — data
  provenance, attribution, and third-party licensing.

## Data principles

- Prefer primary and official sources when available.
- Keep observed/official, curated, derived, and secondary values
  distinguishable.
- Do not silently interpolate missing observations.
- Treat current station snapshots as replaceable runtime/build data rather than
  repository source files.

## Repository status

The local Python/SQLite station map remains the working application. Repository
CI, validated static-data generation, static/local parity checks, allowlisted
site assembly, GitHub Pages deployment, and rolling seven-day public history
state persistence are implemented. Scheduled refresh timing and stale-data
status remain deployment follow-up work.

## Data sources and licensing

Project code is released under the [MIT License](LICENSE).

Official source data and third-party material have their own provenance and
reuse terms, see
[`DATA_SOURCES_AND_LICENSES.md`](DATA_SOURCES_AND_LICENSES.md).
