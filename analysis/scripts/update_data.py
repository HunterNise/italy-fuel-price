
#!/usr/bin/env python3
"""
Update helper.

What it can do:
1) Fetch MIMIT's public national-average page and append the newest petrol/diesel
   ordinary-road self-service values to data/observations.csv.
2) Download the current MIMIT station-level 08:00 snapshot.
3) Import an official MASE monthly or weekly CSV export downloaded manually from
   the MASE open-data portal.

No interpolation is performed here.
"""
from __future__ import annotations
from pathlib import Path
import argparse, re, unicodedata
import pandas as pd
import numpy as np
import requests

ROOT = Path(__file__).parents[1]
OBS = ROOT / "data" / "observations.csv"
EXCISE = ROOT / "data" / "reference" / "excise_schedule.csv"
VAT = ROOT / "data" / "reference" / "vat_schedule.csv"

MIMIT_NATIONAL = "https://www.mimit.gov.it/it/prezzi-carburanti-media-nazionale"
MIMIT_STATION = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
MASE_PORTAL = "https://sisen.mase.gov.it/dgsaie/open-data"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def load_ref():
    ex = pd.read_csv(EXCISE, parse_dates=["effective_from"])
    vat = pd.read_csv(VAT, parse_dates=["effective_from","effective_to"])
    return ex, vat

def rate_for_day(fuel, day, ex):
    z = ex[(ex["fuel"] == fuel) & (ex["effective_from"] <= day)].sort_values("effective_from")
    return float(z.iloc[-1]["excise_eur_per_litre"])

def vat_for_day(day, vat):
    z = vat[vat["effective_from"] <= day].copy()
    z = z[(z["effective_to"].isna()) | (z["effective_to"] >= day)]
    return float(z.iloc[-1]["vat_rate"])

def add_components(final, fuel, day, ex, vat):
    e = rate_for_day(fuel, day, ex)
    r = vat_for_day(day, vat)
    v = final * r/(1+r)
    n = final - e - v
    return n,e,v

def append_rows(rows):
    obs = pd.read_csv(OBS)
    new = pd.DataFrame(rows)
    both = pd.concat([obs,new], ignore_index=True)
    # Deduplicate exact logical series keys, keeping newest import.
    keys = ["date","frequency","fuel","scope","network","service_mode"]
    both = both.drop_duplicates(keys, keep="last").sort_values(["fuel","frequency","date"])
    both.to_csv(OBS, index=False)
    print(f"updated {OBS}: {len(new)} row(s) added/replaced")

def fetch_mimit_national():
    html = requests.get(MIMIT_NATIONAL, timeout=30).text
    m = re.search(r"Aggiornamento\s+(\d{2})-(\d{2})-(\d{4})", html, flags=re.I)
    if not m:
        raise RuntimeError("Could not find MIMIT update date.")
    dd,mm,yyyy = m.groups()
    day = pd.Timestamp(f"{yyyy}-{mm}-{dd}")

    tables = pd.read_html(html, decimal=".", thousands=None)
    target = None
    for t in tables:
        cols = [norm(c) for c in t.columns]
        if "tipologia" in cols and "oggi" in cols:
            target = t.copy()
            target.columns = cols
            break
    if target is None:
        raise RuntimeError("Could not find national road-price table.")

    ex, vat = load_ref()
    rows=[]
    mapping={"benzina":"petrol","gasolio":"diesel"}
    for _, r in target.iterrows():
        typ = norm(r["tipologia"])
        if typ not in mapping: continue
        fuel = mapping[typ]
        final = float(r["oggi"])
        net,e,v = add_components(final, fuel, day, ex, vat)
        rows.append({
            "date":day.strftime("%Y-%m-%d"),
            "period_start":day.strftime("%Y-%m-%d"),
            "period_end":day.strftime("%Y-%m-%d"),
            "frequency":"daily","fuel":fuel,"scope":"Italy national",
            "network":"ordinary road network","service_mode":"self-service","unit":"EUR/litre",
            "final_price":final,"net_price":net,"excise":e,"vat":v,"total_taxes":e+v,
            "final_price_status":"observed",
            "components_status":"derived from final price + statutory tax schedule",
            "is_partial":False,"is_interpolated":False,
            "coverage_days":1,"expected_days":1,
            "source_name":"MIMIT national daily self-service average",
            "source_url":MIMIT_NATIONAL,
            "source_note":"Fetched automatically from MIMIT national-average page."
        })
    append_rows(rows)

def download_station_snapshot(dest):
    r = requests.get(MIMIT_STATION, timeout=60)
    r.raise_for_status()
    Path(dest).write_bytes(r.content)
    print(f"saved raw MIMIT station snapshot: {dest}")

def read_mase_csv(path):
    # MASE Italian Excel-CSV uses ; delimiter and comma decimals.
    # Fall back to ordinary CSV if needed.
    try:
        df = pd.read_csv(path, sep=";", decimal=",")
        if len(df.columns) == 1:
            raise ValueError
    except Exception:
        df = pd.read_csv(path)
    df.columns = [norm(c) for c in df.columns]
    return df

MONTHS_IT = {
    "gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,
    "luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12
}

def pick_col(cols, choices):
    for c in choices:
        if c in cols: return c
    return None

def import_mase(path, fuel, frequency):
    df = read_mase_csv(path)
    cols=set(df.columns)
    price_col=pick_col(cols, ["prezzo","price","prezzo_finale"])
    net_col=pick_col(cols, ["netto","prezzo_industriale","industrial_price"])
    exc_col=pick_col(cols, ["accisa","excise"])
    vat_col=pick_col(cols, ["iva","vat"])
    if not price_col:
        raise RuntimeError(f"Cannot identify price column. Columns found: {list(df.columns)}")

    if frequency == "monthly":
        year_col=pick_col(cols, ["anno","year"])
        month_col=pick_col(cols, ["mese","month"])
        date_col=pick_col(cols, ["data","date"])
        if date_col:
            dates=pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        elif year_col and month_col:
            mm=df[month_col].map(lambda x: MONTHS_IT.get(norm(x), x))
            dates=pd.to_datetime(dict(year=pd.to_numeric(df[year_col]), month=pd.to_numeric(mm), day=1), errors="coerce")
        else:
            raise RuntimeError(f"Cannot identify monthly date fields. Columns: {list(df.columns)}")
    else:
        date_col=pick_col(cols, ["data","date","rilevazione"])
        if not date_col:
            raise RuntimeError(f"Cannot identify weekly date column. Columns: {list(df.columns)}")
        dates=pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")

    def num(c):
        if not c: return pd.Series(np.nan,index=df.index)
        return pd.to_numeric(df[c], errors="coerce")

    price=num(price_col); net=num(net_col); exc=num(exc_col); vv=num(vat_col)

    # MASE exports are generally €/1,000 L for petrol/diesel.
    # Detect scale conservatively.
    scale = 1000.0 if price.dropna().median() > 20 else 1.0
    price,net,exc,vv = [s/scale for s in [price,net,exc,vv]]

    rows=[]
    for i, day in dates.items():
        if pd.isna(day): continue
        rows.append({
            "date":day.strftime("%Y-%m-%d"),
            "period_start":day.strftime("%Y-%m-%d"),
            "period_end":(day + (pd.offsets.MonthEnd(0) if frequency=="monthly" else pd.Timedelta(days=6))).strftime("%Y-%m-%d"),
            "frequency":frequency,"fuel":fuel,"scope":"Italy national",
            "network":"national statistical series","service_mode":"self-service","unit":"EUR/litre",
            "final_price":price.loc[i],"net_price":net.loc[i],"excise":exc.loc[i],"vat":vv.loc[i],
            "total_taxes":(exc.loc[i]+vv.loc[i]) if pd.notna(exc.loc[i]) and pd.notna(vv.loc[i]) else np.nan,
            "final_price_status":"official MASE import",
            "components_status":"official MASE import" if all(pd.notna([net.loc[i],exc.loc[i],vv.loc[i]])) else "partly missing in import",
            "is_partial":False,"is_interpolated":False,
            "coverage_days":1 if frequency=="weekly" else day.days_in_month,
            "expected_days":7 if frequency=="weekly" else day.days_in_month,
            "source_name":"MASE official CSV import","source_url":MASE_PORTAL,
            "source_note":f"Imported from {Path(path).name}; scale divisor={scale:g}."
        })
    append_rows(rows)

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mimit-national", help="Append latest MIMIT national petrol/diesel averages.")

    d=sub.add_parser("mimit-station", help="Download current station-level 08:00 CSV.")
    d.add_argument("--dest", default=str(ROOT/"data"/"raw"/"mimit_prezzo_alle_8.csv"))

    m=sub.add_parser("import-mase", help="Import a MASE CSV export downloaded from the official portal.")
    m.add_argument("path")
    m.add_argument("--fuel", choices=["petrol","diesel"], required=True)
    m.add_argument("--frequency", choices=["monthly","weekly"], required=True)

    args=p.parse_args()
    if args.cmd=="mimit-national":
        fetch_mimit_national()
    elif args.cmd=="mimit-station":
        download_station_snapshot(args.dest)
    elif args.cmd=="import-mase":
        import_mase(args.path,args.fuel,args.frequency)

if __name__=="__main__":
    main()
