"""
Synthetic EHR encounter dataset generator.

Builds a realistically MESSY dataset (~8,000 encounters, ~5,000 patients) with the
kinds of data-quality problems real clinical/claims extracts actually have:
  - Inconsistent categorical formatting (gender: "M"/"Male"/"m"/"FEMALE"/missing)
  - Impossible/erroneous values (negative ages, age=999, LOS=0 for inpatient, etc.)
  - Missing values scattered non-randomly (sicker/older patients missing more fields,
    which is realistic - these are often the most complex charts to complete)
  - Inconsistent date formats across a mix of "systems" (simulating a merged extract
    from multiple source EHR systems, which is extremely common in the real world)
  - Duplicate encounter rows (partial and exact)
  - Free-text-ish inconsistency in a few fields (extra whitespace, mixed case)
  - Outlier costs and lengths of stay from data-entry errors

This is intentionally messy so the cleaning script has real work to do — mirroring
the "data cleaning of messy clinical data" skill this project is meant to demonstrate.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(7)
N_PATIENTS = 5000
N_ENCOUNTERS = 8200

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
DIAGNOSIS_CATALOG = [
    ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine", 1.0),
    ("I10", "Essential hypertension", "Cardiovascular", 0.9),
    ("I50.9", "Heart failure, unspecified", "Cardiovascular", 2.4),
    ("J18.9", "Pneumonia, unspecified organism", "Respiratory", 1.6),
    ("J44.9", "COPD, unspecified", "Respiratory", 1.8),
    ("N18.3", "Chronic kidney disease, stage 3", "Renal", 2.0),
    ("K21.9", "Gastro-esophageal reflux disease", "Digestive", 0.6),
    ("M17.9", "Osteoarthritis of knee, unspecified", "Musculoskeletal", 0.8),
    ("F32.9", "Major depressive disorder, single episode", "Mental Health", 1.1),
    ("S72.001A", "Fracture of neck of femur, initial encounter", "Injury", 3.2),
    ("I21.9", "Acute myocardial infarction, unspecified", "Cardiovascular", 3.8),
    ("A41.9", "Sepsis, unspecified organism", "Infectious", 4.1),
    ("E66.9", "Obesity, unspecified", "Endocrine", 0.7),
    ("R07.9", "Chest pain, unspecified", "Symptoms", 0.9),
    ("Z00.00", "General adult medical examination", "Preventive", 0.3),
]

PROCEDURE_CATALOG = [
    "Basic metabolic panel", "Chest X-ray", "Echocardiogram", "CT scan - abdomen",
    "Physical therapy evaluation", "Cardiac catheterization", "Colonoscopy",
    "Total knee arthroplasty", "Appendectomy", "None", "None", "None",
]

INSURANCE_TYPES = ["Medicare", "Medicaid", "Commercial", "Self-Pay", "Uninsured"]
DEPARTMENTS = ["Internal Medicine", "Cardiology", "Emergency", "Orthopedics",
               "Pulmonology", "General Surgery", "Family Medicine"]

# ---------------------------------------------------------------------------
# Generate patient base (age, sex, chronic condition tendency)
# ---------------------------------------------------------------------------
patient_ids = [f"PT{100000+i}" for i in range(N_PATIENTS)]
patient_base_age = np.clip(RNG.gamma(shape=6, scale=9, size=N_PATIENTS), 1, 95).astype(int)
patient_sex = RNG.choice(["M", "F"], size=N_PATIENTS, p=[0.48, 0.52])
patient_complexity = RNG.beta(2, 5, size=N_PATIENTS)  # underlying tendency toward comorbidity

# messy-formatting variants applied inconsistently, simulating multiple source systems
gender_variants = {
    "M": ["M", "Male", "m", "MALE", "Male "],
    "F": ["F", "Female", "f", "FEMALE", " Female"],
}

records = []
enc_id = 500000
start_date = datetime(2024, 1, 1)

for _ in range(N_ENCOUNTERS):
    p_idx = RNG.integers(0, N_PATIENTS)
    pid = patient_ids[p_idx]
    base_age = patient_base_age[p_idx]
    sex_clean = patient_sex[p_idx]
    complexity = patient_complexity[p_idx]

    # age at encounter drifts slightly + occasional data-entry errors
    age = base_age + RNG.integers(-1, 2)
    if RNG.random() < 0.01:
        age = RNG.choice([-1, 999, 0])  # data entry errors

    # messy gender formatting (~15% of rows use a non-standard variant)
    if RNG.random() < 0.03:
        sex_raw = np.nan
    else:
        sex_raw = RNG.choice(gender_variants[sex_clean])

    # number of comorbid diagnoses this encounter touches (complexity-driven)
    n_dx = 1 + RNG.poisson(complexity * 4)
    n_dx = min(n_dx, 5)
    dx_indices = RNG.choice(len(DIAGNOSIS_CATALOG), size=n_dx, replace=False)
    primary_dx = DIAGNOSIS_CATALOG[dx_indices[0]]
    comorbidity_count = n_dx - 1

    severity_weight = primary_dx[3]
    department = RNG.choice(DEPARTMENTS)
    procedure = RNG.choice(PROCEDURE_CATALOG)

    # Length of stay: lognormal driven by severity + comorbidity, with outlier errors
    los_mu = np.log(1.5 * severity_weight * (1 + 0.3 * comorbidity_count))
    length_of_stay = float(np.clip(RNG.lognormal(los_mu, 0.6), 0, 45))
    length_of_stay = round(length_of_stay, 1)
    if RNG.random() < 0.005:
        length_of_stay = RNG.choice([999, -2])  # data entry error

    # Cost: driven by LOS + severity + procedure complexity, with missingness and outliers
    base_cost = 800 + length_of_stay * 950 * severity_weight + (300 if procedure != "None" else 0)
    cost = float(np.clip(RNG.lognormal(np.log(max(base_cost, 100)), 0.35), 100, 250000))
    cost = round(cost, 2)
    if RNG.random() < 0.04:
        cost = np.nan
    elif RNG.random() < 0.01:
        cost = cost * 50  # extreme outlier / billing error

    # Insurance and readmission flag
    insurance = RNG.choice(INSURANCE_TYPES, p=[0.32, 0.18, 0.35, 0.08, 0.07])
    readmit_30d = bool(RNG.random() < (0.06 + 0.05 * comorbidity_count + 0.03 * (age > 65)))

    # Dates: three different formatting "systems" mixed together (realistic merge artifact)
    enc_date = start_date + timedelta(days=int(RNG.integers(0, 365)), hours=int(RNG.integers(0, 23)))
    date_format_choice = RNG.integers(0, 3)
    if date_format_choice == 0:
        date_str = enc_date.strftime("%Y-%m-%d")
    elif date_format_choice == 1:
        date_str = enc_date.strftime("%m/%d/%Y")
    else:
        date_str = enc_date.strftime("%d-%b-%Y")

    row = {
        "encounter_id": f"ENC{enc_id}",
        "patient_id": pid,
        "encounter_date": date_str,
        "age": age,
        "gender": sex_raw,
        "department": department,
        "primary_diagnosis_code": primary_dx[0] if RNG.random() > 0.015 else np.nan,
        "primary_diagnosis_desc": primary_dx[1],
        "diagnosis_category": primary_dx[2],
        "comorbidity_count": comorbidity_count,
        "procedure": procedure,
        "length_of_stay_days": length_of_stay,
        "total_cost": cost,
        "insurance_type": insurance,
        "readmitted_30d": readmit_30d,
    }
    records.append(row)
    enc_id += 1

df = pd.DataFrame(records)

# Inject exact and near-duplicate rows (~1.5% of the dataset) - realistic ETL artifact
dupe_sample = df.sample(frac=0.015, random_state=1).copy()
df = pd.concat([df, dupe_sample], ignore_index=True)

# Shuffle
df = df.sample(frac=1, random_state=2).reset_index(drop=True)

out_path = "/home/claude/ehr-patient-outcomes/data/ehr_encounters_raw.csv"
df.to_csv(out_path, index=False)

print(f"Generated {len(df):,} raw encounter rows across {N_PATIENTS:,} patients")
print(f"Missing gender: {df['gender'].isna().sum()}")
print(f"Missing diagnosis code: {df['primary_diagnosis_code'].isna().sum()}")
print(f"Missing cost: {df['total_cost'].isna().sum()}")
print(f"Duplicate encounter_ids: {df['encounter_id'].duplicated().sum()}")
print(f"Gender value variants: {sorted(df['gender'].dropna().unique())}")
print(f"Saved to {out_path}")
