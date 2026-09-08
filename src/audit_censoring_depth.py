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

censored = df[df["OUTCOME"] == "right_censored"].copy()

bins = [-1, 0, 180, 365, 548, 730]
labels = [
    "0 days",
    "1-6 months",
    "6-12 months",
    "12-18 months",
    "18-24 months",
]

censored["FOLLOWUP_GROUP"] = pd.cut(
    censored["FOLLOWUP_DAYS"],
    bins=bins,
    labels=labels
)

print("\n=== RIGHT-CENSORED FOLLOW-UP DEPTH ===")
print(censored["FOLLOWUP_GROUP"].value_counts().sort_index())

print("\n=== BY BASELINE PHASE ===")
print(
    pd.crosstab(
        censored["BASELINE_PHASE"],
        censored["FOLLOWUP_GROUP"]
    )
)

print("\n=== EXACT ZERO FOLLOW-UP ===")
print((censored["FOLLOWUP_DAYS"] == 0).sum())

print("\nCensoring-depth audit complete.")