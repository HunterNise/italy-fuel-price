from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Iterable, Sequence

from .config import DB


SCHEMA = """
CREATE TABLE IF NOT EXISTS stations(
  station_id TEXT PRIMARY KEY,
  address TEXT,
  comune TEXT,
  provincia TEXT,
  road_type TEXT,
  lat REAL,
  lon REAL,
  registry_date TEXT,
  captured_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_stations_latlon ON stations(lat, lon);

CREATE TABLE IF NOT EXISTS current_prices(
  station_id TEXT NOT NULL,
  fuel TEXT NOT NULL,
  is_self INTEGER NOT NULL,
  price REAL NOT NULL,
  communicated_at TEXT,
  observed_date TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  PRIMARY KEY(station_id, fuel, is_self)
);
CREATE INDEX IF NOT EXISTS idx_current_prices_lookup
  ON current_prices(fuel,is_self,observed_date);

CREATE TABLE IF NOT EXISTS prices(
  station_id TEXT NOT NULL,
  observed_date TEXT NOT NULL,
  fuel TEXT NOT NULL,
  is_self INTEGER NOT NULL,
  price REAL NOT NULL,
  communicated_at TEXT,
  source TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  PRIMARY KEY(station_id, observed_date, fuel, is_self, source)
);
CREATE INDEX IF NOT EXISTS idx_prices_lookup
  ON prices(station_id, fuel, is_self, observed_date);

CREATE TABLE IF NOT EXISTS tracked_stations(
  station_id TEXT PRIMARY KEY,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=5.0)
    con.execute("PRAGMA busy_timeout=5000")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    con = connect()
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def commit_snapshot(
    registry_date: str,
    station_rows: Sequence[tuple],
    price_date: str,
    price_rows: Sequence[tuple],
    captured_at: str,
) -> None:
    """Replace the current nationwide snapshot atomically."""
    init_db()
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute("DELETE FROM stations")
        con.executemany(
            """
            INSERT INTO stations
              (station_id,address,comune,provincia,road_type,lat,lon,registry_date,captured_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            station_rows,
        )

        con.execute("DELETE FROM current_prices")
        con.executemany(
            """
            INSERT INTO current_prices
              (station_id,fuel,is_self,price,communicated_at,observed_date,captured_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            price_rows,
        )

        # Retain this new date only for stations the user has actually viewed.
        con.execute(
            """
            INSERT OR REPLACE INTO prices
              (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
            SELECT c.station_id,c.observed_date,c.fuel,c.is_self,c.price,c.communicated_at,
                   'mimit_08_tracked',c.captured_at
            FROM current_prices c
            JOIN tracked_stations t ON t.station_id=c.station_id
            """
        )

        con.executemany(
            "INSERT OR REPLACE INTO sync_state(key,value) VALUES(?,?)",
            [
                ("registry_date", registry_date),
                ("price_date", price_date),
                ("last_sync", captured_at),
            ],
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def sync_state() -> dict:
    init_db()
    con = connect()
    state = dict(con.execute("SELECT key,value FROM sync_state").fetchall())
    state["station_rows"] = con.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
    state["current_price_rows"] = con.execute("SELECT COUNT(*) FROM current_prices").fetchone()[0]
    hist = con.execute(
        "SELECT MIN(observed_date),MAX(observed_date),COUNT(DISTINCT observed_date) FROM prices"
    ).fetchone()
    state["history_start"] = hist[0]
    state["history_end"] = hist[1]
    state["history_days"] = hist[2] or 0
    state["tracked_station_rows"] = con.execute(
        "SELECT COUNT(*) FROM tracked_stations"
    ).fetchone()[0]
    con.close()
    return state


def nearby_candidates(
    fuel: str,
    want_self: bool,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
) -> list[tuple]:
    init_db()
    con = connect()
    rows = con.execute(
        """
        SELECT s.station_id,s.lat,s.lon,s.address,s.comune,s.provincia,s.road_type,
               p.price,p.communicated_at,p.observed_date
        FROM stations s
        JOIN current_prices p ON p.station_id=s.station_id
        WHERE lower(p.fuel)=lower(?)
          AND p.is_self=?
          AND s.lat BETWEEN ? AND ?
          AND s.lon BETWEEN ? AND ?
        """,
        (fuel, 1 if want_self else 0, min_lat, max_lat, min_lon, max_lon),
    ).fetchall()
    con.close()
    return rows


def track_station_ids(station_ids: Iterable[str]) -> None:
    ids = [str(x) for x in station_ids if str(x)]
    if not ids:
        return

    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        con.executemany(
            """
            INSERT INTO tracked_stations(station_id,first_seen,last_seen)
            VALUES(?,?,?)
            ON CONFLICT(station_id) DO UPDATE SET last_seen=excluded.last_seen
            """,
            [(sid, now, now) for sid in ids],
        )
        # Immediately seed today's history for newly viewed stations.
        con.execute(
            """
            INSERT OR REPLACE INTO prices
              (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
            SELECT c.station_id,c.observed_date,c.fuel,c.is_self,c.price,c.communicated_at,
                   'mimit_08_tracked',c.captured_at
            FROM current_prices c
            JOIN tracked_stations t ON t.station_id=c.station_id
            """
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def station_history(station_id: str, fuel: str, want_self: bool, days: int) -> dict:
    init_db()
    con = connect()
    flag = 1 if want_self else 0

    latest = con.execute(
        """
        SELECT MAX(observed_date) FROM prices
        WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
        """,
        (station_id, fuel, flag),
    ).fetchone()[0]

    if not latest:
        con.close()
        return {
            "points": [],
            "requested_days": days,
            "observed_days": 0,
            "missing_days": days,
            "start": None,
            "end": None,
            "available_total_days": 0,
            "available_start": None,
            "available_end": None,
            "interpolated": False,
        }

    end = date.fromisoformat(latest)
    start = end - timedelta(days=days - 1)

    rows = con.execute(
        """
        SELECT observed_date,price,source,communicated_at
        FROM prices
        WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
          AND observed_date BETWEEN ? AND ?
        ORDER BY observed_date
        """,
        (station_id, fuel, flag, start.isoformat(), end.isoformat()),
    ).fetchall()

    overall = con.execute(
        """
        SELECT MIN(observed_date),MAX(observed_date),COUNT(DISTINCT observed_date)
        FROM prices
        WHERE station_id=? AND lower(fuel)=lower(?) AND is_self=?
        """,
        (station_id, fuel, flag),
    ).fetchone()
    con.close()

    precedence = {"mimit_08_archive": 0, "mimit_08_tracked": 1, "mimit_08_current": 1}
    by_date = {}
    for observed, price, source, communicated in rows:
        item = {
            "date": observed,
            "price": price,
            "source": source,
            "communicated_at": communicated,
        }
        if (
            observed not in by_date
            or precedence.get(source, 9)
            < precedence.get(by_date[observed]["source"], 9)
        ):
            by_date[observed] = item

    points = [by_date[k] for k in sorted(by_date)]
    return {
        "points": points,
        "requested_days": days,
        "observed_days": len(points),
        "missing_days": max(0, days - len(points)),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "available_total_days": overall[2] or 0,
        "available_start": overall[0],
        "available_end": overall[1],
        "interpolated": False,
    }


def insert_archive_rows(rows: Sequence[tuple]) -> int:
    """Insert pre-normalized historical rows from a completed archive."""
    if not rows:
        return 0
    init_db()
    con = connect()
    con.executemany(
        """
        INSERT OR REPLACE INTO prices
          (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    con.commit()
    con.close()
    return len(rows)


def history_coverage() -> list[tuple]:
    init_db()
    con = connect()
    rows = con.execute(
        """
        SELECT source,MIN(observed_date),MAX(observed_date),
               COUNT(*),COUNT(DISTINCT observed_date)
        FROM prices
        GROUP BY source
        ORDER BY source
        """
    ).fetchall()
    con.close()
    return rows
