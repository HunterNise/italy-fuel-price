#!/usr/bin/env python3
from serve_map import init_db, sync_current

if __name__ == "__main__":
    init_db()
    result = sync_current(save_raw=True)
    print("MIMIT snapshot synchronized")
    for key, value in result.items():
        print(f"{key}: {value}")
