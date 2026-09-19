
#!/usr/bin/env python3
from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

from fuel_data import load_observations, get_series

def set_ticks(ax, frequency, tick_every, y_tick_step):
    tick_every = max(1, tick_every)
    if frequency == "yearly":
        ax.xaxis.set_major_locator(mdates.YearLocator(base=tick_every))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    elif frequency == "monthly":
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=tick_every))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    elif frequency == "weekly":
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=tick_every))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=tick_every))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))

    if y_tick_step is not None:
        ax.yaxis.set_major_locator(mticker.MultipleLocator(y_tick_step))

def main():
    p = argparse.ArgumentParser(description="Plot price decomposition for one fuel.")
    p.add_argument("--data", default=str(Path(__file__).parents[1] / "data" / "observations.csv"))
    p.add_argument("--fuel", required=True, help="e.g. petrol or diesel")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--frequency", choices=["yearly","monthly","weekly","daily"], required=True)
    p.add_argument("--interpolate", choices=["none","linear","ffill"], default="none",
                   help="Default none. Needed only to upsample coarser data.")
    p.add_argument("--allow-partial", action="store_true")
    p.add_argument("--x-tick-every", type=int, default=1,
                   help="Show every N units of the selected frequency.")
    p.add_argument("--y-tick-step", type=float, default=None, help="Optional fixed y tick spacing.")
    p.add_argument("--title", default=None)
    p.add_argument("--output", default=None)
    p.add_argument("--show-points", action="store_true")
    args = p.parse_args()

    raw = load_observations(args.data)
    df = get_series(raw, args.fuel, args.start, args.end, args.frequency,
                    interpolate=args.interpolate, allow_partial=args.allow_partial)

    fig, ax = plt.subplots(figsize=(12, 6.5))
    x = df["date"]

    # Areas deliberately below the grid.
    ax.stackplot(
        x, df["net_price"], df["excise"], df["vat"],
        labels=["Net / industrial price", "Excise duty", "VAT"],
        zorder=1
    )
    ax.plot(x, df["final_price"], linewidth=2.1, label="Final consumer price", zorder=20)
    if args.show_points:
        ax.scatter(x, df["final_price"], s=15, zorder=21)

    # IMPORTANT: dotted tick grid is drawn above the filled areas.
    ax.set_axisbelow(False)
    ax.grid(True, which="major", axis="both", linestyle=":", linewidth=0.8, zorder=10)

    set_ticks(ax, args.frequency, args.x_tick_every, args.y_tick_step)
    ax.set_ylabel("€/litre")
    ax.set_title(args.title or f"Italy — {args.fuel} price decomposition ({args.frequency})")
    ax.legend(loc="upper left", ncol=2)
    fig.autofmt_xdate()

    # Mark explicitly partial/interpolated rows.
    partial = df[df.get("is_partial", False).fillna(False).astype(bool)] if "is_partial" in df else df.iloc[0:0]
    interp = df[df.get("is_interpolated", False).fillna(False).astype(bool)] if "is_interpolated" in df else df.iloc[0:0]
    if len(partial):
        ax.scatter(partial["date"], partial["final_price"], marker="s", s=35, zorder=22, label="Partial period")
    if len(interp):
        ax.scatter(interp["date"], interp["final_price"], marker="x", s=35, zorder=22, label="Interpolated")

    fig.tight_layout()
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=180, bbox_inches="tight")
        print(f"saved: {args.output}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
