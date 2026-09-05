"""
generate_synthetic_data.py
----------------------------
Generates a synthetic population of chronic disease patients with
guideline-recommended screenings/follow-ups, and labels each patient with
whether they went on to miss (fail to complete within the guideline window)
their next-due recommended service.

This mirrors a payer/ACO population health registry: each patient carries
one or more chronic conditions (diabetes, hypertension, CHF, CKD, COPD),
a set of guideline-recommended services with due dates, and utilization/
access features that realistically predict follow-through.

Output: ../data/patients.csv
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_PATIENTS = 15000

# ---------------------------------------------------------------------------
# 1. Chronic conditions and their guideline-recommended services.
#    (Simplified, illustrative mapping -- not clinical guidance.)
# ---------------------------------------------------------------------------
CONDITION_SERVICES = {
    "Diabetes": ["HbA1c test", "Diabetic eye exam", "Diabetic foot exam", "Nephropathy screening"],
    "Hypertension": ["Blood pressure check", "Lipid panel"],
    "CHF": ["Cardiology follow-up", "Weight/fluid check"],
    "CKD": ["Nephrology follow-up", "Nephropathy screening"],
    "COPD": ["Pulmonary follow-up", "Flu/pneumonia vaccination"],
}
ALL_CONDITIONS = list(CONDITION_SERVICES.keys())

# ---------------------------------------------------------------------------
# 2. Patient population generation
# ---------------------------------------------------------------------------
rows = []
for i in range(N_PATIENTS):
    patient_id = f"PT-{100000 + i}"

    age = int(np.clip(RNG.normal(62, 14), 22, 95))
    sex = RNG.choice(["F", "M"])

    # Number of chronic conditions -- weighted so most patients have 1-2
    n_conditions = RNG.choice([1, 2, 3, 4], p=[0.42, 0.33, 0.18, 0.07])
    conditions = list(RNG.choice(ALL_CONDITIONS, size=n_conditions, replace=False))

    # Candidate due services from all held conditions
    candidate_services = sorted(set(s for c in conditions for s in CONDITION_SERVICES[c]))
    # This care-gap episode centers on one specific due/overdue service
    focus_service = RNG.choice(candidate_services)

    insurance = RNG.choice(
        ["Medicare Advantage", "Medicaid MCO", "Commercial", "Dual-eligible"],
        p=[0.34, 0.24, 0.30, 0.12]
    )

    # Access / utilization features
    days_since_last_visit = int(np.clip(RNG.gamma(shape=2.2, scale=45), 7, 540))
    prior_noshow_rate = float(np.clip(RNG.beta(2, 6), 0, 1))  # historical appointment no-show rate
    pdc_medication_adherence = float(np.clip(RNG.beta(5, 2.2), 0.05, 1.0))  # proportion of days covered
    has_transportation_barrier = bool(RNG.random() < (0.22 if insurance in ("Medicaid MCO", "Dual-eligible") else 0.08))
    has_pcp_assigned = bool(RNG.random() < 0.86)
    distance_to_clinic_miles = float(np.clip(RNG.gamma(shape=2.0, scale=6.0), 0.5, 60))
    open_care_gaps_count = int(np.clip(RNG.poisson(1.3), 0, 6))
    telehealth_enrolled = bool(RNG.random() < 0.31)
    reminder_contact_on_file = bool(RNG.random() < 0.78)
    language_barrier_flag = bool(RNG.random() < 0.11)
    days_since_last_reminder_sent = int(np.clip(RNG.exponential(40), 0, 365))

    rows.append({
        "patient_id": patient_id,
        "age": age,
        "sex": sex,
        "insurance_type": insurance,
        "n_chronic_conditions": n_conditions,
        "conditions": "|".join(conditions),
        "focus_service": focus_service,
        "days_since_last_visit": days_since_last_visit,
        "prior_noshow_rate": round(prior_noshow_rate, 3),
        "pdc_medication_adherence": round(pdc_medication_adherence, 3),
        "has_transportation_barrier": has_transportation_barrier,
        "has_pcp_assigned": has_pcp_assigned,
        "distance_to_clinic_miles": round(distance_to_clinic_miles, 1),
        "open_care_gaps_count": open_care_gaps_count,
        "telehealth_enrolled": telehealth_enrolled,
        "reminder_contact_on_file": reminder_contact_on_file,
        "language_barrier_flag": language_barrier_flag,
        "days_since_last_reminder_sent": days_since_last_reminder_sent,
    })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 3. Label generation: missed_next_service (1 = misses the guideline window)
#    Built from a logistic combination of realistic risk factors, then
#    sampled -- so the label is learnable but noisy, like real behavior data.
# ---------------------------------------------------------------------------
logit = (
    -1.05
    + 0.55 * (df["prior_noshow_rate"] > 0.35).astype(int)
    + 1.10 * df["prior_noshow_rate"]
    - 1.35 * df["pdc_medication_adherence"]
    + 0.008 * df["days_since_last_visit"]
    + 0.65 * df["has_transportation_barrier"].astype(int)
    - 0.45 * df["has_pcp_assigned"].astype(int)
    + 0.018 * df["distance_to_clinic_miles"]
    + 0.22 * df["open_care_gaps_count"]
    - 0.40 * df["telehealth_enrolled"].astype(int)
    - 0.35 * df["reminder_contact_on_file"].astype(int)
    + 0.40 * df["language_barrier_flag"].astype(int)
    + 0.006 * df["days_since_last_reminder_sent"]
    + 0.012 * (df["age"] < 45).astype(int) * 10  # younger patients skip more
    - 0.010 * (df["age"] > 75).astype(int) * 10  # oldest patients more compliant (caregiver support)
)
prob_miss = 1 / (1 + np.exp(-logit))
prob_miss = np.clip(prob_miss + RNG.normal(0, 0.05, size=len(df)), 0.02, 0.97)
df["missed_next_service"] = (RNG.random(len(df)) < prob_miss).astype(int)

print(f"Patients generated: {len(df):,}")
print(f"Care-gap miss rate (base rate): {df['missed_next_service'].mean():.1%}")
print("\nMiss rate by insurance type:")
print(df.groupby("insurance_type")["missed_next_service"].mean().round(3))
print("\nMiss rate by focus service:")
print(df.groupby("focus_service")["missed_next_service"].mean().round(3).sort_values(ascending=False))

df.to_csv("../data/patients.csv", index=False)
print("\nSaved to ../data/patients.csv")
