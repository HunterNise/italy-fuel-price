# Project guide

## Mission

Maintain tools for transparent exploration and analysis of Italian road-fuel
prices using official public data.

The repository has two related components:

- `station_map/`: current station-level prices and local station history.
- `analysis/`: national and historical analysis and price decomposition.

Prefer simple, explicit implementations over unnecessary frameworks or
abstractions.

## Project principles

- Prefer official (MIMIT and MASE) data sources.
- Do not silently interpolate or manufacture missing observations.
- Keep observed, curated, and derived values distinguishable.
- Keep calculations and filtering behavior transparent to the user.
- Do not commit station-map runtime data from `station_map/data/` or
  `station_map/cache/`.
- Preserve the local application while static/GitHub Pages support is developed;
  do not make one deployment mode depend unnecessarily on the other.
- Avoid architectural expansion until a concrete feature requires it.
- Preserve English/Italian UI behavior when changing user-facing map features.

## Required routing

Before repository work, read [`.agents/README.md`](.agents/README.md) and follow
the applicable instructions.

For read-only tasks, inspect the relevant source and documentation before
drawing conclusions.

Do not modify repository files, Git history, remotes, or GitHub state unless the
user has requested the corresponding change.

For non-trivial design or architectural changes, explain the proposed direction
and tradeoffs before implementation unless the user has already explicitly
approved that design.

## Handoffs

Report the concrete outcome first: what changed, what was verified, and any
meaningful limitation or next decision.

Do not narrate routine commands or claim checks that were not actually run.
