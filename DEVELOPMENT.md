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

## Check static/local station parity

For a cached real MIMIT snapshot and its generated public data, compare local
current-snapshot semantics against the generated static cells:

```bash
python3 tools/check_static_parity.py \
  --registry-file /path/to/anagrafica_impianti_attivi.csv \
  --price-file /path/to/prezzo_alle_8.csv \
  --data-dir /tmp/italy-fuel-web-data
```

The checker runs representative national city probes plus automatically derived
probes on populated 0.5° grid boundaries. It compares full station-result tuples
including station ID, coordinates, address, road type, price, communication
timestamp, observed date, fuel/service mode, and rounded distance.

The network-independent unit suite also contains synthetic cross-cell parity
cases, so boundary regressions fail normal repository checks.

## Deploy GitHub Pages

The Pages workflow is `.github/workflows/pages.yml`. Before its first deployment,
configure the repository once in GitHub:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. If a `github-pages` environment already exists with branch restrictions,
   allow the current verification branch temporarily. After the final merge,
   restrict deployment to `main`.

A deployment run:

1. runs the network-independent repository checks;
2. downloads one coherent MIMIT/ISTAT source bundle;
3. restores the newest non-expired `pages-history-state` Actions artifact when
   one exists;
4. generates validated static data from the cached source bundle and restored
   rolling state;
5. runs real-snapshot static/local parity against the same MIMIT inputs;
6. assembles the allowlisted site;
7. uploads the refreshed history state as a 30-day Actions artifact;
8. uploads the GitHub Pages artifact, including generated dotfiles;
9. deploys it through the `github-pages` environment.

The steady-state triggers are manual dispatch plus one daily schedule:

```yaml
schedule:
  - cron: "15 9 * * *"
    timezone: "Europe/Rome"
```

GitHub scheduled workflows run from the latest commit on the default branch, so
the daily trigger is inactive while this workflow exists only on
`feat/static-provider`. The pre-merge workflow temporarily keeps a path-filtered
push bootstrap for that feature branch; remove the bootstrap before merging the
deployment work to `main`.

The 09:15 Rome time is deliberately away from the top of the hour. The first
publication measurement on 2026-10-05 showed the price snapshot switching
between 08:40 and 08:50 and the registry switching between 08:50 and 09:00,
with both stable from 09:00 onward. Keep collecting measurements before adding a
fallback schedule.

Rolling public history is stored only as a GitHub Actions artifact and is
restored on later distinct workflow runs. The state file is not committed and
is not included in the Pages site. A GitHub **rerun** is not a valid persistence
test because prior-attempt artifacts from that same workflow run are not
reliably available to the new attempt; verify restoration with a separate later
workflow run instead.

Since this is a public repository, do not place secrets or user-private data in
the history artifact; the current state contains only derived public MIMIT
snapshots.

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
