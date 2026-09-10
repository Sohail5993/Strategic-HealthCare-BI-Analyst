"""
Exploratory analysis on the cleaned EHR dataset:
  1. Demographic and diagnosis-category profile
  2. Cost driver analysis (what predicts high cost?)
  3. Length-of-stay patterns by comorbidity burden
  4. Rule-based cohort identification: high-cost, high-complexity patients
     who are outreach-worthy candidates for a care-management program
"""

import pandas as pd
import numpy as np
from scipy import stats

CLEAN_PATH = "/home/claude/ehr-patient-outcomes/data/ehr_encounters_clean.csv"
OUT_DIR = "/home/claude/ehr-patient-outcomes/output"

df = pd.read_csv(CLEAN_PATH, parse_dates=["encounter_date"])

print("=" * 70)
print("1. DEMOGRAPHIC & DIAGNOSIS PROFILE")
print("=" * 70)
print(f"Total clean encounters: {len(df):,}")
print(f"Unique patients: {df['patient_id'].nunique():,}")
print(f"\nGender distribution:\n{df['gender'].value_counts(dropna=False)}")
print(f"\nDiagnosis category distribution:\n{df['diagnosis_category'].value_counts()}")

diag_summary = (
    df.groupby("diagnosis_category")
    .agg(n_encounters=("encounter_id", "count"),
         avg_los=("length_of_stay_days", "mean"),
         avg_cost=("total_cost", "mean"),
         readmit_rate=("readmitted_30d", "mean"))
    .round(2)
    .sort_values("avg_cost", ascending=False)
)
diag_summary.to_csv(f"{OUT_DIR}/diagnosis_category_summary.csv")
print(f"\n{diag_summary}")

print("\n" + "=" * 70)
print("2. COST DRIVER ANALYSIS")
print("=" * 70)
cost_df = df.dropna(subset=["total_cost"])
cost_df = cost_df[~cost_df["cost_outlier_flag"]]  # exclude flagged billing-error outliers

corr_los = cost_df[["total_cost", "length_of_stay_days"]].corr().iloc[0, 1]
corr_comorb = cost_df[["total_cost", "comorbidity_count"]].corr().iloc[0, 1]
print(f"Correlation: cost vs. length of stay = {corr_los:.3f}")
print(f"Correlation: cost vs. comorbidity count = {corr_comorb:.3f}")

# ANOVA: does diagnosis category significantly affect cost?
groups = [g["total_cost"].values for _, g in cost_df.groupby("diagnosis_category")]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA (cost by diagnosis category): F = {f_stat:.1f}, p = {p_val:.2e}")

# Simple linear regression: cost ~ LOS + comorbidity_count + age
from numpy.polynomial import polynomial as P
X = cost_df[["length_of_stay_days", "comorbidity_count", "age"]].dropna()
y = cost_df.loc[X.index, "total_cost"]
X_with_const = np.column_stack([np.ones(len(X)), X.values])
coeffs, residuals, rank, sv = np.linalg.lstsq(X_with_const, y.values, rcond=None)
pred = X_with_const @ coeffs
ss_res = np.sum((y.values - pred) ** 2)
ss_tot = np.sum((y.values - y.values.mean()) ** 2)
r_squared = 1 - ss_res / ss_tot
print(f"\nLinear model: cost ~ LOS + comorbidity_count + age")
print(f"  Intercept: {coeffs[0]:.0f}")
print(f"  LOS coefficient: ${coeffs[1]:.0f} per additional day")
print(f"  Comorbidity coefficient: ${coeffs[2]:.0f} per additional comorbidity")
print(f"  Age coefficient: ${coeffs[3]:.0f} per additional year")
print(f"  R-squared: {r_squared:.3f}")

print("\n" + "=" * 70)
print("3. LENGTH OF STAY BY COMORBIDITY BURDEN")
print("=" * 70)
los_by_comorbidity = (
    df.dropna(subset=["length_of_stay_days"])
    .groupby("comorbidity_count")["length_of_stay_days"]
    .agg(["mean", "median", "count"])
    .round(2)
)
los_by_comorbidity.to_csv(f"{OUT_DIR}/los_by_comorbidity.csv")
print(los_by_comorbidity)

kw_groups = [g["length_of_stay_days"].dropna().values
             for _, g in df.groupby("comorbidity_count")]
h_stat, p_val_kw = stats.kruskal(*kw_groups)
print(f"\nKruskal-Wallis (LOS by comorbidity count): H = {h_stat:.1f}, p = {p_val_kw:.2e}")

print("\n" + "=" * 70)
print("4. COHORT IDENTIFICATION: High-cost, high-complexity patients")
print("=" * 70)
# Patient-level rollup
patient_roll = (
    df.groupby("patient_id")
    .agg(n_encounters=("encounter_id", "count"),
         total_cost_ytd=("total_cost", "sum"),
         max_comorbidity=("comorbidity_count", "max"),
         avg_age=("age", "mean"),
         any_readmit=("readmitted_30d", "max"))
    .reset_index()
)

cost_p90 = patient_roll["total_cost_ytd"].quantile(0.90)
cohort_mask = (patient_roll["total_cost_ytd"] >= cost_p90) & (patient_roll["max_comorbidity"] >= 3)
cohort = patient_roll[cohort_mask].copy()

print(f"Cohort definition: annual cost >= 90th percentile (${cost_p90:,.0f}) AND max comorbidity count >= 3")
print(f"Cohort size: {len(cohort):,} patients ({len(cohort)/len(patient_roll)*100:.1f}% of all patients)")
print(f"Cohort share of total cost: ${cohort['total_cost_ytd'].sum():,.0f} "
      f"({cohort['total_cost_ytd'].sum() / patient_roll['total_cost_ytd'].sum() * 100:.1f}% of all spend)")
print(f"Cohort avg age: {cohort['avg_age'].mean():.1f}")
print(f"Cohort 30-day readmit rate: {cohort['any_readmit'].mean()*100:.1f}%  "
      f"(vs. {patient_roll[~cohort_mask]['any_readmit'].mean()*100:.1f}% for everyone else)")

cohort.to_csv(f"{OUT_DIR}/high_cost_complex_cohort.csv", index=False)
patient_roll.to_csv(f"{OUT_DIR}/patient_level_summary.csv", index=False)

print(f"\nSaved cohort list -> {OUT_DIR}/high_cost_complex_cohort.csv")
