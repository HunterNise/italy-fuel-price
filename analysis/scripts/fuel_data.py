
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import warnings

FREQ_ORDER = {"daily": 0, "weekly": 1, "monthly": 2, "yearly": 3}

def load_observations(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for c in ["date", "period_start", "period_end"]:
        if c in df:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in ["final_price", "net_price", "excise", "vat", "total_taxes"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def list_availability(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby(["fuel","frequency"], dropna=False)
          .agg(start=("date","min"), end=("date","max"), rows=("date","size"),
               missing_final=("final_price", lambda s: int(s.isna().sum())),
               partial=("is_partial", lambda s: int(pd.Series(s).fillna(False).astype(bool).sum())))
          .reset_index()
    )
    return g

def _full_period_expected(freq: str, idx: pd.DatetimeIndex) -> pd.Series:
    if freq == "monthly":
        return pd.Series(idx.days_in_month, index=idx)
    if freq == "weekly":
        return pd.Series(7, index=idx)
    if freq == "daily":
        return pd.Series(1, index=idx)
    return pd.Series(np.nan, index=idx)

def _aggregate_exact(df: pd.DataFrame, target: str, allow_partial: bool) -> pd.DataFrame:
    """Aggregate a finer series. Never upsamples here."""
    src = df["frequency"].iloc[0]
    if FREQ_ORDER[src] > FREQ_ORDER[target]:
        raise ValueError(f"Cannot aggregate {src} to finer {target} data.")

    x = df.copy().set_index("date").sort_index()
    rule = {"weekly":"W-MON", "monthly":"MS", "yearly":"YS"}[target]

    # Day weighting is most appropriate for monthly/annual price averages.
    if src == "monthly":
        weights = x["coverage_days"].fillna(x.index.days_in_month).astype(float)
    else:
        weights = x["coverage_days"].fillna(1).astype(float)

    def wavg(s, w):
        mask = s.notna() & w.notna()
        if not mask.any():
            return np.nan
        return np.average(s[mask], weights=w[mask])

    rows = []
    for period, grp in x.groupby(pd.Grouper(freq=rule)):
        if grp.empty:
            continue
        wg = weights.loc[grp.index]
        coverage = float(grp["coverage_days"].fillna(1).sum())
        if target == "weekly":
            expected = 7
        elif target == "monthly":
            expected = int(period.days_in_month)
        else:
            expected = 366 if period.is_leap_year else 365

        complete = coverage >= expected
        vals = {}
        for c in ["final_price","net_price","excise","vat","total_taxes"]:
            vals[c] = wavg(grp[c], wg) if (complete or allow_partial) else np.nan

        rows.append({
            "date": period, "frequency": target, "fuel": grp["fuel"].iloc[0],
            "scope": grp["scope"].iloc[0], "network": grp["network"].iloc[0],
            "service_mode": grp["service_mode"].iloc[0], "unit": grp["unit"].iloc[0],
            **vals,
            "is_partial": not complete,
            "is_interpolated": False,
            "coverage_days": coverage,
            "expected_days": expected,
            "source_name": f"Aggregated from package {src} observations",
            "source_url": "",
            "source_note": f"{target} value aggregated from {src}; allow_partial={allow_partial}.",
        })
    return pd.DataFrame(rows)

def _upsample_with_interpolation(df: pd.DataFrame, target: str, method: str) -> pd.DataFrame:
    """Explicitly upsample. Used only when user asks for interpolation."""
    src = df["frequency"].iloc[0]
    if FREQ_ORDER[src] <= FREQ_ORDER[target]:
        raise ValueError("Upsampling requested but source is not coarser than target.")
    x = df.copy().set_index("date").sort_index()
    rule = {"daily":"D", "weekly":"W-MON", "monthly":"MS"}[target]
    idx = pd.date_range(x.index.min(), x.index.max(), freq=rule)
    y = x.reindex(x.index.union(idx)).sort_index()
    cols = ["final_price","net_price","excise","vat","total_taxes"]
    if method == "linear":
        y[cols] = y[cols].interpolate(method="time")
    elif method == "ffill":
        y[cols] = y[cols].ffill()
    else:
        raise ValueError("Interpolation must be 'linear' or 'ffill'.")
    y = y.reindex(idx)
    meta = x.iloc[0]
    out = pd.DataFrame(index=idx)
    for c in cols:
        out[c] = y[c]
    out["date"] = idx
    out["frequency"] = target
    out["fuel"] = meta["fuel"]
    out["scope"] = meta["scope"]
    out["network"] = meta["network"]
    out["service_mode"] = meta["service_mode"]
    out["unit"] = meta["unit"]
    out["is_partial"] = False
    out["is_interpolated"] = True
    out["coverage_days"] = 0
    out["expected_days"] = 1
    out["source_name"] = f"INTERPOLATED from {src}"
    out["source_url"] = ""
    out["source_note"] = f"Explicit user-requested {method} interpolation from {src} to {target}."
    return out.reset_index(drop=True)

def get_series(
    df: pd.DataFrame,
    fuel: str,
    start: str,
    end: str,
    frequency: str,
    interpolate: str = "none",
    allow_partial: bool = False,
) -> pd.DataFrame:
    fuel = fuel.lower()
    frequency = frequency.lower()
    sub = df[df["fuel"].str.lower().eq(fuel)].copy()
    if sub.empty:
        raise ValueError(f"No data for fuel={fuel!r}. Available: {sorted(df['fuel'].dropna().unique())}")

    exact = sub[sub["frequency"].eq(frequency)].copy()
    if not exact.empty:
        chosen = exact
    else:
        # Prefer the finest embedded source that can be aggregated to target.
        candidates = []
        for sf in sub["frequency"].dropna().unique():
            if sf in FREQ_ORDER and FREQ_ORDER[sf] < FREQ_ORDER[frequency]:
                candidates.append(sf)
        if candidates:
            sf = sorted(candidates, key=lambda x: FREQ_ORDER[x])[0]
            chosen = _aggregate_exact(sub[sub["frequency"].eq(sf)].copy(), frequency, allow_partial)
        else:
            coarser = [sf for sf in sub["frequency"].dropna().unique()
                       if sf in FREQ_ORDER and FREQ_ORDER[sf] > FREQ_ORDER[frequency]]
            if not coarser:
                raise ValueError(f"No source data can produce {frequency} for {fuel}.")
            if interpolate == "none":
                raise ValueError(
                    f"{frequency} data are unavailable for {fuel}. "
                    f"Available embedded frequencies: {sorted(sub['frequency'].unique())}. "
                    "No interpolation was performed. Use --interpolate linear or --interpolate ffill explicitly."
                )
            sf = sorted(coarser, key=lambda x: FREQ_ORDER[x])[0]
            chosen = _upsample_with_interpolation(
                sub[sub["frequency"].eq(sf)].copy(), frequency, interpolate
            )

    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    chosen = chosen[(chosen["date"] >= start_ts) & (chosen["date"] <= end_ts)].copy()
    chosen = chosen.sort_values("date")
    if chosen.empty:
        raise ValueError(f"No {frequency} {fuel} data in {start}..{end}.")

    if not allow_partial and "is_partial" in chosen:
        # Keep the rows visible but values remain what the source contains; warn rather than delete.
        n = int(chosen["is_partial"].fillna(False).astype(bool).sum())
        if n:
            warnings.warn(f"{n} partial period(s) are present and clearly flagged.")
    return chosen

def assert_same_units(frames: dict[str, pd.DataFrame]) -> str:
    units = set()
    for f, df in frames.items():
        units.update(df["unit"].dropna().unique())
    if len(units) > 1:
        raise ValueError(f"Cannot directly compare mixed units: {sorted(units)}")
    return next(iter(units)) if units else ""
