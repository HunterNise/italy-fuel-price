
# Italy fuel-price toolkit

A small reproducible package for charting Italian road-fuel prices and their
price decomposition.

## What is included

`data/observations.csv`
: The exact compact working dataset used by the plotting scripts. It is in
  **long, labelled form**: each row records the date, frequency, fuel, geographic
  scope, network, service mode, unit, final price, net/industrial price, excise,
  VAT, total taxes, provenance, partial-period flag and interpolation flag.

`data/sources.csv`
: Official source catalogue and granularity notes.

`data/availability.csv`
: Quick inventory of what is embedded and what is not.

`data/reference/excise_schedule.csv`
: Excise schedule used to reproduce the derived decomposition where official
  component values are not embedded.

`data/reference/vat_schedule.csv`
: VAT schedule used by the same decomposition.

`scripts/plot_decomposition.py`
: One-fuel stacked price decomposition.

`scripts/plot_compare.py`
: Final-price comparison across fuels.

`scripts/update_data.py`
: Fetch/append MIMIT national daily data, download the current MIMIT
  station-level snapshot, or import official MASE monthly/weekly CSV files.

`scripts/inspect_data.py`
: Prints the actually available frequencies, date ranges and partial rows.

## Important provenance distinction

The package deliberately distinguishes **observed/curated final prices** from
**derived components**.

The compact monthly petrol/diesel chart copy in this package covers 2000 through
September 2026. The final-price series is the working copy used to reproduce the
charts in the conversation. The component columns are reconstructed using the
statutory excise/VAT schedules and are labelled as derived.

For strict research use, download fresh official MASE CSV exports and import them
with `update_data.py import-mase`. The official MASE export contains the
decomposition fields directly.

The daily September 2026 national data are a compact curated series used for the
recent charts. MIMIT's public national page exposes the newest and previous
national values, while its station-level daily open-data feed is the true raw
daily source.

## Official granularity

### MASE
* Monthly petrol/diesel series: **1996-present**
* Weekly series: **2005-present**
* Petrol and diesel use self-service prices.
* The MASE site's "daily" value is derived from the weekly observation; it is
  not an independent daily national measurement.

### MIMIT
* Station-level `Prezzo alle 8`: **daily**, archive from March 2015.
* Current station snapshot:
  `https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv`
* Historical station archives are grouped by quarter.
* Daily national-average page: latest + previous national self-service average.
* Regional/provincial average files are also published daily.

Therefore the finest genuine raw source is MIMIT **station-by-station daily**,
not a long national daily series.

## No silent interpolation

The plotting layer follows this rule:

1. Use exact requested-frequency data when embedded.
2. A finer series may be aggregated to a coarser requested frequency.
3. Coarser data are **never** silently expanded to a finer frequency.
4. If you request weekly/daily data and only monthly data are available, the
   script raises an error.
5. Interpolation happens only with:
   `--interpolate linear` or `--interpolate ffill`.
6. Interpolated rows are explicitly tagged `is_interpolated=True`.

Partial periods are also stored explicitly (`is_partial=True`) rather than being
silently treated as complete.

## Tick density and grid layering

Both chart scripts expose:

* `--x-tick-every N`
* `--y-tick-step VALUE`

Examples:

* monthly chart, one label every 24 months: `--x-tick-every 24`
* daily chart, one label every 3 days: `--x-tick-every 3`
* y ticks every €0.25/l: `--y-tick-step 0.25`

The dotted major grid is intentionally assigned a z-order **above the filled
areas**, while the final-price line is drawn above the grid. This prevents the
vertical/horizontal dotted guides from disappearing inside stacked areas.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Inspect what is available

```bash
python scripts/inspect_data.py
```

## Plot a decomposition

```bash
python scripts/plot_decomposition.py \
  --fuel petrol \
  --start 2000-01-01 \
  --end 2026-09-30 \
  --frequency monthly \
  --x-tick-every 24 \
  --y-tick-step 0.25 \
  --output output/petrol_monthly.png
```

## Compare final prices

```bash
python scripts/plot_compare.py \
  --fuels petrol diesel \
  --start 2000-01-01 \
  --end 2026-09-30 \
  --frequency monthly \
  --x-tick-every 24 \
  --output output/petrol_vs_diesel.png
```

## Update the daily national data

```bash
python scripts/update_data.py mimit-national
```

Run that once per day after MIMIT updates its public page. It appends/replaces
that day's petrol/diesel national ordinary-road self-service values.

## Download the finest current raw snapshot

```bash
python scripts/update_data.py mimit-station
```

This downloads MIMIT's current station-level 08:00 CSV to `data/raw/`.
As of 10 February 2026, MIMIT documents `|` as the field separator for the
station/anagraphic files.

## Import official MASE exports

Download the desired CSV from:

`https://sisen.mase.gov.it/dgsaie/open-data`

Then:

```bash
python scripts/update_data.py import-mase my_file.csv \
  --fuel petrol --frequency monthly
```

or:

```bash
python scripts/update_data.py import-mase my_weekly_file.csv \
  --fuel diesel --frequency weekly
```

The importer recognises common Italian column names such as `Anno`, `Mese`,
`Data`, `Prezzo`, `IVA`, `Accisa`, `Netto`, converts the MASE per-1,000-unit
scale to per-unit values when detected, and preserves missing component fields
as missing.

## Research caveats

* Do not mix €/litre fuels with €/kg fuels on one final-price chart without a
  deliberate unit conversion. The comparison script rejects mixed units.
* A national arithmetic station average and a MASE statistical price series are
  not automatically interchangeable.
* Station-level MIMIT snapshots are very large. They are intentionally not
  bundled in this compact ZIP.
* A partial current month should not be compared with completed months without
  noting the partial coverage flag.
