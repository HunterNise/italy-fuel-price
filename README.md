# Italy Fuel Price

Tools for exploring and analysing Italian road-fuel prices using official public
data.

The repository currently contains two related projects:

- [`station_map/`](station_map/) — an interactive local map of current Italian
  fuel-station prices using the MIMIT station registry and daily price snapshot.
- [`analysis/`](analysis/) — a reproducible toolkit for national and historical
  fuel-price analysis and price decomposition.

## Station map

Start the local application with:

```bash
./station_map/run.sh
```

Then open:

```text
http://127.0.0.1:8000
```

The map downloads current MIMIT data into local runtime storage. Its `data/` and
`cache/` directories are intentionally not tracked by Git.
See [`station_map/README.md`](station_map/README.md) for usage, history support,
and implementation details.

## Analysis toolkit

Create an environment and install its dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt
```

Examples and data notes are documented in
[`analysis/README.md`](analysis/README.md).

## Data principles

- Prefer official MIMIT/MASE sources.
- Keep observed and derived values distinguishable.
- Do not silently interpolate missing observations.
- Treat current station snapshots as replaceable data rather than repository
  source files.

## Repository status

The station map currently runs as a local Python application.
A static web deployment using GitHub Actions and GitHub Pages is planned, but is
not yet part of the repository.
