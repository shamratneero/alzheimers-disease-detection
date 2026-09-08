from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

df = pd.read_csv(DXSUM_PATH, low_memory=False)
df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")


# ---------------------------------------------------------
# 1. DIAGNOSIS = 10
# ---------------------------------------------------------
print("\n=== DIAGNOSIS = 10 ===")

diag10 = df[df["DIAGNOSIS"] == 10]

cols = [
    c for c in [
        "RID",
        "PTID",
        "EXAMDATE",
        "VISCODE",
        "VISCODE2",
        "PHASE",
        "DIAGNOSIS",
        "DXAD",
        "DXDDUE",
        "DXOTHDEM",
    ]
    if c in df.columns
]

print(f"Rows: {len(diag10)}")
print(diag10[cols].to_string(index=False))


# ---------------------------------------------------------
# 2. Missing DIAGNOSIS
# ---------------------------------------------------------
print("\n=== MISSING DIAGNOSIS ===")

missing_diag = df[df["DIAGNOSIS"].isna()]

print(f"Rows: {len(missing_diag)}")
print(missing_diag[cols].to_string(index=False))


# ---------------------------------------------------------
# 3. Same RID + same date with conflicting diagnosis
# ---------------------------------------------------------
print("\n=== CONFLICTING SAME-DAY DIAGNOSES ===")

valid = df.dropna(subset=["RID", "EXAMDATE", "DIAGNOSIS"]).copy()

conflicting_keys = (
    valid.groupby(["RID", "EXAMDATE"])["DIAGNOSIS"]
    .nunique()
)

conflicting_keys = conflicting_keys[conflicting_keys > 1].index

conflicting = valid.set_index(["RID", "EXAMDATE"]).loc[
    conflicting_keys
].reset_index()

print(f"Rows involved: {len(conflicting)}")
print(conflicting[cols].sort_values(["RID", "EXAMDATE"]).to_string(index=False))


print("\nFocused diagnosis audit complete.")