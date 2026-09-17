"""
train_pipeline.py
--------------------
Trains logistic regression, random forest, and XGBoost models to predict
which chronic disease patients will miss their next guideline-recommended
screening/follow-up. Evaluates on precision at realistic outreach-capacity
thresholds (not just ROC-AUC), consistent with the readmission project's
evaluation philosophy.

Outputs:
    ../models/best_care_gap_model.joblib
    ../reports/metrics/metrics.json
    ../reports/metrics/model_comparison_metrics.csv
"""

import json
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score
from xgboost import XGBClassifier

sys.path.append(".")
from feature_engineering import get_splits

RANDOM_STATE = 42


def precision_at_k(y_true, y_scores, k_frac):
    n = len(y_true)
    k = max(1, int(n * k_frac))
    order = np.argsort(-y_scores)
    top_k_idx = order[:k]
    return precision_score(y_true.iloc[top_k_idx] if hasattr(y_true, "iloc") else y_true[top_k_idx],
                            np.ones(k), zero_division=0)


def evaluate_model(name, model, X_test, y_test):
    proba = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, proba)
    pr_auc = average_precision_score(y_test, proba)
    prec_10 = precision_at_k(y_test, proba, 0.10)
    prec_20 = precision_at_k(y_test, proba, 0.20)
    return {
        "model": name,
        "roc_auc": round(roc_auc, 3),
        "pr_auc": round(pr_auc, 3),
        "precision_at_10pct": round(prec_10, 3),
        "precision_at_20pct": round(prec_20, 3),
    }, proba


def main():
    X_train, X_test, y_train, y_test, df_train, df_test = get_splits()
    base_rate = y_test.mean()
    print(f"Train size: {len(X_train):,} | Test size: {len(X_test):,} | Base rate: {base_rate:.1%}")

    results = []
    probas = {}
    models = {}

    # --- Logistic Regression (class-weighted, not resampled) ---
    lr = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)
    lr.fit(X_train, y_train)
    r, p = evaluate_model("Logistic Regression", lr, X_test, y_test)
    results.append(r); probas["Logistic Regression"] = p; models["Logistic Regression"] = lr

    # --- Random Forest ---
    rf = RandomForestClassifier(
        n_estimators=400, max_depth=8, min_samples_leaf=20,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    r, p = evaluate_model("Random Forest", rf, X_test, y_test)
    results.append(r); probas["Random Forest"] = p; models["Random Forest"] = rf

    # --- XGBoost ---
    scale_pos_weight = (1 - y_train.mean()) / y_train.mean()
    xgb = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.85, colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight, eval_metric="logloss",
        random_state=RANDOM_STATE, n_jobs=-1
    )
    xgb.fit(X_train, y_train)
    r, p = evaluate_model("XGBoost", xgb, X_test, y_test)
    results.append(r); probas["XGBoost"] = p; models["XGBoost"] = xgb

    results_df = pd.DataFrame(results).sort_values("pr_auc", ascending=False)
    print("\nModel comparison (held-out test set):")
    print(results_df.to_string(index=False))

    best_name = results_df.iloc[0]["model"]
    best_model = models[best_name]
    print(f"\nBest model by PR-AUC: {best_name}")

    # Save artifacts
    results_df.to_csv("../reports/metrics/model_comparison_metrics.csv", index=False)
    joblib.dump(
        {"model": best_model, "model_name": best_name, "feature_columns": list(X_train.columns),
         "X_test": X_test, "y_test": y_test, "proba_test": probas[best_name]},
        "../models/best_care_gap_model.joblib"
    )

    metrics = {
        "base_rate": round(float(base_rate), 4),
        "best_model": best_name,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_features": X_train.shape[1],
        "models": results,
    }
    with open("../reports/metrics/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved model comparison, best model artifact, and metrics.json")


if __name__ == "__main__":
    main()
