#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import tarfile
import urllib.request
from datetime import datetime
from pathlib import Path

from fuelmap import __version__, db, mimit
from fuelmap.config import CACHE

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

    observed_date = mimit.parse_extract_date(first)
    reader = csv.DictReader(txt, delimiter=delimiter_for(observed_date))
    fields = {str(x).strip().lower(): x for x in (reader.fieldnames or [])}

    required = ["idimpianto", "desccarburante", "prezzo", "isself", "dtcomu"]
    if not all(key in fields for key in required):
        raise ValueError(f"{label}: unexpected header {reader.fieldnames!r}")

    captured_at = datetime.now().isoformat(timespec="seconds")
    batch = []
    count = 0

    for row in reader:
        try:
            batch.append(
                (
                    str(row[fields["idimpianto"]]).strip(),
                    observed_date,
                    str(row[fields["desccarburante"]]).strip(),
                    int(str(row[fields["isself"]]).strip()),
                    float(str(row[fields["prezzo"]]).strip().replace(",", ".")),
                    str(row[fields["dtcomu"]]).strip(),
                    "mimit_08_archive",
                    captured_at,
                )
            )
        except Exception:
            continue

        if len(batch) >= 10000:
            count += db.insert_archive_rows(batch)
            batch = []

    if batch:
        count += db.insert_archive_rows(batch)

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
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith(".csv"):
                continue
            source = archive.extractfile(member)
            if source is None:
                continue
            try:
                total += ingest_stream(source, member.name)
                files += 1
            except Exception as exc:
                print("SKIP", member.name, exc)
    print(f"Archive complete: {files} CSV files, {total:,} rows")


def coverage():
    rows = db.history_coverage()
    if not rows:
        print("history database is empty")
        return
    for source, start, end, count, days in rows:
        print(
            f"{source:20s} {start} .. {end} | "
            f"{days:,} dates | {count:,} rows"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Optional: index completed MIMIT quarterly station-price archives. "
            "The live map does not need this for current snapshots."
        )
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    command = sub.add_parser("download-and-index")
    command.add_argument("year", type=int)
    command.add_argument("quarter", type=int, choices=[1, 2, 3, 4])

    command = sub.add_parser("index-archive")
    command.add_argument("path")

    sub.add_parser("coverage")
    args = parser.parse_args()

    if args.cmd == "download-and-index":
        index_archive(download_quarter(args.year, args.quarter))
    elif args.cmd == "index-archive":
        index_archive(args.path)
    else:
        coverage()


if __name__ == "__main__":
    main()
