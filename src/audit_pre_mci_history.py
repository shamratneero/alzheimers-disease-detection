from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"
BASELINE_PATH = ROOT / "data" / "interim" / "mci_baseline_candidates.csv"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
dx = pd.read_csv(DXSUM_PATH, low_memory=False)
baseline = pd.read_csv(BASELINE_PATH, low_memory=False)

dx["EXAMDATE"] = pd.to_datetime(dx["EXAMDATE"], errors="coerce")
baseline["EXAMDATE"] = pd.to_datetime(baseline["EXAMDATE"], errors="coerce")


# ---------------------------------------------------------
# Merge baseline date onto all diagnosis rows
# ---------------------------------------------------------
baseline_dates = baseline[["RID", "EXAMDATE"]].rename(
    columns={"EXAMDATE": "MCI_BASELINE_DATE"}
)

merged = dx.merge(
    baseline_dates,
    on="RID",
    how="inner"
)


# ---------------------------------------------------------
# Keep only rows before first MCI baseline
# ---------------------------------------------------------
pre = merged[
    merged["EXAMDATE"].notna()
    & (merged["EXAMDATE"] < merged["MCI_BASELINE_DATE"])
].copy()


print("\n=== PRE-MCI HISTORY AUDIT ===")
print(f"Subjects with any dated history before first MCI: {pre['RID'].nunique():,}")


# ---------------------------------------------------------
# Diagnosis distribution before MCI
# ---------------------------------------------------------
print("\n=== PRE-MCI DIAGNOSIS DISTRIBUTION ===")
print(pre["DIAGNOSIS"].value_counts(dropna=False).sort_index())


# ---------------------------------------------------------
# Subjects with dementia before first MCI
# ---------------------------------------------------------
pre_dementia = pre[pre["DIAGNOSIS"] == 3].copy()

print("\n=== SUBJECTS WITH DEMENTIA BEFORE FIRST MCI ===")
print(f"Subjects: {pre_dementia['RID'].nunique():,}")
print(f"Rows: {len(pre_dementia):,}")


cols = [
    c for c in [
        "RID",
        "PTID",
        "EXAMDATE",
        "MCI_BASELINE_DATE",
        "VISCODE",
        "PHASE",
        "DIAGNOSIS",
        "DXAD",
        "DXDDUE",
        "DXOTHDEM",
    ]
    if c in pre_dementia.columns
]

if not pre_dementia.empty:
    print(
        pre_dementia[cols]
        .sort_values(["RID", "EXAMDATE"])
        .to_string(index=False)
    )


print("\nPre-MCI history audit complete.")