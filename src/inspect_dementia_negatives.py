from pathlib import Path
import pandas as pd


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

COHORT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mci24_final_cohort.csv"
)


# =========================================================
# LOAD DATA
# =========================================================

dx = pd.read_csv(
    DXSUM_PATH,
    low_memory=False
)

cohort = pd.read_csv(
    COHORT_PATH,
    low_memory=False
)


# =========================================================
# PARSE DATES
# =========================================================

dx["EXAMDATE"] = pd.to_datetime(
    dx["EXAMDATE"],
    errors="coerce"
)

cohort["MCI_BASELINE_DATE"] = pd.to_datetime(
    cohort["MCI_BASELINE_DATE"],
    errors="coerce"
)

cohort["HORIZON_DATE"] = pd.to_datetime(
    cohort["HORIZON_DATE"],
    errors="coerce"
)


# =========================================================
# SUBJECTS TO INSPECT
# =========================================================

target_rids = [2398, 4637]


for rid in target_rids:

    row = cohort[
        cohort["RID"] == rid
    ].iloc[0]

    baseline_date = row["MCI_BASELINE_DATE"]
    horizon_date = row["HORIZON_DATE"]

    print("\n" + "=" * 80)
    print(f"RID: {rid}")
    print(f"PTID: {row['PTID']}")
    print(f"Baseline MCI date: {baseline_date.date()}")
    print(f"24-month horizon: {horizon_date.date()}")
    print(f"Current outcome: {row['OUTCOME']}")
    print("=" * 80)

    subject = dx[
        (dx["RID"] == rid)
        & dx["EXAMDATE"].notna()
        & (dx["EXAMDATE"] >= baseline_date)
        & (dx["EXAMDATE"] <= horizon_date)
    ].copy()

    subject = subject.sort_values("EXAMDATE")

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
            "DXODES",
            "DXAPP",
            "DXAPROB",
            "DXAPOSS",
            "DXCONFID",
        ]
        if c in subject.columns
    ]

    print(subject[cols].to_string(index=False))


print("\nInspection complete.")