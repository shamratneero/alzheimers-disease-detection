import numpy as np
import pandas as pd
import statsmodels.api as sm

from pathlib import Path
from sklearn.metrics import (
    roc_curve,
    confusion_matrix,
    balanced_accuracy_score,
)

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
OOF_PATH = Path(
    "results/baseline_model/primary_baseline_oof_predictions.csv"
)

# ------------------------------------------------------------
# Load OOF predictions
# ------------------------------------------------------------
df = pd.read_csv(OOF_PATH)

required = [
    "PRIMARY_LABEL",
    "OOF_PROBABILITY",
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

y = df["PRIMARY_LABEL"].astype(int).to_numpy()
p = df["OOF_PROBABILITY"].astype(float).to_numpy()

print("=" * 72)
print("BASELINE OOF PROBABILITY + CALIBRATION AUDIT")
print("=" * 72)

print("\nN:", len(df))
print("Converters:", int(y.sum()))
print("Non-converters:", int((y == 0).sum()))

# ------------------------------------------------------------
# Probability distribution
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("OOF PROBABILITY DISTRIBUTION")
print("=" * 72)

for label, name in [(0, "NON-CONVERTER"), (1, "CONVERTER")]:
    x = p[y == label]

    print(f"\n{name}:")
    print(f"N      : {len(x)}")
    print(f"Min    : {x.min():.4f}")
    print(f"P25    : {np.percentile(x, 25):.4f}")
    print(f"Median : {np.median(x):.4f}")
    print(f"P75    : {np.percentile(x, 75):.4f}")
    print(f"Max    : {x.max():.4f}")
    print(f"Mean   : {x.mean():.4f}")

print("\nOverall:")
print(f"Min    : {p.min():.4f}")
print(f"Median : {np.median(p):.4f}")
print(f"Max    : {p.max():.4f}")
print(f"Mean   : {p.mean():.4f}")

# ------------------------------------------------------------
# Calibration intercept and slope
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("CALIBRATION INTERCEPT + SLOPE")
print("=" * 72)

eps = 1e-6
p_clip = np.clip(p, eps, 1 - eps)
logit_p = np.log(p_clip / (1 - p_clip))

# calibration intercept only
X_int = np.ones((len(logit_p), 1))
model_int = sm.GLM(
    y,
    X_int,
    family=sm.families.Binomial(),
    offset=logit_p
).fit()

cal_intercept = float(model_int.params[0])

# calibration slope
X_slope = sm.add_constant(logit_p)
model_slope = sm.GLM(
    y,
    X_slope,
    family=sm.families.Binomial()
).fit()

cal_intercept_joint = float(model_slope.params[0])
cal_slope = float(model_slope.params[1])

print(f"\nCalibration intercept (offset method): {cal_intercept:.4f}")
print(f"Joint calibration intercept:           {cal_intercept_joint:.4f}")
print(f"Calibration slope:                      {cal_slope:.4f}")

# ------------------------------------------------------------
# ROC-derived threshold: Youden J
# descriptive only
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("DESCRIPTIVE THRESHOLD ANALYSIS")
print("=" * 72)

fpr, tpr, thresholds = roc_curve(y, p)

youden = tpr - fpr
best_idx = int(np.argmax(youden))
best_threshold = float(thresholds[best_idx])

pred = (p >= best_threshold).astype(int)

tn, fp, fn, tp = confusion_matrix(
    y,
    pred,
    labels=[0, 1]
).ravel()

sensitivity = tp / (tp + fn)
specificity = tn / (tn + fp)
bacc = balanced_accuracy_score(y, pred)

print(f"\nYouden threshold:   {best_threshold:.4f}")
print(f"Sensitivity:        {sensitivity:.4f}")
print(f"Specificity:        {specificity:.4f}")
print(f"Balanced accuracy:  {bacc:.4f}")

print("\nConfusion matrix:")
print(
    np.array([
        [tn, fp],
        [fn, tp]
    ])
)

print("\n" + "=" * 72)
print("AUDIT COMPLETE")
print("=" * 72)

print(
    "\nImportant: the Youden threshold is descriptive only. "
    "It was derived from the pooled OOF predictions and should not be "
    "treated as a locked deployment threshold."
)