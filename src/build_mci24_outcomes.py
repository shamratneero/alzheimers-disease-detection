from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"
BASELINE_PATH = ROOT / "data" / "interim" / "mci_baseline_candidates.csv"
OUT_PATH = ROOT / "data" / "interim" / "mci24_outcomes_initial.csv"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
dx = pd.read_csv(DXSUM_PATH, low_memory=False)
baseline = pd.read_csv(BASELINE_PATH, low_memory=False)

dx["EXAMDATE"] = pd.to_datetime(dx["EXAMDATE"], errors="coerce")
baseline["EXAMDATE"] = pd.to_datetime(baseline["EXAMDATE"], errors="coerce")


# ---------------------------------------------------------
# Identify subjects with dementia before baseline MCI
# ---------------------------------------------------------
baseline_dates = baseline[["RID", "EXAMDATE"]].rename(
    columns={"EXAMDATE": "MCI_BASELINE_DATE"}
)

merged = dx.merge(
    baseline_dates,
    on="RID",
    how="inner"
)

pre = merged[
    merged["EXAMDATE"].notna()
    & (merged["EXAMDATE"] < merged["MCI_BASELINE_DATE"])
]

prior_dementia_rids = set(
    pre.loc[pre["DIAGNOSIS"] == 3, "RID"].unique()
)

print("\n=== EXCLUDING PRIOR DEMENTIA ===")
print(f"Subjects excluded: {len(prior_dementia_rids):,}")


# ---------------------------------------------------------
# Keep clean baseline candidates
# ---------------------------------------------------------
clean_baseline = baseline[
    ~baseline["RID"].isin(prior_dementia_rids)
].copy()

print(f"Clean baseline MCI candidates: {len(clean_baseline):,}")


# ---------------------------------------------------------
# Helper: determine whether a row is an AD event
# ---------------------------------------------------------
def is_ad_event(row):
    if row["DIAGNOSIS"] != 3:
        return False

    phase = row["PHASE"]

    if phase == "ADNI1":
        return row.get("DXAD") == 1

    if phase in ["ADNIGO", "ADNI2", "ADNI3", "ADNI4"]:
        return row.get("DXDDUE") == 1

    return False


dx["AD_EVENT"] = dx.apply(is_ad_event, axis=1)


# ---------------------------------------------------------
# Build subject-level outcomes
# ---------------------------------------------------------
records = []

for _, base in clean_baseline.iterrows():
    rid = base["RID"]
    baseline_date = base["EXAMDATE"]

    subject = dx[
        (dx["RID"] == rid)
        & dx["EXAMDATE"].notna()
        & (dx["EXAMDATE"] >= baseline_date)
    ].copy()

    subject = subject.sort_values("EXAMDATE")

    # 24-month horizon
    horizon_date = baseline_date + pd.DateOffset(months=24)

    # AD events after baseline and within 24 months
    ad_within_24 = subject[
        (subject["AD_EVENT"])
        & (subject["EXAMDATE"] > baseline_date)
        & (subject["EXAMDATE"] <= horizon_date)
    ]

    # Latest dated follow-up after baseline
    post_baseline = subject[
        subject["EXAMDATE"] > baseline_date
    ]

    if len(post_baseline) > 0:
        last_followup_date = post_baseline["EXAMDATE"].max()
        followup_days = (last_followup_date - baseline_date).days
    else:
        last_followup_date = pd.NaT
        followup_days = 0

    # -----------------------------------------------------
    # Primary outcome
    # -----------------------------------------------------
    if len(ad_within_24) > 0:
        outcome = "converter"
        first_ad_date = ad_within_24["EXAMDATE"].min()
        days_to_ad = (first_ad_date - baseline_date).days

    elif pd.notna(last_followup_date) and last_followup_date >= horizon_date:
        outcome = "stable_mci"
        first_ad_date = pd.NaT
        days_to_ad = None

    else:
        outcome = "right_censored"
        first_ad_date = pd.NaT
        days_to_ad = None

    records.append(
        {
            "RID": rid,
            "PTID": base["PTID"],
            "MCI_BASELINE_DATE": baseline_date,
            "BASELINE_PHASE": base["PHASE"],
            "HORIZON_DATE": horizon_date,
            "OUTCOME": outcome,
            "FIRST_AD_DATE": first_ad_date,
            "DAYS_TO_AD": days_to_ad,
            "LAST_FOLLOWUP_DATE": last_followup_date,
            "FOLLOWUP_DAYS": followup_days,
        }
    )


outcomes = pd.DataFrame(records)


# ---------------------------------------------------------
# Audit summary
# ---------------------------------------------------------
print("\n=== 24-MONTH OUTCOME COUNTS ===")
print(outcomes["OUTCOME"].value_counts())

print("\n=== CONSISTENCY CHECK ===")
n_total = len(outcomes)
n_converter = (outcomes["OUTCOME"] == "converter").sum()
n_stable = (outcomes["OUTCOME"] == "stable_mci").sum()
n_censored = (outcomes["OUTCOME"] == "right_censored").sum()

print(f"Total: {n_total}")
print(f"Converter: {n_converter}")
print(f"Stable MCI: {n_stable}")
print(f"Right-censored: {n_censored}")
print(f"Sum check: {n_converter + n_stable + n_censored}")

assert n_total == n_converter + n_stable + n_censored

outcomes.to_csv(OUT_PATH, index=False)

print(f"\nSaved to: {OUT_PATH}")
print("\nInitial 24-month outcome build complete.")