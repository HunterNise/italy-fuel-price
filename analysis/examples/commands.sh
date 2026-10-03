# Run from the package root.

# Monthly petrol decomposition, 2000-2026, x tick every 24 months.
python scripts/plot_decomposition.py \
  --fuel petrol --start 2000-01-01 --end 2026-09-30 --frequency monthly \
  --x-tick-every 24 --y-tick-step 0.25 \
  --output output/petrol_monthly.png

# Daily diesel zoom, September 2026, x tick every 3 days.
python scripts/plot_decomposition.py \
  --fuel diesel --start 2026-09-01 --end 2026-09-18 --frequency daily \
  --x-tick-every 3 --y-tick-step 0.25 \
  --output output/diesel_daily.png

# Compare final petrol and diesel prices.
python scripts/plot_compare.py \
  --fuels petrol diesel --start 2000-01-01 --end 2026-09-30 --frequency monthly \
  --x-tick-every 24 --y-tick-step 0.25 \
  --output output/petrol_vs_diesel.png

# Asking for weekly data without an embedded weekly source fails rather than
# silently inventing it from monthly observations:
python scripts/plot_compare.py \
  --fuels petrol diesel --start 2020-01-01 --end 2021-12-31 --frequency weekly

# If you explicitly WANT interpolation, request it:
python scripts/plot_compare.py \
  --fuels petrol diesel --start 2020-01-01 --end 2021-12-31 --frequency weekly \
  --interpolate linear --x-tick-every 8

# Append today's MIMIT national average when the official page has updated:
python scripts/update_data.py mimit-national

# Download the current station-level raw snapshot:
python scripts/update_data.py mimit-station

# After manually downloading a MASE export from the official portal:
python scripts/update_data.py import-mase path/to/benzina_mensile.csv --fuel petrol --frequency monthly
python scripts/update_data.py import-mase path/to/gasolio_settimanale.csv --fuel diesel --frequency weekly
