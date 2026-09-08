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

converters = outcomes[
    outcomes["OUTCOME"] == "converter"
].copy()


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

    has_followup = len(later) > 0
    has_later_ad = later["AD_EVENT"].any() if has_followup else False

    if has_followup and not has_later_ad:
        records.append(
            {
                "RID": rid,
                "PTID": conv["PTID"],
                "FIRST_AD_DATE": first_ad_date,
            }
        )


unconfirmed = pd.DataFrame(records)

print("\n=== UNCONFIRMED CONVERTERS WITH FOLLOW-UP ===")
print(f"Subjects: {len(unconfirmed)}")

for _, row in unconfirmed.iterrows():
    rid = row["RID"]
    first_ad_date = row["FIRST_AD_DATE"]

    print("\n" + "=" * 60)
    print(f"RID {rid} | PTID {row['PTID']}")
    print(f"First AD date: {first_ad_date.date()}")

    subject = dx[
        (dx["RID"] == rid)
        & dx["EXAMDATE"].notna()
        & (dx["EXAMDATE"] >= first_ad_date)
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
            "AD_EVENT",
        ]
        if c in subject.columns
    ]

    print(subject[cols].to_string(index=False))


print("\nUnconfirmed-converter audit complete.")