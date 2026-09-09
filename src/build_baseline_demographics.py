from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PTDEMOG_PATH = (
    ROOT
    / "data"
    / "raw"
    / "PTDEMOG_06Sep2026.csv"
)

COHORT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mci24_final_cohort.csv"
)

OUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "mci24_baseline_demographics.csv"
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

demo["PTDOBYY_PARSED"] = pd.to_datetime(
    demo["PTDOBYY"],
    errors="coerce"
)

cohort["MCI_BASELINE_DATE"] = pd.to_datetime(
    cohort["MCI_BASELINE_DATE"],
    errors="coerce"
)


# =========================================================
# KEEP COHORT SUBJECTS ONLY
# =========================================================

demo = demo[
    demo["RID"].isin(cohort["RID"])
].copy()


# =========================================================
# HELPERS
# =========================================================

def valid_value(series):
    """
    Remove missing values and ADNI special missing codes.
    """
    return series[
        series.notna()
        & (~series.isin([-4, -1]))
    ]


def get_static_value(g, column):
    """
    For static demographic variables such as sex or birth year.

    Prefer earliest valid value.
    """
    valid = g[
        g[column].notna()
        & (~g[column].isin([-4, -1]))
    ].copy()

    if valid.empty:
        return None

    valid = valid.sort_values(
        "VISDATE"
    )

    return valid.iloc[0][column]


def get_prebaseline_value(
    g,
    column,
    baseline_date
):
    """
    For variables such as education that should not use
    post-baseline information.

    Select the most recent valid value on or before baseline.
    """

    valid = g[
        g[column].notna()
        & (~g[column].isin([-4, -1]))
        & g["VISDATE"].notna()
        & (g["VISDATE"] <= baseline_date)
    ].copy()

    if valid.empty:
        return None, pd.NaT

    valid = valid.sort_values(
        "VISDATE"
    )

    selected = valid.iloc[-1]

    return (
        selected[column],
        selected["VISDATE"]
    )


# =========================================================
# BUILD SUBJECT-LEVEL DEMOGRAPHICS
# =========================================================

records = []


for _, subject in cohort.iterrows():

    rid = subject["RID"]
    ptid = subject["PTID"]
    baseline_date = subject["MCI_BASELINE_DATE"]

    g = demo[
        demo["RID"] == rid
    ].copy()


    # =====================================================
    # SEX
    # =====================================================

    sex_code = get_static_value(
        g,
        "PTGENDER"
    )


    # =====================================================
    # BIRTH YEAR
    # =====================================================

    birth_year_values = (
        g["PTDOBYY_PARSED"]
        .dropna()
        .dt.year
        .unique()
    )

    if len(birth_year_values) == 1:
        birth_year = int(
            birth_year_values[0]
        )

    elif len(birth_year_values) == 0:
        birth_year = None

    else:
        raise ValueError(
            f"Conflicting birth years for RID {rid}: "
            f"{birth_year_values}"
        )


    # =====================================================
    # APPROXIMATE BASELINE AGE
    # =====================================================

    if birth_year is not None:

        year_start = pd.Timestamp(
            year=baseline_date.year,
            month=1,
            day=1
        )

        next_year_start = pd.Timestamp(
            year=baseline_date.year + 1,
            month=1,
            day=1
        )

        fraction_of_year = (
            (baseline_date - year_start).days
            / (next_year_start - year_start).days
        )

        baseline_age = (
            baseline_date.year
            + fraction_of_year
            - birth_year
        )

    else:

        baseline_age = None


    # =====================================================
    # EDUCATION
    # =====================================================

    education_years, education_date = (
        get_prebaseline_value(
            g,
            "PTEDUCAT",
            baseline_date
        )
    )


    records.append(
        {
            "RID": rid,
            "PTID": ptid,
            "MCI_BASELINE_DATE": baseline_date,

            "SEX_CODE": sex_code,

            "BIRTH_YEAR": birth_year,

            "BASELINE_AGE_YEARS":
                baseline_age,

            "EDUCATION_YEARS":
                education_years,

            "EDUCATION_SOURCE_DATE":
                education_date,
        }
    )


demographics = pd.DataFrame(
    records
)


# =========================================================
# SANITY CHECKS
# =========================================================

print("\n=== BASELINE DEMOGRAPHICS ===")
print(
    f"Subjects: {len(demographics):,}"
)


print("\n=== SEX CODE DISTRIBUTION ===")
print(
    demographics["SEX_CODE"]
    .value_counts(
        dropna=False
    )
)


print("\n=== AGE COVERAGE ===")
print(
    demographics[
        "BASELINE_AGE_YEARS"
    ]
    .isna()
    .value_counts()
)


print("\n=== AGE DISTRIBUTION ===")
print(
    demographics[
        "BASELINE_AGE_YEARS"
    ]
    .dropna()
    .describe()
)


print("\n=== EDUCATION COVERAGE ===")
print(
    demographics[
        "EDUCATION_YEARS"
    ]
    .isna()
    .value_counts()
)


print("\n=== EDUCATION DISTRIBUTION ===")
print(
    demographics[
        "EDUCATION_YEARS"
    ]
    .dropna()
    .describe()
)


print("\n=== EDUCATION SOURCE TIMING ===")

education_delay = (
    demographics[
        "MCI_BASELINE_DATE"
    ]
    - demographics[
        "EDUCATION_SOURCE_DATE"
    ]
).dt.days

print(
    education_delay
    .dropna()
    .describe()
)


# =========================================================
# ASSERTIONS
# =========================================================

assert len(demographics) == 1744
assert demographics["RID"].is_unique

assert (
    demographics[
        "EDUCATION_SOURCE_DATE"
    ]
    .dropna()
    <= demographics.loc[
        demographics[
            "EDUCATION_SOURCE_DATE"
        ].notna(),
        "MCI_BASELINE_DATE"
    ]
).all()


# =========================================================
# SAVE
# =========================================================

demographics.to_csv(
    OUT_PATH,
    index=False
)

print("\n=== SAVED ===")
print(OUT_PATH)

print(
    "\nBaseline demographics build complete."
)