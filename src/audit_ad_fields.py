from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

df = pd.read_csv(DXSUM_PATH, low_memory=False)

# Keep only dementia rows
dementia = df[df["DIAGNOSIS"] == 3].copy()

fields = [
    "DXAD",
    "DXDDUE",
    "DXOTHDEM",
    "DXODES",
    "DXAPP",
    "DXAPROB",
    "DXAPOSS",
    "DXCONFID",
]

print("\n=== DEMENTIA ROWS BY PHASE ===")
print(dementia["PHASE"].value_counts(dropna=False))


for field in fields:
    if field not in dementia.columns:
        continue

    print(f"\n\n==============================")
    print(f"{field}")
    print(f"==============================")

    print("\nOverall:")
    print(
        dementia[field]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("\nBy phase:")

    table = pd.crosstab(
        dementia["PHASE"],
        dementia[field],
        dropna=False
    )

    print(table)


print("\nAD field audit complete.")