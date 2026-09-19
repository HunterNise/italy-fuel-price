#!/usr/bin/env python3
from serve_map import init_db, sync_current, sync_state

if __name__ == "__main__":
    init_db()
    result = sync_current(save_raw=True)
    state = sync_state()
    print("MIMIT current snapshot synchronized")
    for key, value in result.items():
        print(f"{key}: {value}")
    print(f"local_history_days: {state.get('history_days', 0)}")
    print(f"local_history_range: {state.get('history_start')} .. {state.get('history_end')}")
