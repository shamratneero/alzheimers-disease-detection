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
# PARSE DATES
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
# DEFINE QUALIFYING AD EVENT
# =========================================================

def is_ad_event(row):
    """
    A qualifying AD event must first be a dementia diagnosis.

    ADNI1:
        DIAGNOSIS == 3 and DXAD == 1

    ADNIGO / ADNI2 / ADNI3 / ADNI4:
        DIAGNOSIS == 3 and DXDDUE == 1
    """

    if row["DIAGNOSIS"] != 3:
        return False

    phase = row["PHASE"]

    if phase == "ADNI1":
        return row.get("DXAD") == 1

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
# BUILD SUBJECT-LEVEL QUALITY FLAGS
# =========================================================

records = []

for _, subject in cohort.iterrows():

    rid = subject["RID"]
    original_outcome = subject["OUTCOME"]

    baseline_date = subject["MCI_BASELINE_DATE"]
    horizon_date = subject["HORIZON_DATE"]

    # -----------------------------------------------------
    # Defaults
    # -----------------------------------------------------

    has_post_ad_followup = False
    later_confirmed_ad = False

    reversion_mci = False
    reversion_cn = False
    reversion_any = False

    first_later_ad_date = pd.NaT

    competing_event_non_ad_dementia = False
    first_non_ad_dementia_date = pd.NaT


    # =====================================================
    # CONVERTER-SPECIFIC AUDIT
    # =====================================================

    if original_outcome == "converter":

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


    # =====================================================
    # NEGATIVE-SIDE COMPETING EVENT AUDIT
    # =====================================================

    if original_outcome == "stable_mci":

        window = dx[
            (dx["RID"] == rid)
            & dx["EXAMDATE"].notna()
            & (dx["EXAMDATE"] >= baseline_date)
            & (dx["EXAMDATE"] <= horizon_date)
        ].copy()

        # Dementia visits that are NOT qualifying AD events
        non_ad_dementia = window[
            (window["DIAGNOSIS"] == 3)
            & (~window["AD_EVENT"])
        ].copy()

        if not non_ad_dementia.empty:

            competing_event_non_ad_dementia = True

            first_non_ad_dementia_date = (
                non_ad_dementia["EXAMDATE"].min()
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

            "COMPETING_EVENT_NON_AD_DEMENTIA":
                competing_event_non_ad_dementia,

            "FIRST_NON_AD_DEMENTIA_DATE":
                first_non_ad_dementia_date,
        }
    )


flags = pd.DataFrame(records)


# =========================================================
# MERGE FLAGS
# =========================================================

final = cohort.merge(
    flags,
    on="RID",
    how="left",
    validate="one_to_one"
)


# =========================================================
# CLEAN OUTCOME TERMINOLOGY
# =========================================================

# Start from original labels
final["FINAL_OUTCOME"] = final["OUTCOME"]

# Rename stable_mci because not everyone actually stayed MCI
final.loc[
    final["OUTCOME"] == "stable_mci",
    "FINAL_OUTCOME"
] = "ad_non_converter"

# Override the two non-AD dementia cases
final.loc[
    final["COMPETING_EVENT_NON_AD_DEMENTIA"],
    "FINAL_OUTCOME"
] = "competing_event_non_ad_dementia"


# =========================================================
# PRIMARY BINARY LABEL
# =========================================================

final["PRIMARY_LABEL"] = pd.NA

# Positive
final.loc[
    final["FINAL_OUTCOME"] == "converter",
    "PRIMARY_LABEL"
] = 1

# Clean negative
final.loc[
    final["FINAL_OUTCOME"] == "ad_non_converter",
    "PRIMARY_LABEL"
] = 0

# Right-censored remains NA
# Competing-event non-AD dementia remains NA


# =========================================================
# STRICT LABEL
# =========================================================

final["STRICT_LABEL"] = pd.NA

# Clean negatives stay negative
final.loc[
    final["FINAL_OUTCOME"] == "ad_non_converter",
    "STRICT_LABEL"
] = 0

# Only later-confirmed converters become strict positives
final.loc[
    (
        (final["FINAL_OUTCOME"] == "converter")
        & (final["LATER_CONFIRMED_AD"])
    ),
    "STRICT_LABEL"
] = 1


# =========================================================
# ADDITIONAL FLAGS
# =========================================================

final["RIGHT_CENSORED"] = (
    final["FINAL_OUTCOME"] == "right_censored"
)

final["NO_POST_AD_FOLLOWUP"] = (
    (final["FINAL_OUTCOME"] == "converter")
    & (~final["HAS_POST_AD_FOLLOWUP"])
)

final["UNCONFIRMED_WITH_FOLLOWUP"] = (
    (final["FINAL_OUTCOME"] == "converter")
    & (final["HAS_POST_AD_FOLLOWUP"])
    & (~final["LATER_CONFIRMED_AD"])
)


# =========================================================
# SANITY CHECKS
# =========================================================

print("\n=== TOTAL CLEAN BASELINE MCI COHORT ===")
print(len(final))


print("\n=== FINAL OUTCOME COUNTS ===")
print(
    final["FINAL_OUTCOME"]
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


print("\n=== COMPETING NON-AD DEMENTIA ===")
print(
    final[
        final["COMPETING_EVENT_NON_AD_DEMENTIA"]
    ][
        [
            "RID",
            "PTID",
            "MCI_BASELINE_DATE",
            "FIRST_NON_AD_DEMENTIA_DATE",
            "FINAL_OUTCOME",
        ]
    ].to_string(index=False)
)


print("\n=== CONVERTER CONFIRMATION ===")
print(
    final.loc[
        final["FINAL_OUTCOME"] == "converter",
        "LATER_CONFIRMED_AD"
    ]
    .value_counts(dropna=False)
)


print("\n=== CONVERTER REVERSION ===")
print(
    final.loc[
        final["FINAL_OUTCOME"] == "converter",
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


# =========================================================
# ASSERTIONS
# =========================================================

# One row per subject
assert final["RID"].is_unique

# Overall clean baseline cohort remains unchanged
assert len(final) == 1744

# Final mutually exclusive outcome counts
assert (
    final["FINAL_OUTCOME"] == "converter"
).sum() == 196

assert (
    final["FINAL_OUTCOME"] == "ad_non_converter"
).sum() == 827

assert (
    final["FINAL_OUTCOME"] == "right_censored"
).sum() == 719

assert (
    final["FINAL_OUTCOME"]
    == "competing_event_non_ad_dementia"
).sum() == 2

# These must sum to the full cohort
assert (
    (final["FINAL_OUTCOME"] == "converter").sum()
    + (final["FINAL_OUTCOME"] == "ad_non_converter").sum()
    + (final["FINAL_OUTCOME"] == "right_censored").sum()
    + (
        final["FINAL_OUTCOME"]
        == "competing_event_non_ad_dementia"
    ).sum()
) == len(final)

# Converter audits
assert (
    final["LATER_CONFIRMED_AD"]
    & (final["FINAL_OUTCOME"] == "converter")
).sum() == 152

assert (
    final["REVERSION_ANY"]
    & (final["FINAL_OUTCOME"] == "converter")
).sum() == 13

assert (
    final["NO_POST_AD_FOLLOWUP"]
).sum() == 39

assert (
    final["UNCONFIRMED_WITH_FOLLOWUP"]
).sum() == 5

# Primary training cohort
assert (
    final["PRIMARY_LABEL"] == 1
).sum() == 196

assert (
    final["PRIMARY_LABEL"] == 0
).sum() == 827

# Strict sensitivity cohort
assert (
    final["STRICT_LABEL"] == 1
).sum() == 152

assert (
    final["STRICT_LABEL"] == 0
).sum() == 827


# =========================================================
# SAVE
# =========================================================

final.to_csv(
    FINAL_PATH,
    index=False
)

print("\n=== SAVED ===")
print(FINAL_PATH)

print("\nFinal cohort rebuild complete.")