import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    brier_score_loss,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
DATA_PATH = Path(
    "data/processed/mci24_primary_baseline_predictors.csv"
)

OUTPUT_DIR = Path("results/baseline_model")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
PREDICTORS = [
    "BASELINE_AGE_YEARS",
    "SEX_CODE",
    "EDUCATION_YEARS",
    "APOE4_COUNT",
]

CONTINUOUS = [
    "BASELINE_AGE_YEARS",
    "EDUCATION_YEARS",
    "APOE4_COUNT",
]

PASSTHROUGH = [
    "SEX_CODE",
]

TARGET = "PRIMARY_LABEL"

N_SPLITS = 5
RANDOM_STATE = 42


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
df = pd.read_csv(DATA_PATH, low_memory=False)

df = df.dropna(
    subset=PREDICTORS + [TARGET]
).copy()

assert len(df) == 1018
assert df["RID"].nunique() == 1018

y = df[TARGET].astype(int).to_numpy()
X = df[PREDICTORS].copy()

print("=" * 72)
print("PRIMARY BASELINE MODEL")
print("=" * 72)

print("\nComplete-case N:", len(df))
print("Converters:", int(y.sum()))
print("Non-converters:", int((y == 0).sum()))


# ------------------------------------------------------------
# Preprocessing
#
# IMPORTANT:
# Scaling happens INSIDE each CV fold.
# No full-dataset scaling is performed.
# ------------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        (
            "continuous",
            StandardScaler(),
            CONTINUOUS,
        ),
        (
            "sex",
            "passthrough",
            PASSTHROUGH,
        ),
    ],
    remainder="drop",
)


# ------------------------------------------------------------
# Logistic regression
# ------------------------------------------------------------
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            LogisticRegression(
                penalty="l2",
                C=1.0,
                solver="liblinear",
                max_iter=1000,
                random_state=RANDOM_STATE,
            ),
        ),
    ]
)


# ------------------------------------------------------------
# Cross-validation
# ------------------------------------------------------------
cv = StratifiedKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

oof_prob = np.full(len(df), np.nan)
oof_pred = np.full(len(df), np.nan)

fold_results = []

for fold, (train_idx, test_idx) in enumerate(
    cv.split(X, y),
    start=1,
):
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    pipeline.fit(X_train, y_train)

    prob = pipeline.predict_proba(X_test)[:, 1]

    # Standard fixed threshold.
    pred = (prob >= 0.5).astype(int)

    oof_prob[test_idx] = prob
    oof_pred[test_idx] = pred

    auc = roc_auc_score(y_test, prob)
    pr_auc = average_precision_score(y_test, prob)
    brier = brier_score_loss(y_test, prob)
    bacc = balanced_accuracy_score(y_test, pred)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        pred,
        labels=[0, 1],
    ).ravel()

    sensitivity = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else np.nan
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else np.nan
    )

    fold_results.append(
        {
            "fold": fold,
            "n_train": len(train_idx),
            "n_test": len(test_idx),
            "positives_test": int(y_test.sum()),
            "roc_auc": auc,
            "pr_auc": pr_auc,
            "brier": brier,
            "balanced_accuracy": bacc,
            "sensitivity": sensitivity,
            "specificity": specificity,
        }
    )

    print(
        f"\nFold {fold}:"
        f" AUC={auc:.4f}"
        f" PR-AUC={pr_auc:.4f}"
        f" Brier={brier:.4f}"
        f" BAcc={bacc:.4f}"
        f" Sens={sensitivity:.4f}"
        f" Spec={specificity:.4f}"
    )


# ------------------------------------------------------------
# OOF validation
# ------------------------------------------------------------
assert not np.isnan(oof_prob).any()
assert not np.isnan(oof_pred).any()

oof_pred = oof_pred.astype(int)

pooled_auc = roc_auc_score(y, oof_prob)

pooled_pr_auc = average_precision_score(
    y,
    oof_prob,
)

pooled_brier = brier_score_loss(
    y,
    oof_prob,
)

pooled_bacc = balanced_accuracy_score(
    y,
    oof_pred,
)

tn, fp, fn, tp = confusion_matrix(
    y,
    oof_pred,
    labels=[0, 1],
).ravel()

pooled_sensitivity = tp / (tp + fn)
pooled_specificity = tn / (tn + fp)


print("\n" + "=" * 72)
print("POOLED OUT-OF-FOLD PERFORMANCE")
print("=" * 72)

print(f"\nROC-AUC:           {pooled_auc:.4f}")
print(f"PR-AUC:            {pooled_pr_auc:.4f}")
print(f"Brier score:       {pooled_brier:.4f}")
print(f"Balanced accuracy: {pooled_bacc:.4f}")
print(f"Sensitivity:       {pooled_sensitivity:.4f}")
print(f"Specificity:       {pooled_specificity:.4f}")

print("\nConfusion matrix:")
print(
    np.array(
        [
            [tn, fp],
            [fn, tp],
        ]
    )
)


# ------------------------------------------------------------
# Fold summaries
# ------------------------------------------------------------
fold_df = pd.DataFrame(fold_results)

print("\n" + "=" * 72)
print("MEAN ± SD ACROSS FOLDS")
print("=" * 72)

metrics = [
    "roc_auc",
    "pr_auc",
    "brier",
    "balanced_accuracy",
    "sensitivity",
    "specificity",
]

for metric in metrics:
    mean = fold_df[metric].mean()
    sd = fold_df[metric].std(ddof=1)

    print(
        f"{metric:20s}: "
        f"{mean:.4f} ± {sd:.4f}"
    )


# ------------------------------------------------------------
# Save OOF predictions
# ------------------------------------------------------------
oof_df = df[
    [
        "RID",
        "PTID",
        "PRIMARY_LABEL",
    ]
].copy()

oof_df["OOF_PROBABILITY"] = oof_prob
oof_df["OOF_PREDICTION_0_5"] = oof_pred

oof_path = (
    OUTPUT_DIR /
    "primary_baseline_oof_predictions.csv"
)

oof_df.to_csv(
    oof_path,
    index=False,
)


# ------------------------------------------------------------
# Save fold metrics
# ------------------------------------------------------------
fold_path = (
    OUTPUT_DIR /
    "primary_baseline_fold_metrics.csv"
)

fold_df.to_csv(
    fold_path,
    index=False,
)


# ------------------------------------------------------------
# Save summary
# ------------------------------------------------------------
summary = {
    "n": int(len(df)),
    "positives": int(y.sum()),
    "negatives": int((y == 0).sum()),
    "predictors": PREDICTORS,
    "n_splits": N_SPLITS,
    "random_state": RANDOM_STATE,
    "pooled_roc_auc": float(pooled_auc),
    "pooled_pr_auc": float(pooled_pr_auc),
    "pooled_brier": float(pooled_brier),
    "pooled_balanced_accuracy": float(pooled_bacc),
    "pooled_sensitivity": float(
        pooled_sensitivity
    ),
    "pooled_specificity": float(
        pooled_specificity
    ),
}

summary_path = (
    OUTPUT_DIR /
    "primary_baseline_summary.json"
)

with open(summary_path, "w") as f:
    json.dump(
        summary,
        f,
        indent=2,
    )


print("\n" + "=" * 72)
print("TRAINING COMPLETE")
print("=" * 72)

print("\nSaved:")
print(oof_path)
print(fold_path)
print(summary_path)