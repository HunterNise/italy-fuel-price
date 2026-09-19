
#!/usr/bin/env python3
from pathlib import Path
import argparse
from fuel_data import load_observations, list_availability

p=argparse.ArgumentParser(description="Show what is actually available; useful before plotting.")
p.add_argument("--data", default=str(Path(__file__).parents[1]/"data"/"observations.csv"))
args=p.parse_args()
df=load_observations(args.data)
print(list_availability(df).to_string(index=False))
print("\nPartial rows:")
cols=["date","fuel","frequency","final_price","coverage_days","expected_days","source_note"]
print(df[df["is_partial"].fillna(False).astype(bool)][cols].to_string(index=False))
