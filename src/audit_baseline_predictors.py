import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

DATA = "data/processed/mci24_primary_baseline_predictors.csv"

df = pd.read_csv(DATA, low_memory=False)

predictors = [
    "BASELINE_AGE_YEARS",
    "SEX_CODE",
    "EDUCATION_YEARS",
    "APOE4_COUNT",
]

print("=" * 72)
print("FINAL BASELINE PREDICTOR AUDIT")
print("=" * 72)

# Complete-case set
cc = df.dropna(subset=predictors + ["PRIMARY_LABEL"]).copy()

print("\nRows:", len(cc))
print("Converters:", int((cc["PRIMARY_LABEL"] == 1).sum()))
print("Non-converters:", int((cc["PRIMARY_LABEL"] == 0).sum()))

# ------------------------------------------------------------
# Descriptive statistics by class
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("DESCRIPTIVE STATISTICS BY CLASS")
print("=" * 72)

for label, name in [(0, "NON-CONVERTER"), (1, "CONVERTER")]:
    x = cc[cc["PRIMARY_LABEL"] == label]

    print(f"\n{name} (N={len(x)})")

    print(
        x[
            [
                "BASELINE_AGE_YEARS",
                "EDUCATION_YEARS",
                "APOE4_COUNT",
            ]
        ]
        .describe()
        .to_string()
    )

    print("\nSEX_CODE:")
    print(x["SEX_CODE"].value_counts().sort_index().to_string())

# ------------------------------------------------------------
# Correlation matrix
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("CORRELATION MATRIX")
print("=" * 72)

corr = cc[predictors].corr()
print(corr.round(3).to_string())

# ------------------------------------------------------------
# VIF
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("VARIANCE INFLATION FACTOR")
print("=" * 72)

X_vif = cc[predictors].astype(float).copy()
X_vif = sm.add_constant(X_vif)

vif_rows = []

for i, col in enumerate(X_vif.columns):
    vif_rows.append({
        "VARIABLE": col,
        "VIF": variance_inflation_factor(X_vif.values, i)
    })

vif_df = pd.DataFrame(vif_rows)
print(vif_df.to_string(index=False))

# ------------------------------------------------------------
# Univariable logistic regressions
# ------------------------------------------------------------
print("\n" + "=" * 72)
print("UNIVARIABLE LOGISTIC REGRESSION")
print("=" * 72)

y = cc["PRIMARY_LABEL"].astype(int)

results = []

for predictor in predictors:

    X = cc[[predictor]].astype(float)
    X = sm.add_constant(X)

    model = sm.Logit(y, X).fit(disp=False)

    beta = model.params[predictor]
    se = model.bse[predictor]
    p = model.pvalues[predictor]

    OR = np.exp(beta)
    CI_low = np.exp(beta - 1.96 * se)
    CI_high = np.exp(beta + 1.96 * se)

    results.append({
        "Predictor": predictor,
        "OR": OR,
        "CI_low": CI_low,
        "CI_high": CI_high,
        "p_value": p
    })

results_df = pd.DataFrame(results)

print(
    results_df.round({
        "OR": 3,
        "CI_low": 3,
        "CI_high": 3,
        "p_value": 5
    }).to_string(index=False)
)

print("\n" + "=" * 72)
print("AUDIT COMPLETE")
print("=" * 72)
print("No predictive model has been trained yet.")