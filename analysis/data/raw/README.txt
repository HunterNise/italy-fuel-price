This folder is intentionally empty in the compact package.

The true upstream raw datasets can be large (especially MIMIT station-level daily archives).
Use scripts/update_data.py to:
  * append the latest MIMIT national daily averages;
  * download the current MIMIT station-level 08:00 snapshot;
  * import official MASE monthly/weekly CSV exports you download from the MASE open-data portal.

No script silently fabricates weekly or daily observations from monthly data.
