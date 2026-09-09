from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PTDEMOG_PATH = ROOT / "data" / "raw" / "PTDEMOG_06Sep2026.csv"

COHORT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mci24_final_cohort.csv"
)


# =========================================================
# LOAD
# =========================================================

demo = pd.read_csv(
    PTDEMOG_PATH,
    low_memory=False
)

cohort = pd.read_csv(
    COHORT_PATH,
    low_memory=False
)


# =========================================================
# PARSE DATES
# =========================================================

demo["VISDATE"] = pd.to_datetime(
    demo["VISDATE"],
    errors="coerce"
)

cohort["MCI_BASELINE_DATE"] = pd.to_datetime(
    cohort["MCI_BASELINE_DATE"],
    errors="coerce"
)


# =========================================================
# KEEP ONLY OUR COHORT SUBJECTS
# =========================================================

demo = demo[
    demo["RID"].isin(cohort["RID"])
].copy()


print("\n=== COHORT COVERAGE IN PTDEMOG ===")

print(
    "Cohort subjects:",
    cohort["RID"].nunique()
)

print(
    "Cohort subjects found in PTDEMOG:",
    demo["RID"].nunique()
)

missing_rids = sorted(
    set(cohort["RID"])
    - set(demo["RID"])
)

print(
    "Cohort subjects missing entirely from PTDEMOG:",
    len(missing_rids)
)

if missing_rids:
    print(missing_rids[:50])


# =========================================================
# REPEATED DEMOGRAPHIC VALUES
# =========================================================

def normalized_values(series):
    """
    Ignore NaN and ADNI special missing codes -4 and -1.
    Return unique remaining values.
    """
    return sorted(
        set(
            series[
                series.notna()
                & (~series.isin([-4, -1]))
            ].tolist()
        )
    )


sex_conflicts = []
education_conflicts = []


for rid, g in demo.groupby("RID"):

    sex_values = normalized_values(
        g["PTGENDER"]
    )

    education_values = normalized_values(
        g["PTEDUCAT"]
    )

    if len(sex_values) > 1:
        sex_conflicts.append(
            {
                "RID": rid,
                "VALUES": sex_values,
                "N_ROWS": len(g),
            }
        )

    if len(education_values) > 1:
        education_conflicts.append(
            {
                "RID": rid,
                "VALUES": education_values,
                "N_ROWS": len(g),
            }
        )


sex_conflicts = pd.DataFrame(
    sex_conflicts
)

education_conflicts = pd.DataFrame(
    education_conflicts
)


print("\n=== SEX CONFLICTS ACROSS PTDEMOG RECORDS ===")
print(
    "Subjects with >1 valid PTGENDER value:",
    len(sex_conflicts)
)

if not sex_conflicts.empty:
    print(
        sex_conflicts.head(30)
        .to_string(index=False)
    )


print("\n=== EDUCATION CONFLICTS ACROSS PTDEMOG RECORDS ===")
print(
    "Subjects with >1 valid PTEDUCAT value:",
    len(education_conflicts)
)

if not education_conflicts.empty:
    print(
        education_conflicts.head(30)
        .to_string(index=False)
    )


# =========================================================
# ALIGN PTDEMOG TO MCI BASELINE
# =========================================================

records = []


for _, subject in cohort.iterrows():

    rid = subject["RID"]
    baseline_date = subject["MCI_BASELINE_DATE"]

    g = demo[
        demo["RID"] == rid
    ].copy()

    if g.empty:

        records.append(
            {
                "RID": rid,
                "PTID": subject["PTID"],
                "N_PTDEMOG_ROWS": 0,
                "N_DATED_PTDEMOG_ROWS": 0,
                "SELECTED_VISDATE": pd.NaT,
                "DAYS_FROM_BASELINE": None,
                "SELECTED_BEFORE_OR_ON_BASELINE": False,
            }
        )

        continue


    dated = g[
        g["VISDATE"].notna()
    ].copy()

    if dated.empty:

        records.append(
            {
                "RID": rid,
                "PTID": subject["PTID"],
                "N_PTDEMOG_ROWS": len(g),
                "N_DATED_PTDEMOG_ROWS": 0,
                "SELECTED_VISDATE": pd.NaT,
                "DAYS_FROM_BASELINE": None,
                "SELECTED_BEFORE_OR_ON_BASELINE": False,
            }
        )

        continue


    # -----------------------------------------------------
    # Prefer a demographic record on or before baseline
    # -----------------------------------------------------

    prior = dated[
        dated["VISDATE"] <= baseline_date
    ].copy()

    if not prior.empty:

        selected = (
            prior
            .sort_values("VISDATE")
            .iloc[-1]
        )

    else:

        # If nothing exists before baseline,
        # use the earliest future demographic record
        selected = (
            dated
            .sort_values("VISDATE")
            .iloc[0]
        )


    days_from_baseline = (
        selected["VISDATE"]
        - baseline_date
    ).days


    records.append(
        {
            "RID": rid,
            "PTID": subject["PTID"],
            "N_PTDEMOG_ROWS": len(g),
            "N_DATED_PTDEMOG_ROWS": len(dated),
            "SELECTED_VISDATE": selected["VISDATE"],
            "DAYS_FROM_BASELINE": days_from_baseline,
            "SELECTED_BEFORE_OR_ON_BASELINE":
                selected["VISDATE"] <= baseline_date,
        }
    )


alignment = pd.DataFrame(
    records
)


# =========================================================
# SUMMARIES
# =========================================================

print("\n=== PTDEMOG ROW COUNTS WITHIN COHORT ===")

print(
    alignment["N_PTDEMOG_ROWS"]
    .describe()
)


print("\n=== SELECTED RECORD TIMING ===")

print(
    alignment[
        "SELECTED_BEFORE_OR_ON_BASELINE"
    ]
    .value_counts(
        dropna=False
    )
)


print("\n=== DAYS FROM MCI BASELINE ===")

print(
    alignment[
        "DAYS_FROM_BASELINE"
    ]
    .dropna()
    .describe()
)


print("\n=== ABSOLUTE DISTANCE FROM BASELINE ===")

abs_days = (
    alignment[
        "DAYS_FROM_BASELINE"
    ]
    .dropna()
    .abs()
)

print(
    abs_days.describe()
)


for threshold in [
    0,
    30,
    90,
    180,
    365,
    730,
]:

    count = (
        abs_days <= threshold
    ).sum()

    print(
        f"Within ±{threshold} days: "
        f"{count:,} / {len(alignment):,}"
    )


# =========================================================
# FUTURE-ONLY DEMOGRAPHIC RECORDS
# =========================================================

future_only = alignment[
    (
        alignment["SELECTED_VISDATE"].notna()
        & (~alignment["SELECTED_BEFORE_OR_ON_BASELINE"])
    )
].copy()


print("\n=== SUBJECTS REQUIRING POST-BASELINE PTDEMOG ===")

print(
    "Subjects:",
    len(future_only)
)

if not future_only.empty:

    print(
        future_only[
            [
                "RID",
                "PTID",
                "SELECTED_VISDATE",
                "DAYS_FROM_BASELINE",
                "N_PTDEMOG_ROWS",
            ]
        ]
        .sort_values(
            "DAYS_FROM_BASELINE",
            ascending=False
        )
        .head(50)
        .to_string(index=False)
    )


# =========================================================
# ASSERTIONS
# =========================================================

assert len(alignment) == 1744
assert alignment["RID"].is_unique


print(
    "\nPTDEMOG alignment audit complete."
)