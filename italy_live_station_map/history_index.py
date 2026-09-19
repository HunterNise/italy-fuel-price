#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import tarfile
import urllib.request
from datetime import datetime
from pathlib import Path

from serve_map import CACHE, DB, init_db, parse_extract_date

ARCHIVE_URL = (
    "https://opendatacarburanti.mise.gov.it/"
    "categorized/prezzo_alle_8/{year}/{year}_{quarter}_tr.tar.gz"
)


def delimiter_for(observed_date):
    return "|" if observed_date >= "2026-02-10" else ";"


def ingest_stream(binary, label="<stream>"):
    txt = io.TextIOWrapper(
        binary, encoding="utf-8-sig", errors="replace", newline=""
    )
    first = txt.readline()
    if not first:
        return 0

    observed_date = parse_extract_date(first)
    reader = csv.DictReader(txt, delimiter=delimiter_for(observed_date))
    fields = {str(x).strip().lower(): x for x in (reader.fieldnames or [])}

    required = [
        "idimpianto",
        "desccarburante",
        "prezzo",
        "isself",
        "dtcomu",
    ]
    if not all(k in fields for k in required):
        raise ValueError(f"{label}: unexpected header {reader.fieldnames!r}")

    init_db()
    con = sqlite3.connect(DB)
    now = datetime.now().isoformat(timespec="seconds")
    sql = """
      INSERT OR REPLACE INTO prices
      (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
      VALUES(?,?,?,?,?,?,?,?)
    """

    batch = []
    count = 0
    for row in reader:
        try:
            item = (
                str(row[fields["idimpianto"]]).strip(),
                observed_date,
                str(row[fields["desccarburante"]]).strip(),
                int(str(row[fields["isself"]]).strip()),
                float(str(row[fields["prezzo"]]).strip().replace(",", ".")),
                str(row[fields["dtcomu"]]).strip(),
                "mimit_08_archive",
                now,
            )
        except Exception:
            continue

        batch.append(item)
        if len(batch) >= 10000:
            con.executemany(sql, batch)
            count += len(batch)
            batch = []

    if batch:
        con.executemany(sql, batch)
        count += len(batch)

    con.commit()
    con.close()
    print(f"{observed_date}: indexed {count:,} rows from {label}")
    return count


def download_quarter(year, quarter):
    CACHE.mkdir(parents=True, exist_ok=True)
    url = ARCHIVE_URL.format(year=year, quarter=quarter)
    destination = CACHE / f"{year}_{quarter}_tr.tar.gz"
    print("Downloading:", url)
    urllib.request.urlretrieve(url, destination)
    print(
        f"Saved {destination} "
        f"({destination.stat().st_size / 1024 / 1024:.1f} MB)"
    )
    return destination


def index_archive(path):
    path = Path(path)
    total = 0
    files = 0

    with tarfile.open(path, "r:gz") as tf:
        for member in tf:
            if not member.isfile() or not member.name.lower().endswith(".csv"):
                continue

            f = tf.extractfile(member)
            if f is None:
                continue

            try:
                total += ingest_stream(f, member.name)
                files += 1
            except Exception as e:
                print("SKIP", member.name, e)

    print(f"Archive complete: {files} CSV files, {total:,} rows")


def coverage():
    init_db()
    con = sqlite3.connect(DB)
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

    if not rows:
        print("history database is empty")
        return

    for source, start, end, count, days in rows:
        print(
            f"{source:20s} {start} .. {end} | "
            f"{days:,} dates | {count:,} rows"
        )


def main():
    p = argparse.ArgumentParser(
        description="Index MIMIT historical station-price archives."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download-and-index")
    d.add_argument("year", type=int)
    d.add_argument("quarter", type=int, choices=[1, 2, 3, 4])

    i = sub.add_parser("index-archive")
    i.add_argument("path")

    sub.add_parser("coverage")

    args = p.parse_args()

    if args.cmd == "download-and-index":
        index_archive(download_quarter(args.year, args.quarter))
    elif args.cmd == "index-archive":
        index_archive(args.path)
    else:
        coverage()


if __name__ == "__main__":
    main()
