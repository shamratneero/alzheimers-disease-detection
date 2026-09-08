from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

OUTCOME_PATH = (
    ROOT
    / "data"
    / "interim"
    / "mci24_outcomes_initial.csv"
)

df = pd.read_csv(OUTCOME_PATH)

converters = df[df["OUTCOME"] == "converter"].copy()

print("\n=== CONVERTER COUNT ===")
print(len(converters))

print("\n=== DAYS TO AD ===")
print(
    converters["DAYS_TO_AD"]
    .describe()
    .round(1)
)

bins = [0, 183, 365, 548, float("inf")]
labels = [
    "0-6 months",
    "6-12 months",
    "12-18 months",
    "18-24 months",
]

converters["CONVERSION_WINDOW"] = pd.cut(
    converters["DAYS_TO_AD"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

assert converters["CONVERSION_WINDOW"].notna().all()
assert len(converters) == converters["CONVERSION_WINDOW"].value_counts().sum()

print("\n=== CONVERSION WINDOWS ===")
print(
    converters["CONVERSION_WINDOW"]
    .value_counts()
    .sort_index()
)

print("\n=== CONVERSION WINDOW BY BASELINE PHASE ===")
print(
    pd.crosstab(
        converters["BASELINE_PHASE"],
        converters["CONVERSION_WINDOW"]
    )
)

print("\nConversion-timing audit complete.")