
#!/usr/bin/env python3
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from fuel_data import load_observations, get_series, assert_same_units

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
    p = argparse.ArgumentParser(description="Compare final consumer prices for several fuels.")
    p.add_argument("--data", default=str(Path(__file__).parents[1] / "data" / "observations.csv"))
    p.add_argument("--fuels", nargs="+", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--frequency", choices=["yearly","monthly","weekly","daily"], required=True)
    p.add_argument("--interpolate", choices=["none","linear","ffill"], default="none")
    p.add_argument("--allow-partial", action="store_true")
    p.add_argument("--x-tick-every", type=int, default=1)
    p.add_argument("--y-tick-step", type=float, default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--output", default=None)
    args = p.parse_args()

    raw = load_observations(args.data)
    frames = {}
    for fuel in args.fuels:
        frames[fuel] = get_series(
            raw, fuel, args.start, args.end, args.frequency,
            interpolate=args.interpolate, allow_partial=args.allow_partial
        )
    unit = assert_same_units(frames)

    fig, ax = plt.subplots(figsize=(12, 6.5))
    for fuel, df in frames.items():
        ax.plot(df["date"], df["final_price"], linewidth=2.0, label=fuel, zorder=20)

    # Dotted grid explicitly above plot background; line series remain above the grid.
    ax.set_axisbelow(False)
    ax.grid(True, which="major", axis="both", linestyle=":", linewidth=0.8, zorder=10)
    set_ticks(ax, args.frequency, args.x_tick_every, args.y_tick_step)
    ax.set_ylabel("€/litre" if unit == "EUR/litre" else unit)
    ax.set_title(args.title or f"Italy — final fuel-price comparison ({args.frequency})")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=180, bbox_inches="tight")
        print(f"saved: {args.output}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
