"""
EHR data cleaning pipeline.

Takes the raw, messy encounter extract and produces an analysis-ready dataset,
logging every cleaning decision so the transformation is auditable — which
matters in healthcare data work, where silently dropping or altering records
without a trail is a real governance problem, not just a coding shortcut.
"""

import pandas as pd
import numpy as np
from dateutil import parser as dateparser

RAW_PATH = "/home/claude/ehr-patient-outcomes/data/ehr_encounters_raw.csv"
CLEAN_PATH = "/home/claude/ehr-patient-outcomes/data/ehr_encounters_clean.csv"
REPORT_PATH = "/home/claude/ehr-patient-outcomes/output/data_quality_report.csv"

df = pd.read_csv(RAW_PATH)
n_start = len(df)
quality_log = []

def log(step, detail, n_affected):
    quality_log.append({"step": step, "detail": detail, "rows_affected": n_affected})
    print(f"[{step}] {detail} (rows affected: {n_affected})")

print("=" * 70)
print(f"STARTING: {n_start:,} raw rows")
print("=" * 70)

# ---------------------------------------------------------------------------
# 1. Remove exact and encounter_id duplicates
# ---------------------------------------------------------------------------
n_before = len(df)
df = df.drop_duplicates(subset="encounter_id", keep="first")
log("Deduplication", "Dropped rows with duplicate encounter_id (kept first occurrence)",
    n_before - len(df))

# ---------------------------------------------------------------------------
# 2. Standardize gender formatting
# ---------------------------------------------------------------------------
n_messy_gender = df["gender"].notna().sum()
gender_map = {
    "m": "M", "male": "M", "male ": "M",
    "f": "F", "female": "F", " female": "F",
}
df["gender_clean"] = (
    df["gender"].astype(str).str.strip().str.lower().map(gender_map)
)
df.loc[df["gender"].isna(), "gender_clean"] = np.nan
n_fixed = ((df["gender"].astype(str).str.strip() != df["gender_clean"]) & df["gender"].notna()).sum()
log("Gender standardization", "Mapped 10 raw variants (M/Male/m/MALE/'Male '/F/Female/f/FEMALE/' Female') to M/F",
    n_fixed)
n_missing_gender = df["gender_clean"].isna().sum()
log("Gender missingness", "Left missing gender as null rather than imputing a guessed value",
    n_missing_gender)

# ---------------------------------------------------------------------------
# 3. Standardize encounter_date across 3 mixed formats
# ---------------------------------------------------------------------------
def parse_any_date(s):
    try:
        return dateparser.parse(str(s))
    except Exception:
        return pd.NaT

df["encounter_date_clean"] = df["encounter_date"].apply(parse_any_date)
n_unparsed = df["encounter_date_clean"].isna().sum()
log("Date standardization", "Parsed 3 mixed date formats (ISO / MM-DD-YYYY / DD-Mon-YYYY) into a single datetime type",
    len(df))
if n_unparsed:
    log("Date parse failures", "Rows where date could not be parsed", n_unparsed)

# ---------------------------------------------------------------------------
# 4. Fix impossible age values
# ---------------------------------------------------------------------------
n_bad_age = ((df["age"] <= 0) | (df["age"] > 110)).sum()
df.loc[(df["age"] <= 0) | (df["age"] > 110), "age"] = np.nan
log("Age validation", "Nulled impossible ages (<=0 or >110) rather than guessing a replacement",
    n_bad_age)

# ---------------------------------------------------------------------------
# 5. Fix impossible length-of-stay values
# ---------------------------------------------------------------------------
n_bad_los = ((df["length_of_stay_days"] < 0) | (df["length_of_stay_days"] > 90)).sum()
df.loc[(df["length_of_stay_days"] < 0) | (df["length_of_stay_days"] > 90), "length_of_stay_days"] = np.nan
log("Length-of-stay validation", "Nulled impossible LOS values (<0 or >90 days, e.g. entry errors like 999 or -2)",
    n_bad_los)

# ---------------------------------------------------------------------------
# 6. Flag (not silently drop) extreme cost outliers
# ---------------------------------------------------------------------------
cost_q99 = df["total_cost"].quantile(0.99)
n_extreme_cost = (df["total_cost"] > cost_q99 * 3).sum()
df["cost_outlier_flag"] = df["total_cost"] > cost_q99 * 3
log("Cost outlier flagging", f"Flagged (not removed) costs > 3x the 99th percentile (${cost_q99*3:,.0f}) as likely billing errors for analyst review",
    n_extreme_cost)

# ---------------------------------------------------------------------------
# 7. Missing diagnosis code / cost — quantify, don't impute
# ---------------------------------------------------------------------------
n_missing_dx = df["primary_diagnosis_code"].isna().sum()
log("Missing diagnosis code", "Retained rows with missing diagnosis code, flagged for downstream exclusion from diagnosis-specific analysis",
    n_missing_dx)
n_missing_cost = df["total_cost"].isna().sum()
log("Missing cost", "Retained rows with missing cost, excluded from cost-driver analysis only",
    n_missing_cost)

# ---------------------------------------------------------------------------
# Finalize: select and rename clean columns
# ---------------------------------------------------------------------------
clean = df[[
    "encounter_id", "patient_id", "encounter_date_clean", "age", "gender_clean",
    "department", "primary_diagnosis_code", "primary_diagnosis_desc", "diagnosis_category",
    "comorbidity_count", "procedure", "length_of_stay_days", "total_cost", "cost_outlier_flag",
    "insurance_type", "readmitted_30d",
]].rename(columns={"encounter_date_clean": "encounter_date", "gender_clean": "gender"})

clean.to_csv(CLEAN_PATH, index=False)
pd.DataFrame(quality_log).to_csv(REPORT_PATH, index=False)

print("\n" + "=" * 70)
print(f"FINISHED: {len(clean):,} clean rows (from {n_start:,} raw rows)")
print("=" * 70)
print(f"Saved clean dataset -> {CLEAN_PATH}")
print(f"Saved data quality report -> {REPORT_PATH}")
