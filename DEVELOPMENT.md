# Development

This document owns the repository's human-facing build, run, test, branch, and
release workflow.

## Baseline verification

From the repository root:

```bash
python3 -m compileall -q station_map analysis/scripts tools tests
python3 station_map/serve_map.py --version
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The same network-independent baseline runs in
[`.github/workflows/check.yml`](.github/workflows/check.yml).

## Run the local station map

```bash
./station_map/run.sh
```

Then open:

```text
http://127.0.0.1:8000
```

For local sync/history behavior, see
[`station_map/README.md`](station_map/README.md).

## Build static web data

Use cached MIMIT inputs for repeatable local verification:

```bash
python3 tools/build_web_data.py \
  --output /tmp/italy-fuel-web-data \
  --registry-file /path/to/anagrafica_impianti_attivi.csv \
  --price-file /path/to/prezzo_alle_8.csv \
  --localities-file /path/to/LocalitaPuntuali_21.zip \
  --municipalities-2021-file /path/to/Limiti2021_g.zip \
  --history-state-output /tmp/italy-fuel-history-state.json
```

Use live current feeds only when an integration/deployment check is intended:

```bash
python3 tools/build_web_data.py \
  --output /tmp/italy-fuel-web-data \
  --download-localities \
  --history-state-output /tmp/italy-fuel-history-state.json
```

Generated web data and rolling-history state are build artifacts and are not
committed.

## Assemble the static Pages site

After generating public web data, assemble the deployable site with:

```bash
python3 tools/build_static_site.py \
  --data-dir /tmp/italy-fuel-web-data \
  --output /tmp/italy-fuel-pages-site
```

Preview the exact assembled artifact locally:

```bash
python3 -m http.server 8765 --directory /tmp/italy-fuel-pages-site
```

The site assembler uses an explicit frontend/data allowlist, generates the
static runtime configuration, writes `.nojekyll`, and rejects unexpected files
instead of copying the whole `station_map/` tree.

The assembled site is a build artifact and is not committed.

## Analysis toolkit

Create an environment when the analysis dependencies are needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt
```

Inspect the embedded analysis data with:

```bash
python3 analysis/scripts/inspect_data.py
```

See [`analysis/README.md`](analysis/README.md) for plotting, update, provenance,
and interpolation behavior.

## Branch and merge workflow

`main` is intended to stay green and releasable.

For non-trivial work, create a short-lived branch from an up-to-date `main`:

```bash
git switch main
git pull --ff-only
git switch -c feat/<short-name>
```

Use concise prefixes such as `feat/`, `fix/`, `ci/`, `docs/`, or `refactor/`.
There is no permanent `develop` branch.

Keep commits reviewable and merge only after the branch `Checks` workflow
passes.

Pull requests are optional. Use one when the consolidated GitHub review,
discussion, or merge UI is useful. For straightforward solo work, a reviewed
and green short-lived branch may be fast-forwarded directly into `main`.

Prefer a fast-forward merge when `main` has not diverged. If `main` has moved,
rebase the feature branch onto the latest `main`, rerun checks, then
fast-forward it.

## Version and tag workflow

Semantic Versioning currently applies to the station map. The analysis toolkit
does not have an independent release lifecycle.

The authoritative station-map version is `station_map/fuelmap/version.py`.

The station-map version is a lightweight working milestone rather than a formal
release gate.

A bounded application change that produces a meaningful working state may bump
the version and add a concise human-readable changelog entry.

Documentation-only, repository-maintenance, test-only, CI-only, and internal
changes normally do not bump the application version or add a feature changelog
entry.

Git tags are reserved for selected stable milestones and do not need to exist
for every application version.

Use descriptive component-prefixed tag names when useful. For example, the
stable local milestone before static deployment work is:

```text
station-map-local-v0.8.10
```

A tag identifies the whole repository snapshot at that commit, even when the
version number follows one component.

Scheduled/current-data refreshes do not create source commits, version bumps, or
release tags.
