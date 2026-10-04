# Project guide

## Mission

Maintain tools for transparent exploration and analysis of Italian road-fuel
prices using public data.

The repository has two related components:

- `station_map/`: current station-level prices and local station history.
- `analysis/`: national and historical analysis and price decomposition.

Prefer simple, explicit implementations over unnecessary frameworks or
abstractions.

## Project principles

- Prefer primary and official sources when available.
- Preserve source provenance and keep official/observed, curated, derived, and
  secondary values distinguishable.
- Do not silently interpolate or manufacture missing observations.
- Keep calculations and filtering behavior transparent to the user.
- Keep generated/runtime data out of source control.
- Preserve the local station-map application while static deployment support is
  developed; neither deployment mode should unnecessarily depend on the other.
- Avoid architectural expansion until a concrete feature requires it.
- Preserve English/Italian UI behavior when changing user-facing map features.

## Required routing

Before repository work, read [`.agents/README.md`](.agents/README.md) and follow
every instruction file routed by that index.

The routed instructions are mandatory. If applicable instructions conflict,
stop and report the conflict instead of silently choosing one.

For read-only tasks, inspect the relevant source and authoritative documentation
before drawing conclusions.

Do not modify repository files, Git history, remotes, or GitHub state unless the
user has requested the corresponding change.

Documentation ownership and routing are defined in
[`.agents/documentation.md`](.agents/documentation.md); do not duplicate those
rules here.

## Handoffs

Lead with the concrete outcome. Report what changed, what was verified, and any
meaningful limitation or next decision.

Do not narrate routine commands or claim checks that were not actually run.
