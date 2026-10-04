# Italy Fuel Price

Tools for exploring and analysing Italian road-fuel prices using public data,
with a preference for primary and official sources.

The repository contains two related components:

- [`station_map/`](station_map/) — an interactive local map of current Italian
  fuel-station prices and local station history.
- [`analysis/`](analysis/) — a reproducible toolkit for national and historical
  fuel-price analysis and price decomposition.

## Start here

- [`DEVELOPMENT.md`](DEVELOPMENT.md) — build, run, test, branch, and release
  workflow.
- [`station_map/README.md`](station_map/README.md) — current station-map usage.
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

The local station map is the working application. Repository CI and the
validated static-data builder are in place as foundations for a GitHub Pages
deployment; the static browser provider and Pages deployment workflow are not
yet connected.

## Data sources and licensing

Project code is released under the [MIT License](LICENSE).

Official source data and third-party material have their own provenance and reuse terms, see [`DATA_SOURCES_AND_LICENSES.md`](DATA_SOURCES_AND_LICENSES.md).
