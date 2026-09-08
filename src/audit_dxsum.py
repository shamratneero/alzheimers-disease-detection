from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"


# ---------------------------------------------------------
# Load DXSUM
# ---------------------------------------------------------
df = pd.read_csv(DXSUM_PATH, low_memory=False)

print("\n=== BASIC SHAPE ===")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns):,}")


# ---------------------------------------------------------
# Important columns
# ---------------------------------------------------------
important_cols = [
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
]

print("\n=== IMPORTANT COLUMNS PRESENT ===")

for col in important_cols:
    print(f"{col:12s} -> {col in df.columns}")


# ---------------------------------------------------------
# Unique participants
# ---------------------------------------------------------
if "RID" in df.columns:
    print("\n=== PARTICIPANTS ===")
    print(f"Unique RID: {df['RID'].nunique():,}")


# ---------------------------------------------------------
# Missing exam dates
# ---------------------------------------------------------
if "EXAMDATE" in df.columns:
    df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")

    print("\n=== EXAM DATE QUALITY ===")
    print(f"Missing/invalid EXAMDATE: {df['EXAMDATE'].isna().sum():,}")


# ---------------------------------------------------------
# Diagnosis value distributions
# ---------------------------------------------------------
for col in ["DIAGNOSIS", "DXAD", "DXDDUE", "DXOTHDEM"]:
    if col in df.columns:
        print(f"\n=== VALUE COUNTS: {col} ===")
        print(
            df[col]
            .value_counts(dropna=False)
            .sort_index()
        )


# ---------------------------------------------------------
# Duplicate RID + date records
# ---------------------------------------------------------
if {"RID", "EXAMDATE"}.issubset(df.columns):
    duplicate_mask = df.duplicated(
        subset=["RID", "EXAMDATE"],
        keep=False
    )

    duplicates = df.loc[duplicate_mask]

    print("\n=== DUPLICATE RID + EXAMDATE ===")
    print(f"Rows involved: {len(duplicates):,}")

    if not duplicates.empty:
        print(
            duplicates[
                [
                    c for c in
                    ["RID", "PTID", "EXAMDATE", "VISCODE", "PHASE", "DIAGNOSIS"]
                    if c in duplicates.columns
                ]
            ]
            .sort_values(["RID", "EXAMDATE"])
            .head(30)
            .to_string(index=False)
        )


# ---------------------------------------------------------
# Visits per participant
# ---------------------------------------------------------
if "RID" in df.columns:
    visits_per_subject = df.groupby("RID").size()

    print("\n=== VISITS PER SUBJECT ===")
    print(visits_per_subject.describe())


print("\nAudit complete.")