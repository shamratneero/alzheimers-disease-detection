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
# KEEP ONLY PRIMARY NEGATIVES
# =========================================================

negatives = cohort[
    cohort["PRIMARY_LABEL"] == 0
].copy()

print("\n=== PRIMARY NEGATIVE SUBJECTS ===")
print(f"Subjects: {len(negatives):,}")


# =========================================================
# AUDIT DIAGNOSIS TRAJECTORY WITHIN 24 MONTHS
# =========================================================

records = []

for _, subject in negatives.iterrows():

    rid = subject["RID"]
    baseline_date = subject["MCI_BASELINE_DATE"]
    horizon_date = subject["HORIZON_DATE"]

    # All valid diagnosis visits from baseline through 24 months
    window = dx[
        (dx["RID"] == rid)
        & dx["EXAMDATE"].notna()
        & (dx["EXAMDATE"] >= baseline_date)
        & (dx["EXAMDATE"] <= horizon_date)
    ].copy()

    window = window.sort_values("EXAMDATE")

    # Diagnosis codes:
    # 1 = CN
    # 2 = MCI
    # 3 = dementia
    has_cn = bool(
        (window["DIAGNOSIS"] == 1).any()
    )

    has_mci = bool(
        (window["DIAGNOSIS"] == 2).any()
    )

    has_dementia = bool(
        (window["DIAGNOSIS"] == 3).any()
    )

    # Count how many visits of each type occurred
    n_cn = int(
        (window["DIAGNOSIS"] == 1).sum()
    )

    n_mci = int(
        (window["DIAGNOSIS"] == 2).sum()
    )

    n_dementia = int(
        (window["DIAGNOSIS"] == 3).sum()
    )

    # Last diagnosis seen within the 24-month window
    if len(window) > 0:

        last_row = window.iloc[-1]

        last_diag = last_row["DIAGNOSIS"]
        last_diag_date = last_row["EXAMDATE"]

    else:

        last_diag = pd.NA
        last_diag_date = pd.NaT


    records.append(
        {
            "RID": rid,
            "PTID": subject["PTID"],

            "HAS_CN_WITHIN_24M": has_cn,
            "HAS_MCI_WITHIN_24M": has_mci,
            "HAS_DEMENTIA_WITHIN_24M": has_dementia,

            "N_CN_VISITS_24M": n_cn,
            "N_MCI_VISITS_24M": n_mci,
            "N_DEMENTIA_VISITS_24M": n_dementia,

            "LAST_DIAGNOSIS_24M": last_diag,
            "LAST_DIAGNOSIS_DATE_24M": last_diag_date,
        }
    )


audit = pd.DataFrame(records)


# =========================================================
# SUMMARY
# =========================================================

print("\n=== ANY CN WITHIN 24 MONTHS ===")
print(
    audit["HAS_CN_WITHIN_24M"]
    .value_counts(dropna=False)
)

print("\n=== ANY MCI WITHIN 24 MONTHS ===")
print(
    audit["HAS_MCI_WITHIN_24M"]
    .value_counts(dropna=False)
)

print("\n=== ANY DEMENTIA WITHIN 24 MONTHS ===")
print(
    audit["HAS_DEMENTIA_WITHIN_24M"]
    .value_counts(dropna=False)
)


print("\n=== LAST DIAGNOSIS WITHIN 24 MONTHS ===")
print(
    audit["LAST_DIAGNOSIS_24M"]
    .value_counts(dropna=False)
    .sort_index()
)


# =========================================================
# IMPORTANT SUBGROUPS
# =========================================================

reverted_to_cn = audit[
    audit["HAS_CN_WITHIN_24M"]
].copy()

dementia_without_primary_ad = audit[
    audit["HAS_DEMENTIA_WITHIN_24M"]
].copy()


print("\n=== NEGATIVES WITH CN DURING 24 MONTHS ===")
print(f"Subjects: {len(reverted_to_cn):,}")


print("\n=== NEGATIVES WITH DEMENTIA DURING 24 MONTHS ===")
print(f"Subjects: {len(dementia_without_primary_ad):,}")


# Show the subjects with dementia because these are the ones
# we need to inspect carefully.
if not dementia_without_primary_ad.empty:

    print("\n=== DEMENTIA-NEGATIVE SUBJECT IDS ===")

    print(
        dementia_without_primary_ad[
            [
                "RID",
                "PTID",
                "N_DEMENTIA_VISITS_24M",
                "LAST_DIAGNOSIS_24M",
                "LAST_DIAGNOSIS_DATE_24M",
            ]
        ]
        .sort_values("RID")
        .to_string(index=False)
    )


# =========================================================
# CONSISTENCY CHECK
# =========================================================

assert len(audit) == 829
assert audit["RID"].is_unique


print("\nNegative-trajectory audit complete.")