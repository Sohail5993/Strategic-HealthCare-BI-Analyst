"""
evaluate.py
-------------
Produces the ROC/PR curve comparison and confusion matrix for the best
care-gap model, matching the readmission project's evaluation visuals.

Outputs:
    ../reports/figures/01_roc_pr_curves.png
    ../reports/figures/02_confusion_matrix.png
"""

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (roc_curve, precision_recall_curve, auc,
                              confusion_matrix, ConfusionMatrixDisplay)

plt.rcParams["figure.dpi"] = 150

artifact = joblib.load("../models/best_care_gap_model.joblib")
model = artifact["model"]
model_name = artifact["model_name"]
X_test = artifact["X_test"]
y_test = artifact["y_test"]
proba = artifact["proba_test"]

# --- ROC + PR curves side by side ---
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

fpr, tpr, _ = roc_curve(y_test, proba)
roc_auc_val = auc(fpr, tpr)
axes[0].plot(fpr, tpr, color="#2C5F8A", linewidth=2, label=f"{model_name} (AUC = {roc_auc_val:.3f})")
axes[0].plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC Curve")
axes[0].legend(loc="lower right", fontsize=9)
axes[0].spines[["top", "right"]].set_visible(False)

precision, recall, _ = precision_recall_curve(y_test, proba)
pr_auc_val = auc(recall, precision)
base_rate = y_test.mean()
axes[1].plot(recall, precision, color="#c0392b", linewidth=2, label=f"{model_name} (AUC = {pr_auc_val:.3f})")
axes[1].axhline(base_rate, linestyle="--", color="gray", linewidth=1, label=f"Base rate ({base_rate:.1%})")
axes[1].set_xlabel("Recall")
axes[1].set_ylabel("Precision")
axes[1].set_title("Precision-Recall Curve")
axes[1].legend(loc="upper right", fontsize=9)
axes[1].spines[["top", "right"]].set_visible(False)

plt.tight_layout()
plt.savefig("../reports/figures/01_roc_pr_curves.png")
plt.close()
print("Saved ROC/PR curves.")

# --- Confusion matrix at a realistic outreach threshold (top 20% flagged) ---
k = int(len(y_test) * 0.20)
threshold = np.sort(proba)[::-1][k - 1]
y_pred = (proba >= threshold).astype(int)

cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(5.5, 5))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["No miss", "Misses"])
disp.plot(ax=ax, cmap="Blues", colorbar=False, values_format="d")
ax.set_title(f"Confusion Matrix at Top-20% Outreach Threshold\n(threshold = {threshold:.3f})", fontsize=11)
plt.tight_layout()
plt.savefig("../reports/figures/02_confusion_matrix.png")
plt.close()
print("Saved confusion matrix.")
print(f"\nAt top-20% threshold: {cm[1,1]} true positives, {cm[0,1]} false positives out of {k} flagged")
