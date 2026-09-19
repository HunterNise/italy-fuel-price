#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sqlite3
import tarfile
import tempfile
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
DB=HERE/"data"/"station_history.sqlite"
CACHE=HERE/"cache"
CURRENT_URL="https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
ARCHIVE_URL="https://opendatacarburanti.mise.gov.it/categorized/prezzo_alle_8/{year}/{year}_{quarter}_tr.tar.gz"

def init_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB)
    con.execute("""
      CREATE TABLE IF NOT EXISTS prices(
        station_id TEXT NOT NULL,
        observed_date TEXT NOT NULL,
        fuel TEXT NOT NULL,
        is_self INTEGER NOT NULL,
        price REAL NOT NULL,
        communicated_at TEXT,
        source TEXT NOT NULL,
        captured_at TEXT NOT NULL,
        PRIMARY KEY(station_id,observed_date,fuel,is_self,source)
      )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_prices_lookup ON prices(station_id,fuel,is_self,observed_date)")
    con.commit(); con.close()

DATE_RE=re.compile(r"(\d{4}-\d{2}-\d{2})")

def extraction_date(line):
    m=DATE_RE.search(line)
    if not m: raise ValueError(f"Cannot parse extraction date from first line: {line!r}")
    return m.group(1)

def delimiter_for(obs_date):
    return "|" if obs_date >= "2026-02-10" else ";"

def ingest_stream(binary, source, label="<stream>"):
    """Read one MIMIT prezzo_alle_8 CSV: line 1 extraction date, line 2 header."""
    txt=io.TextIOWrapper(binary,encoding="utf-8-sig",errors="replace",newline="")
    first=txt.readline()
    if not first: return 0
    obs=extraction_date(first)
    delim=delimiter_for(obs)
    reader=csv.DictReader(txt,delimiter=delim)
    # normalize exact documented header capitalization
    fields={str(x).lower():x for x in (reader.fieldnames or [])}
    req=["idimpianto","desccarburante","prezzo","isself","dtcomu"]
    if not all(k in fields for k in req):
        raise ValueError(f"{label}: unexpected header {reader.fieldnames!r}")

    init_db()
    con=sqlite3.connect(DB)
    now=datetime.now().isoformat(timespec="seconds")
    sql="""INSERT OR REPLACE INTO prices
      (station_id,observed_date,fuel,is_self,price,communicated_at,source,captured_at)
      VALUES(?,?,?,?,?,?,?,?)"""
    batch=[]; count=0
    for row in reader:
        try:
            item=(str(row[fields["idimpianto"]]).strip(),obs,
                  str(row[fields["desccarburante"]]).strip(),
                  int(str(row[fields["isself"]]).strip()),
                  float(str(row[fields["prezzo"]]).strip().replace(",",".")),
                  str(row[fields["dtcomu"]]).strip(),source,now)
        except Exception:
            continue
        batch.append(item)
        if len(batch)>=10000:
            con.executemany(sql,batch); count+=len(batch); batch=[]
    if batch: con.executemany(sql,batch); count+=len(batch)
    con.commit(); con.close()
    print(f"{obs}: indexed {count:,} price rows from {label}")
    return count

def capture_current(save_raw=False):
    CACHE.mkdir(exist_ok=True)
    with urllib.request.urlopen(CURRENT_URL,timeout=60) as r:
        data=r.read()
    if save_raw:
        p=CACHE/f"prezzo_alle_8_{date.today().isoformat()}.csv"
        p.write_bytes(data); print(f"saved {p}")
    return ingest_stream(io.BytesIO(data),"mimit_08_current","current MIMIT snapshot")

def download_quarter(year,quarter,dest=None):
    CACHE.mkdir(exist_ok=True)
    url=ARCHIVE_URL.format(year=year,quarter=quarter)
    dest=Path(dest) if dest else CACHE/f"{year}_{quarter}_tr.tar.gz"
    print(f"downloading {url}")
    urllib.request.urlretrieve(url,dest)
    print(f"saved {dest} ({dest.stat().st_size/1024/1024:.1f} MB)")
    return dest

def index_archive(path):
    path=Path(path)
    total=0; files=0
    with tarfile.open(path,"r:gz") as tf:
        for member in tf:
            if not member.isfile() or not member.name.lower().endswith(".csv"):
                continue
            f=tf.extractfile(member)
            if f is None: continue
            try:
                total+=ingest_stream(f,"mimit_08_archive",member.name); files+=1
            except Exception as e:
                print(f"SKIP {member.name}: {e}")
    print(f"archive complete: {files} CSV file(s), {total:,} indexed rows")

def coverage():
    init_db()
    con=sqlite3.connect(DB)
    rows=con.execute("""
      SELECT source,MIN(observed_date),MAX(observed_date),COUNT(*),
             COUNT(DISTINCT observed_date)
      FROM prices GROUP BY source ORDER BY source
    """).fetchall()
    con.close()
    if not rows:
        print("history database is empty")
        return
    for src,a,b,n,days in rows:
        print(f"{src:20s} {a} .. {b} | {days:,} dates | {n:,} price rows")

def main():
    p=argparse.ArgumentParser(description="Build local station-level MIMIT price history.")
    sub=p.add_subparsers(dest="cmd",required=True)

    c=sub.add_parser("capture-current",help="Download/index today's official 08:00 snapshot.")
    c.add_argument("--save-raw",action="store_true")

    d=sub.add_parser("download-quarter",help="Download a quarterly historical price archive.")
    d.add_argument("year",type=int); d.add_argument("quarter",type=int,choices=[1,2,3,4])

    i=sub.add_parser("index-archive",help="Index a previously downloaded quarterly .tar.gz.")
    i.add_argument("path")

    q=sub.add_parser("download-and-index",help="Download and immediately index a quarterly archive.")
    q.add_argument("year",type=int); q.add_argument("quarter",type=int,choices=[1,2,3,4])

    sub.add_parser("coverage",help="Show dates/sources currently stored in history DB.")

    args=p.parse_args()
    if args.cmd=="capture-current": capture_current(args.save_raw)
    elif args.cmd=="download-quarter": download_quarter(args.year,args.quarter)
    elif args.cmd=="index-archive": index_archive(args.path)
    elif args.cmd=="download-and-index": index_archive(download_quarter(args.year,args.quarter))
    elif args.cmd=="coverage": coverage()

if __name__=="__main__":
    main()
