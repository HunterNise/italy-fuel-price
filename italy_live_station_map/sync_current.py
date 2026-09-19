#!/usr/bin/env python3
from fuelmap import __version__
from fuelmap import db, mimit

if __name__ == "__main__":
    db.init_db()
    result = mimit.sync_current(save_raw=True)
    state = db.sync_state()
    print(f"Italy Fuel Price Map {__version__}")
    print("MIMIT current snapshot synchronized")
    for key, value in result.items():
        print(f"{key}: {value}")
    print(f"tracked_stations: {state.get('tracked_station_rows', 0)}")
    print(f"local_history_days: {state.get('history_days', 0)}")
    print(f"local_history_range: {state.get('history_start')} .. {state.get('history_end')}")
