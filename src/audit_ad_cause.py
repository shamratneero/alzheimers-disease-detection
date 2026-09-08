from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

df = pd.read_csv(DXSUM_PATH, low_memory=False)
df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")


# Keep only rows classified as dementia
dementia = df[df["DIAGNOSIS"] == 3].copy()

print("\n=== DEMENTIA ROWS ===")
print(f"Rows: {len(dementia):,}")
print(f"Unique subjects: {dementia['RID'].nunique():,}")


# ---------------------------------------------------------
# Phase distribution
# ---------------------------------------------------------
print("\n=== DEMENTIA BY PHASE ===")
print(dementia["PHASE"].value_counts(dropna=False))


# ---------------------------------------------------------
# AD-specific fields
# ---------------------------------------------------------
for col in ["DXAD", "DXDDUE", "DXOTHDEM"]:
    if col in dementia.columns:
        print(f"\n=== {col} AMONG DEMENTIA ROWS ===")
        print(dementia[col].value_counts(dropna=False).sort_index())


# ---------------------------------------------------------
# Show rows that may indicate non-AD dementia
# ---------------------------------------------------------
possible_non_ad = dementia[
    (
        (dementia["DXDDUE"].notna() & (dementia["DXDDUE"] != 1))
        |
        (dementia["DXOTHDEM"] == 1)
    )
]

cols = [
    c for c in [
        "RID",
        "PTID",
        "EXAMDATE",
        "VISCODE",
        "PHASE",
        "DIAGNOSIS",
        "DXAD",
        "DXDDUE",
        "DXOTHDEM",
    ]
    if c in df.columns
]

print("\n=== POSSIBLE NON-AD DEMENTIA ROWS ===")
print(f"Rows: {len(possible_non_ad):,}")

if not possible_non_ad.empty:
    print(
        possible_non_ad[cols]
        .sort_values(["RID", "EXAMDATE"])
        .to_string(index=False)
    )


print("\nAD-cause audit complete.")