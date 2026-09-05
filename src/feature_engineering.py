"""
feature_engineering.py
------------------------
Builds the model-ready feature matrix from the raw synthetic patient
population: encodes categoricals, expands the multi-label conditions
column into flags, and produces the train/test split used by
train_pipeline.py.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ALL_CONDITIONS = ["Diabetes", "Hypertension", "CHF", "CKD", "COPD"]


def load_and_engineer(path="../data/patients.csv"):
    df = pd.read_csv(path)

    # Expand multi-label conditions into binary flags
    for cond in ALL_CONDITIONS:
        df[f"has_{cond.lower()}"] = df["conditions"].str.contains(cond).astype(int)

    # Simple engineered features
    df["high_noshow_history"] = (df["prior_noshow_rate"] > 0.35).astype(int)
    df["low_adherence"] = (df["pdc_medication_adherence"] < 0.6).astype(int)
    df["overdue_long"] = (df["days_since_last_visit"] > 180).astype(int)
    df["multiple_open_gaps"] = (df["open_care_gaps_count"] >= 2).astype(int)

    feature_cols = [
        "age", "n_chronic_conditions", "days_since_last_visit", "prior_noshow_rate",
        "pdc_medication_adherence", "distance_to_clinic_miles", "open_care_gaps_count",
        "days_since_last_reminder_sent", "high_noshow_history", "low_adherence",
        "overdue_long", "multiple_open_gaps",
        "has_diabetes", "has_hypertension", "has_chf", "has_ckd", "has_copd",
    ] + [f"has_{c.lower()}" for c in [] ]  # placeholder, conditions already added above

    bool_cols = ["has_transportation_barrier", "has_pcp_assigned", "telehealth_enrolled",
                 "reminder_contact_on_file", "language_barrier_flag"]
    for c in bool_cols:
        df[c] = df[c].astype(int)
    feature_cols += bool_cols

    cat_cols = ["sex", "insurance_type", "focus_service"]
    df_encoded = pd.get_dummies(df[cat_cols], prefix=cat_cols)
    feature_cols += list(df_encoded.columns)

    X = pd.concat([df[feature_cols[:len(feature_cols) - len(df_encoded.columns)]], df_encoded], axis=1)
    y = df["missed_next_service"]

    return X, y, df


def get_splits(random_state=42, test_size=0.2):
    X, y, df = load_and_engineer()
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test, df_train, df_test


if __name__ == "__main__":
    X, y, df = load_and_engineer()
    print(f"Feature matrix shape: {X.shape}")
    print(f"Positive rate (missed_next_service): {y.mean():.1%}")
    print(f"\nFeature columns:\n{list(X.columns)}")
