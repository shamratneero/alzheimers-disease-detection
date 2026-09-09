from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PTDEMOG_PATH = (
    ROOT
    / "data"
    / "raw"
    / "PTDEMOG_06Sep2026.csv"
)


# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(
    PTDEMOG_PATH,
    low_memory=False
)


# =========================================================
# BASIC STRUCTURE
# =========================================================

print("\n=== PTDEMOG SHAPE ===")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns):,}")


print("\n=== COLUMN NAMES ===")
for col in df.columns:
    print(col)


# =========================================================
# SUBJECT IDENTIFIERS
# =========================================================

print("\n=== UNIQUE SUBJECTS ===")

if "RID" in df.columns:
    print(
        "Unique RID:",
        df["RID"].nunique(dropna=True)
    )

if "PTID" in df.columns:
    print(
        "Unique PTID:",
        df["PTID"].nunique(dropna=True)
    )


# =========================================================
# POSSIBLE DATE / VISIT COLUMNS
# =========================================================

date_like = [
    c for c in df.columns
    if (
        "DATE" in c.upper()
        or "VIS" in c.upper()
        or "PHASE" in c.upper()
    )
]

print("\n=== POSSIBLE DATE / VISIT COLUMNS ===")
print(date_like)


# =========================================================
# DEMOGRAPHIC CANDIDATE COLUMNS
# =========================================================

keywords = [
    "AGE",
    "SEX",
    "GENDER",
    "EDUC",
    "BIRTH",
    "DOB",
    "PTDOB",
    "PTGENDER",
    "PTEDUCAT",
]

candidate_cols = []

for col in df.columns:
    upper = col.upper()

    if any(
        keyword in upper
        for keyword in keywords
    ):
        candidate_cols.append(col)


print("\n=== DEMOGRAPHIC CANDIDATE COLUMNS ===")
print(candidate_cols)


# =========================================================
# UNIQUE VALUES FOR IMPORTANT DEMOGRAPHIC FIELDS
# =========================================================

for col in candidate_cols:

    print("\n" + "=" * 70)
    print(f"COLUMN: {col}")
    print("=" * 70)

    print(
        df[col]
        .value_counts(
            dropna=False
        )
        .head(30)
    )


# =========================================================
# DUPLICATES PER SUBJECT
# =========================================================

if "RID" in df.columns:

    counts = (
        df.groupby("RID")
        .size()
        .sort_values(
            ascending=False
        )
    )

    print("\n=== ROWS PER RID ===")

    print(
        counts.describe()
    )

    print("\nSubjects with >1 PTDEMOG row:")
    print(
        (counts > 1).sum()
    )

    print("\nTop subjects by number of rows:")
    print(
        counts.head(20)
    )


# =========================================================
# FIRST FEW ROWS
# =========================================================

print("\n=== FIRST 10 ROWS ===")

print(
    df.head(10)
    .to_string()
)


print("\nPTDEMOG audit complete.")