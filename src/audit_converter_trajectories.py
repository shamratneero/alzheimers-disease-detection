from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"
OUTCOME_PATH = ROOT / "data" / "interim" / "mci24_outcomes_initial.csv"

dx = pd.read_csv(DXSUM_PATH, low_memory=False)
outcomes = pd.read_csv(OUTCOME_PATH, low_memory=False)

dx["EXAMDATE"] = pd.to_datetime(dx["EXAMDATE"], errors="coerce")
outcomes["FIRST_AD_DATE"] = pd.to_datetime(
    outcomes["FIRST_AD_DATE"],
    errors="coerce"
)

converters = outcomes[outcomes["OUTCOME"] == "converter"].copy()


def is_ad_event(row):
    if row["DIAGNOSIS"] != 3:
        return False

    if row["PHASE"] == "ADNI1":
        return row.get("DXAD") == 1

    if row["PHASE"] in ["ADNIGO", "ADNI2", "ADNI3", "ADNI4"]:
        return row.get("DXDDUE") == 1

    return False


dx["AD_EVENT"] = dx.apply(is_ad_event, axis=1)

records = []

for _, conv in converters.iterrows():
    rid = conv["RID"]
    first_ad_date = conv["FIRST_AD_DATE"]

    later = dx[
        (dx["RID"] == rid)
        & dx["EXAMDATE"].notna()
        & (dx["EXAMDATE"] > first_ad_date)
    ].copy()

    later = later.sort_values("EXAMDATE")

    has_post_ad_followup = len(later) > 0

    later_confirmed_ad = bool(
        later["AD_EVENT"].any()
    ) if has_post_ad_followup else False

    later_mci = bool(
        (later["DIAGNOSIS"] == 2).any()
    ) if has_post_ad_followup else False

    later_cn = bool(
        (later["DIAGNOSIS"] == 1).any()
    ) if has_post_ad_followup else False

    first_later_ad_date = (
        later.loc[later["AD_EVENT"], "EXAMDATE"].min()
        if later_confirmed_ad
        else pd.NaT
    )

    records.append(
        {
            "RID": rid,
            "PTID": conv["PTID"],
            "FIRST_AD_DATE": first_ad_date,
            "HAS_POST_AD_FOLLOWUP": has_post_ad_followup,
            "LATER_CONFIRMED_AD": later_confirmed_ad,
            "FIRST_LATER_AD_DATE": first_later_ad_date,
            "LATER_MCI": later_mci,
            "LATER_CN": later_cn,
        }
    )

audit = pd.DataFrame(records)

print("\n=== CONVERTER TRAJECTORY AUDIT ===")
print(f"Converters: {len(audit)}")

print("\n=== POST-AD FOLLOW-UP ===")
print(audit["HAS_POST_AD_FOLLOWUP"].value_counts(dropna=False))

print("\n=== LATER CONFIRMED AD ===")
print(audit["LATER_CONFIRMED_AD"].value_counts(dropna=False))

print("\n=== LATER MCI ===")
print(audit["LATER_MCI"].value_counts(dropna=False))

print("\n=== LATER CN ===")
print(audit["LATER_CN"].value_counts(dropna=False))


reversions = audit[
    audit["LATER_MCI"] | audit["LATER_CN"]
].copy()

print("\n=== CONVERTERS WITH LATER MCI OR CN ===")
print(f"Subjects: {len(reversions)}")

if not reversions.empty:
    print(
        reversions[
            [
                "RID",
                "PTID",
                "FIRST_AD_DATE",
                "HAS_POST_AD_FOLLOWUP",
                "LATER_CONFIRMED_AD",
                "LATER_MCI",
                "LATER_CN",
            ]
        ]
        .sort_values("RID")
        .to_string(index=False)
    )

no_followup = audit[
    ~audit["HAS_POST_AD_FOLLOWUP"]
].copy()

print("\n=== NO POST-AD FOLLOW-UP ===")
print(f"Subjects: {len(no_followup)}")

print("\n=== STRICT-CONFIRMATION COUNT ===")
strict_count = audit["LATER_CONFIRMED_AD"].sum()
print(f"Converters with later confirmed AD: {strict_count}")
print(f"Primary converters total: {len(audit)}")

print("\nConverter-trajectory audit complete.")