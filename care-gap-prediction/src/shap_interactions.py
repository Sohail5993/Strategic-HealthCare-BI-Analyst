"""
shap_interactions.py
-----------------------
Generates SHAP explainability artifacts for the best care-gap model:
a global summary (beeswarm), a mean-|SHAP| bar chart, and feature
importance CSV -- mirroring the readmission project's explainability
outputs for a consistent portfolio presentation.

Outputs:
    ../reports/figures/03_shap_beeswarm.png
    ../reports/figures/04_shap_bar.png
    ../reports/metrics/shap_feature_importance.csv
"""

import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression

sys.path.append(".")

plt.rcParams["figure.dpi"] = 150

artifact = joblib.load("../models/best_care_gap_model.joblib")
model = artifact["model"]
model_name = artifact["model_name"]
X_test = artifact["X_test"]
feature_columns = artifact["feature_columns"]

print(f"Explaining model: {model_name}")

# Sample for tractable SHAP computation
sample_size = min(1500, len(X_test))
X_sample = X_test.sample(sample_size, random_state=7).astype(float)

if isinstance(model, LogisticRegression):
    background = X_test.sample(min(200, len(X_test)), random_state=1).astype(float)
    explainer = shap.LinearExplainer(model, shap.maskers.Independent(background, max_samples=200))
    shap_values = explainer.shap_values(X_sample)
else:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

# --- Beeswarm summary plot ---
plt.figure(figsize=(9, 8))
shap.summary_plot(shap_values, X_sample, show=False, plot_size=None)
plt.title("SHAP Summary — Global Feature Impact on Missed Care Gap", fontsize=13)
plt.tight_layout()
plt.savefig("../reports/figures/03_shap_beeswarm.png", bbox_inches="tight")
plt.close()
print("Saved beeswarm plot.")

# --- Mean |SHAP| bar chart ---
mean_abs_shap = np.abs(shap_values).mean(axis=0)
importance_df = pd.DataFrame({
    "feature": feature_columns,
    "mean_abs_shap": mean_abs_shap
}).sort_values("mean_abs_shap", ascending=False)

top_n = 10
fig, ax = plt.subplots(figsize=(9, 5.5))
top_features = importance_df.head(top_n).iloc[::-1]
ax.barh(top_features["feature"], top_features["mean_abs_shap"], color="#2C5F8A")
ax.set_xlabel("mean(|SHAP value|) (average impact on model output magnitude)")
ax.set_title("Mean |SHAP| Feature Importance", fontsize=13)
plt.tight_layout()
plt.savefig("../reports/figures/04_shap_bar.png", bbox_inches="tight")
plt.close()
print("Saved bar chart.")

importance_df.to_csv("../reports/metrics/shap_feature_importance.csv", index=False)
print("\nTop 10 features by mean |SHAP|:")
print(importance_df.head(10).to_string(index=False))
