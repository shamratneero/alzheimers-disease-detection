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

print("\n=== OUTCOME COUNTS ===")
print(df["OUTCOME"].value_counts())

print("\n=== OUTCOME BY BASELINE PHASE ===")

table = pd.crosstab(
    df["BASELINE_PHASE"],
    df["OUTCOME"],
    margins=True
)

print(table)

print("\n=== PERCENTAGE WITHIN EACH PHASE ===")

percentage = pd.crosstab(
    df["BASELINE_PHASE"],
    df["OUTCOME"],
    normalize="index"
) * 100

print(percentage.round(1))

print("\n=== FOLLOW-UP DAYS BY OUTCOME ===")

print(
    df.groupby("OUTCOME")["FOLLOWUP_DAYS"]
    .describe()
    .round(1)
)

print("\nOutcome audit complete.")