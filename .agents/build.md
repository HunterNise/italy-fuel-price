# Build and test conventions

Use [`DEVELOPMENT.md`](../DEVELOPMENT.md) for the canonical human-facing build,
run, and test commands. Do not duplicate those commands here unless an
agent-specific exception is required.

## Verification scope

- Documentation-only changes: run the repository whitespace/diff checks and
  inspect changed links, paths, commands, headings, code fences, and factual
  current/planned status.
- Station-map Python/backend changes: run the baseline checks from
  `DEVELOPMENT.md`, plus a focused local-server smoke test when behavior is
  user-visible.
- Browser/UI changes: run the baseline checks and exercise the affected
  interaction in the local map; preserve English/Italian behavior when
  relevant.
- Static-data builder changes: run the baseline unit suite and, when source-data
  behavior is relevant, build once from cached real MIMIT CSVs. A live download
  is an integration check, not normal CI.
- Analysis changes: compile the affected scripts and run the smallest relevant
  inspection, plotting, or update command supported by the environment.
- CI/workflow changes: keep ordinary checks deterministic and network
  independent. Live source downloads belong in explicit integration/deployment
  workflows.

## Generated artifacts

- Do not commit station-map runtime data/cache, generated Pages datasets,
  rolling-history state, analysis output, or temporary measurement artifacts.
- Prefer `/tmp` or the repository's ignored `tmp/` directory for generated
  verification output.
- A failed live-data build must not overwrite or publish a known-good static
  deployment.
