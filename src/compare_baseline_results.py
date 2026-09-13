import json
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path("results/baseline_model")

PRIMARY_SUMMARY = RESULTS_DIR / "primary_baseline_summary.json"
STRICT_SUMMARY = RESULTS_DIR / "strict_baseline_summary.json"

OUT_CSV = RESULTS_DIR / "baseline_primary_vs_strict.csv"

with open(PRIMARY_SUMMARY) as f:
    primary = json.load(f)

with open(STRICT_SUMMARY) as f:
    strict = json.load(f)

rows = [
    {
        "analysis": "Primary labels",
        "n": primary["n"],
        "positives": primary["positives"],
        "negatives": primary["negatives"],
        "roc_auc": primary["pooled_roc_auc"],
        "pr_auc": primary["pooled_pr_auc"],
        "brier": primary["pooled_brier"],
        "balanced_accuracy_0_5": primary["pooled_balanced_accuracy"],
        "sensitivity_0_5": primary["pooled_sensitivity"],
        "specificity_0_5": primary["pooled_specificity"],
        "calibration_intercept_offset": -0.0093,
        "calibration_intercept_joint": -0.0999,
        "calibration_slope": 0.9336,
        "youden_threshold": 0.1984,
        "youden_sensitivity": 0.6173,
        "youden_specificity": 0.6302,
        "youden_balanced_accuracy": 0.6238,
    },
    {
        "analysis": "Strict confirmed labels",
        "n": strict["n"],
        "positives": strict["positives"],
        "negatives": strict["negatives"],
        "roc_auc": strict["pooled_roc_auc"],
        "pr_auc": strict["pooled_pr_auc"],
        "brier": strict["pooled_brier"],
        "balanced_accuracy_0_5": strict["pooled_balanced_accuracy"],
        "sensitivity_0_5": strict["pooled_sensitivity"],
        "specificity_0_5": strict["pooled_specificity"],
        "calibration_intercept_offset": -0.0180,
        "calibration_intercept_joint": -0.3297,
        "calibration_slope": 0.8048,
        "youden_threshold": 0.1416,
        "youden_sensitivity": 0.6842,
        "youden_specificity": 0.5560,
        "youden_balanced_accuracy": 0.6201,
    },
]

df = pd.DataFrame(rows)

df["delta_roc_auc_vs_primary"] = df["roc_auc"] - df.loc[0, "roc_auc"]
df["delta_pr_auc_vs_primary"] = df["pr_auc"] - df.loc[0, "pr_auc"]
df["delta_brier_vs_primary"] = df["brier"] - df.loc[0, "brier"]

df.to_csv(OUT_CSV, index=False)

print("=" * 80)
print("PRIMARY VS STRICT BASELINE COMPARISON")
print("=" * 80)

print(
    df[
        [
            "analysis",
            "n",
            "positives",
            "negatives",
            "roc_auc",
            "pr_auc",
            "brier",
            "calibration_slope",
            "youden_balanced_accuracy",
            "delta_roc_auc_vs_primary",
        ]
    ]
    .round(4)
    .to_string(index=False)
)

print("\nSaved:")
print(OUT_CSV)

print("\nInterpretation:")
print(
    "If strict-label ROC-AUC remains close to the primary-label ROC-AUC, "
    "the baseline discrimination is robust to stricter converter confirmation."
)