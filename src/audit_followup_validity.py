from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

COHORT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mci24_final_cohort.csv"
)


dx = pd.read_csv(
    DXSUM_PATH,
    low_memory=False
)

cohort = pd.read_csv(
    COHORT_PATH,
    low_memory=False
)


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
# Define a usable diagnosis visit
# =========================================================

def usable_diagnosis(row):
    """
    A visit counts as diagnostic follow-up only if:
    - EXAMDATE is valid
    - DIAGNOSIS is one of the usable clinical states:
      1 = CN
      2 = MCI
      3 = dementia
    """

    return (
        pd.notna(row["EXAMDATE"])
        and row["DIAGNOSIS"] in [1, 2, 3]
    )


dx["USABLE_DIAG_VISIT"] = dx.apply(
    usable_diagnosis,
    axis=1
)


# =========================================================
# Audit primary AD non-converters
# =========================================================

negatives = cohort[
    cohort["FINAL_OUTCOME"] == "ad_non_converter"
].copy()

records = []


for _, subject in negatives.iterrows():

    rid = subject["RID"]
    baseline_date = subject["MCI_BASELINE_DATE"]
    horizon_date = subject["HORIZON_DATE"]

    subject_dx = dx[
        (dx["RID"] == rid)
        & (dx["EXAMDATE"] > baseline_date)
    ].copy()

    # Latest dated DXSUM visit of any kind
    any_dated = subject_dx[
        subject_dx["EXAMDATE"].notna()
    ]

    if len(any_dated) > 0:
        last_any_date = any_dated["EXAMDATE"].max()
    else:
        last_any_date = pd.NaT


    # Latest usable diagnostic visit
    usable = subject_dx[
        subject_dx["USABLE_DIAG_VISIT"]
    ]

    if len(usable) > 0:
        last_usable_diag_date = usable["EXAMDATE"].max()
    else:
        last_usable_diag_date = pd.NaT


    reaches_horizon_any = (
        pd.notna(last_any_date)
        and last_any_date >= horizon_date
    )

    reaches_horizon_usable_diag = (
        pd.notna(last_usable_diag_date)
        and last_usable_diag_date >= horizon_date
    )


    records.append(
        {
            "RID": rid,
            "PTID": subject["PTID"],
            "MCI_BASELINE_DATE": baseline_date,
            "HORIZON_DATE": horizon_date,
            "LAST_ANY_DXSUM_DATE": last_any_date,
            "LAST_USABLE_DIAG_DATE": last_usable_diag_date,
            "REACHES_HORIZON_ANY_DXSUM":
                reaches_horizon_any,
            "REACHES_HORIZON_USABLE_DIAG":
                reaches_horizon_usable_diag,
        }
    )


audit = pd.DataFrame(records)


print("\n=== AD NON-CONVERTERS ===")
print(f"Subjects: {len(audit):,}")


print("\n=== REACH 24 MONTHS USING ANY DXSUM ROW ===")
print(
    audit["REACHES_HORIZON_ANY_DXSUM"]
    .value_counts(dropna=False)
)


print("\n=== REACH 24 MONTHS USING USABLE DIAGNOSIS VISITS ===")
print(
    audit["REACHES_HORIZON_USABLE_DIAG"]
    .value_counts(dropna=False)
)


# Subjects currently negative only because a non-diagnostic
# dated row extended their follow-up beyond 24 months
problem = audit[
    audit["REACHES_HORIZON_ANY_DXSUM"]
    & (~audit["REACHES_HORIZON_USABLE_DIAG"])
].copy()


print("\n=== POTENTIAL FOLLOW-UP MISCLASSIFICATION ===")
print(f"Subjects: {len(problem):,}")

if not problem.empty:

    print(
        problem[
            [
                "RID",
                "PTID",
                "HORIZON_DATE",
                "LAST_ANY_DXSUM_DATE",
                "LAST_USABLE_DIAG_DATE",
            ]
        ]
        .sort_values("RID")
        .to_string(index=False)
    )


assert len(audit) == 827
assert audit["RID"].is_unique

print("\nFollow-up validity audit complete.")