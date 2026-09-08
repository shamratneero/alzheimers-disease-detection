from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DXSUM_PATH = ROOT / "data" / "raw" / "DXSUM_06Sep2026.csv"

df = pd.read_csv(DXSUM_PATH, low_memory=False)
df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")

mask = (
    (df["DIAGNOSIS"] == 3)
    & (df["PHASE"].isin(["ADNIGO", "ADNI2", "ADNI3", "ADNI4"]))
    & (df["DXDDUE"].isna())
)

rows = df.loc[mask].copy()

cols = [
    c for c in [
        "RID",
        "PTID",
        "EXAMDATE",
        "VISCODE",
        "VISCODE2",
        "PHASE",
        "DIAGNOSIS",
        "DXDDUE",
        "DXODES",
        "DXAPP",
        "DXAPOSS",
        "DXMOTHET",
        "DXCONFID",
    ]
    if c in df.columns
]

print("\n=== LATER-PHASE DEMENTIA WITH MISSING DXDDUE ===")
print(f"Rows: {len(rows)}")
print(rows[cols].sort_values(["RID", "EXAMDATE"]).to_string(index=False))

print("\nDone.")