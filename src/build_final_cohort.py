from pathlib import Path
import pandas as pd


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

OUTCOME_PATH = (
    ROOT
    / "data"
    / "interim"
    / "mci24_outcomes_initial.csv"
)

FINAL_PATH = (
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
    OUTCOME_PATH,
    low_memory=False
)


# =========================================================
# DATE PARSING
# =========================================================

dx["EXAMDATE"] = pd.to_datetime(
    dx["EXAMDATE"],
    errors="coerce"
)

for col in [
    "MCI_BASELINE_DATE",
    "HORIZON_DATE",
    "FIRST_AD_DATE",
    "LAST_FOLLOWUP_DATE",
]:
    cohort[col] = pd.to_datetime(
        cohort[col],
        errors="coerce"
    )


# =========================================================
# DEFINE AD EVENT
# =========================================================

def is_ad_event(row):

    # Must first be diagnosed as dementia
    if row["DIAGNOSIS"] != 3:
        return False

    phase = row["PHASE"]

    # ADNI1 uses DXAD
    if phase == "ADNI1":
        return row.get("DXAD") == 1

    # Later ADNI phases use DXDDUE
    if phase in [
        "ADNIGO",
        "ADNI2",
        "ADNI3",
        "ADNI4",
    ]:
        return row.get("DXDDUE") == 1

    return False


dx["AD_EVENT"] = dx.apply(
    is_ad_event,
    axis=1
)


# =========================================================
# BUILD CONVERTER QUALITY FLAGS
# =========================================================

records = []

for _, subject in cohort.iterrows():

    rid = subject["RID"]
    outcome = subject["OUTCOME"]

    # Defaults for non-converters
    has_post_ad_followup = False
    later_confirmed_ad = False
    reversion_mci = False
    reversion_cn = False
    reversion_any = False

    first_later_ad_date = pd.NaT

    # -----------------------------------------------------
    # Only converters have a FIRST_AD_DATE
    # -----------------------------------------------------

    if outcome == "converter":

        first_ad_date = subject["FIRST_AD_DATE"]

        later = dx[
            (dx["RID"] == rid)
            & dx["EXAMDATE"].notna()
            & (dx["EXAMDATE"] > first_ad_date)
        ].copy()

        later = later.sort_values("EXAMDATE")

        has_post_ad_followup = len(later) > 0

        if has_post_ad_followup:

            later_confirmed_ad = bool(
                later["AD_EVENT"].any()
            )

            reversion_mci = bool(
                (later["DIAGNOSIS"] == 2).any()
            )

            reversion_cn = bool(
                (later["DIAGNOSIS"] == 1).any()
            )

            reversion_any = (
                reversion_mci
                or reversion_cn
            )

            if later_confirmed_ad:

                first_later_ad_date = (
                    later.loc[
                        later["AD_EVENT"],
                        "EXAMDATE"
                    ].min()
                )

    records.append(
        {
            "RID": rid,
            "HAS_POST_AD_FOLLOWUP":
                has_post_ad_followup,

            "LATER_CONFIRMED_AD":
                later_confirmed_ad,

            "FIRST_LATER_AD_DATE":
                first_later_ad_date,

            "REVERSION_TO_MCI":
                reversion_mci,

            "REVERSION_TO_CN":
                reversion_cn,

            "REVERSION_ANY":
                reversion_any,
        }
    )


flags = pd.DataFrame(records)


# =========================================================
# MERGE FLAGS INTO SUBJECT COHORT
# =========================================================

final = cohort.merge(
    flags,
    on="RID",
    how="left",
    validate="one_to_one"
)


# =========================================================
# PRIMARY BINARY LABEL
# =========================================================

# Converter = 1
# Stable MCI = 0
# Right-censored = missing because true 24-month
# outcome is unknown.

final["PRIMARY_LABEL"] = pd.NA

final.loc[
    final["OUTCOME"] == "converter",
    "PRIMARY_LABEL"
] = 1

final.loc[
    final["OUTCOME"] == "stable_mci",
    "PRIMARY_LABEL"
] = 0


# =========================================================
# STRICT CONFIRMATION LABEL
# =========================================================

# Strict positive:
# converter + later confirmed AD
#
# Stable MCI remains negative.
#
# Primary converters without later confirmation are
# intentionally not treated as strict positives.

final["STRICT_LABEL"] = pd.NA

final.loc[
    final["OUTCOME"] == "stable_mci",
    "STRICT_LABEL"
] = 0

final.loc[
    (
        (final["OUTCOME"] == "converter")
        & (final["LATER_CONFIRMED_AD"])
    ),
    "STRICT_LABEL"
] = 1


# =========================================================
# OTHER FLAGS
# =========================================================

final["RIGHT_CENSORED"] = (
    final["OUTCOME"] == "right_censored"
)

final["NO_POST_AD_FOLLOWUP"] = (
    (final["OUTCOME"] == "converter")
    & (~final["HAS_POST_AD_FOLLOWUP"])
)

final["UNCONFIRMED_WITH_FOLLOWUP"] = (
    (final["OUTCOME"] == "converter")
    & (final["HAS_POST_AD_FOLLOWUP"])
    & (~final["LATER_CONFIRMED_AD"])
)


# =========================================================
# SANITY CHECKS
# =========================================================

print("\n=== FINAL COHORT SIZE ===")
print(len(final))


print("\n=== PRIMARY OUTCOME COUNTS ===")
print(
    final["OUTCOME"]
    .value_counts(dropna=False)
)


print("\n=== PRIMARY BINARY LABEL ===")
print(
    final["PRIMARY_LABEL"]
    .value_counts(dropna=False)
)


print("\n=== STRICT LABEL ===")
print(
    final["STRICT_LABEL"]
    .value_counts(dropna=False)
)


print("\n=== LATER CONFIRMED AD ===")
print(
    final.loc[
        final["OUTCOME"] == "converter",
        "LATER_CONFIRMED_AD"
    ]
    .value_counts(dropna=False)
)


print("\n=== REVERSION ANY ===")
print(
    final.loc[
        final["OUTCOME"] == "converter",
        "REVERSION_ANY"
    ]
    .value_counts(dropna=False)
)


print("\n=== NO POST-AD FOLLOW-UP ===")
print(
    final["NO_POST_AD_FOLLOWUP"]
    .value_counts(dropna=False)
)


print("\n=== UNCONFIRMED WITH FOLLOW-UP ===")
print(
    final["UNCONFIRMED_WITH_FOLLOWUP"]
    .value_counts(dropna=False)
)


# ---------------------------------------------------------
# One row per subject
# ---------------------------------------------------------

assert final["RID"].is_unique


# ---------------------------------------------------------
# Known cohort totals from our audits
# ---------------------------------------------------------

assert len(final) == 1744

assert (
    final["OUTCOME"] == "converter"
).sum() == 196

assert (
    final["OUTCOME"] == "stable_mci"
).sum() == 829

assert (
    final["OUTCOME"] == "right_censored"
).sum() == 719

assert (
    final["LATER_CONFIRMED_AD"]
    & (final["OUTCOME"] == "converter")
).sum() == 152

assert (
    final["REVERSION_ANY"]
    & (final["OUTCOME"] == "converter")
).sum() == 13

assert (
    final["NO_POST_AD_FOLLOWUP"]
).sum() == 39

assert (
    final["UNCONFIRMED_WITH_FOLLOWUP"]
).sum() == 5


# =========================================================
# SAVE
# =========================================================

final.to_csv(
    FINAL_PATH,
    index=False
)

print("\n=== SAVED ===")
print(FINAL_PATH)

print("\nFinal cohort build complete.")