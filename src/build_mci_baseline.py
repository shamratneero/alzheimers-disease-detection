from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"
OUT_PATH = ROOT / "data" / "interim" / "mci_baseline_candidates.csv"


df = pd.read_csv(DXSUM_PATH, low_memory=False)

# Parse dates
df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")

# Keep only rows with usable dates
df = df[df["EXAMDATE"].notna()].copy()

# Keep only rows explicitly diagnosed as MCI
mci = df[df["DIAGNOSIS"] == 2].copy()

# Sort chronologically within each subject
mci = mci.sort_values(["RID", "EXAMDATE"])

# Select the first documented MCI visit for each subject
baseline = (
    mci.groupby("RID", as_index=False)
    .first()
)

# Keep useful columns only
cols = [
    c for c in [
        "RID",
        "PTID",
        "EXAMDATE",
        "VISCODE",
        "VISCODE2",
        "PHASE",
        "DIAGNOSIS",
    ]
    if c in baseline.columns
]

baseline = baseline[cols]

print("\n=== BASELINE MCI CANDIDATES ===")
print(f"Subjects with at least one dated MCI visit: {len(baseline):,}")

print("\nPhase of first MCI visit:")
print(baseline["PHASE"].value_counts(dropna=False))

print("\nFirst few:")
print(baseline.head(20).to_string(index=False))

baseline.to_csv(OUT_PATH, index=False)

print(f"\nSaved to: {OUT_PATH}")