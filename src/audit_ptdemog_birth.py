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

cohort["MCI_BASELINE_DATE"] = pd.to_datetime(
    cohort["MCI_BASELINE_DATE"],
    errors="coerce"
)

demo["VISDATE"] = pd.to_datetime(
    demo["VISDATE"],
    errors="coerce"
)


# PTDOB is stored like MM/YYYY
demo["PTDOB_PARSED"] = pd.to_datetime(
    demo["PTDOB"],
    format="%m/%Y",
    errors="coerce"
)

# PTDOBYY appears as YYYY-01-01
demo["PTDOBYY_PARSED"] = pd.to_datetime(
    demo["PTDOBYY"],
    errors="coerce"
)


# =========================================================
# KEEP OUR COHORT ONLY
# =========================================================

demo = demo[
    demo["RID"].isin(cohort["RID"])
].copy()


# =========================================================
# HELPER
# =========================================================

def unique_valid_dates(series):
    return sorted(
        set(
            series.dropna()
            .dt.strftime("%Y-%m-%d")
            .tolist()
        )
    )


# =========================================================
# CHECK CONSISTENCY
# =========================================================

ptdob_conflicts = []
ptdobyy_conflicts = []
month_year_disagreement = []
records = []


for _, subject in cohort.iterrows():

    rid = subject["RID"]
    baseline_date = subject["MCI_BASELINE_DATE"]

    g = demo[
        demo["RID"] == rid
    ].copy()

    ptdob_values = unique_valid_dates(
        g["PTDOB_PARSED"]
    )

    ptdobyy_values = unique_valid_dates(
        g["PTDOBYY_PARSED"]
    )

    if len(ptdob_values) > 1:
        ptdob_conflicts.append(
            {
                "RID": rid,
                "PTID": subject["PTID"],
                "PTDOB_VALUES": ptdob_values,
                "N_ROWS": len(g),
            }
        )

    if len(ptdobyy_values) > 1:
        ptdobyy_conflicts.append(
            {
                "RID": rid,
                "PTID": subject["PTID"],
                "PTDOBYY_VALUES": ptdobyy_values,
                "N_ROWS": len(g),
            }
        )


    # =====================================================
    # PICK A BIRTH DATE FOR AUDIT ONLY
    # =====================================================

    # Prefer PTDOB because it gives month + year.
    valid_dob = g[
        g["PTDOB_PARSED"].notna()
    ].copy()

    if not valid_dob.empty:

        selected_dob = (
            valid_dob
            .sort_values("VISDATE")
            .iloc[0]["PTDOB_PARSED"]
        )

        dob_source = "PTDOB"

    else:

        valid_dobyy = g[
            g["PTDOBYY_PARSED"].notna()
        ].copy()

        if not valid_dobyy.empty:

            selected_dob = (
                valid_dobyy
                .sort_values("VISDATE")
                .iloc[0]["PTDOBYY_PARSED"]
            )

            dob_source = "PTDOBYY"

        else:

            selected_dob = pd.NaT
            dob_source = None


    # =====================================================
    # CHECK PTDOB YEAR VS PTDOBYY YEAR
    # =====================================================

    both = g[
        g["PTDOB_PARSED"].notna()
        & g["PTDOBYY_PARSED"].notna()
    ].copy()

    if not both.empty:

        disagreement = both[
            both["PTDOB_PARSED"].dt.year
            != both["PTDOBYY_PARSED"].dt.year
        ]

        if not disagreement.empty:

            month_year_disagreement.append(
                {
                    "RID": rid,
                    "PTID": subject["PTID"],
                    "N_DISAGREE_ROWS": len(disagreement),
                }
            )


    # =====================================================
    # COMPUTE APPROXIMATE BASELINE AGE
    # =====================================================

    if pd.notna(selected_dob):

        age_years = (
            baseline_date - selected_dob
        ).days / 365.2425

    else:

        age_years = None


    records.append(
        {
            "RID": rid,
            "PTID": subject["PTID"],
            "DOB_SOURCE": dob_source,
            "SELECTED_DOB": selected_dob,
            "BASELINE_AGE_YEARS": age_years,
        }
    )


audit = pd.DataFrame(records)

ptdob_conflicts = pd.DataFrame(
    ptdob_conflicts
)

ptdobyy_conflicts = pd.DataFrame(
    ptdobyy_conflicts
)

month_year_disagreement = pd.DataFrame(
    month_year_disagreement
)


# =========================================================
# PRINT RESULTS
# =========================================================

print("\n=== PTDOB CONFLICTS ===")
print(
    "Subjects with >1 valid PTDOB value:",
    len(ptdob_conflicts)
)

if not ptdob_conflicts.empty:
    print(
        ptdob_conflicts.head(30)
        .to_string(index=False)
    )


print("\n=== PTDOBYY CONFLICTS ===")
print(
    "Subjects with >1 valid PTDOBYY value:",
    len(ptdobyy_conflicts)
)

if not ptdobyy_conflicts.empty:
    print(
        ptdobyy_conflicts.head(30)
        .to_string(index=False)
    )


print("\n=== PTDOB YEAR VS PTDOBYY YEAR DISAGREEMENTS ===")
print(
    "Subjects:",
    len(month_year_disagreement)
)

if not month_year_disagreement.empty:
    print(
        month_year_disagreement.head(30)
        .to_string(index=False)
    )


print("\n=== DOB SOURCE COVERAGE ===")
print(
    audit["DOB_SOURCE"]
    .value_counts(dropna=False)
)


print("\n=== MISSING DOB ===")
print(
    audit["SELECTED_DOB"]
    .isna()
    .value_counts()
)


print("\n=== APPROXIMATE BASELINE AGE DISTRIBUTION ===")
print(
    audit["BASELINE_AGE_YEARS"]
    .dropna()
    .describe()
)


print("\n=== POSSIBLE AGE OUTLIERS ===")

outliers = audit[
    audit["BASELINE_AGE_YEARS"].notna()
    & (
        (audit["BASELINE_AGE_YEARS"] < 40)
        | (audit["BASELINE_AGE_YEARS"] > 110)
    )
]

print(
    "Subjects:",
    len(outliers)
)

if not outliers.empty:

    print(
        outliers[
            [
                "RID",
                "PTID",
                "SELECTED_DOB",
                "BASELINE_AGE_YEARS",
            ]
        ]
        .to_string(index=False)
    )


# =========================================================
# ASSERTIONS
# =========================================================

assert len(audit) == 1744
assert audit["RID"].is_unique


print("\nPTDEMOG birth-date audit complete.")