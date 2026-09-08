"""
generate_claims_data.py
------------------------
Generates a realistic SYNTHETIC healthcare claims dataset for the
Strategic Healthcare BI Analyst portfolio project.

No real patient, provider, or payer data is used. Reason codes follow
the real CMS Claim Adjustment Reason Code (CARC) format/spirit, but all
volumes, dollar amounts, and identifiers are simulated.

The data is deliberately generated with a few embedded "root causes"
so that the downstream SQL / Tableau analysis has real signal to find:

  1. A managed-care payer ("Meridian Health Plan") tightens prior-authorization
     requirements starting 2025-01-01, causing a spike in CO-197
     (Authorization) denials for Orthopedics and Oncology from that date on.
  2. Behavioral Health has a chronically elevated CO-50 (Medical Necessity)
     denial rate due to inconsistent documentation practices.
  3. One facility ("East Medical Center") has weaker front-end eligibility
     verification, driving up CO-22 / CO-109 (Eligibility) denials there
     versus other facilities.
  4. Government payers (Medicare/Medicaid) have longer turnaround times
     than commercial payers.

Output: data/claims.csv (fact table, one row per claim)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N_CLAIMS = 9000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 6, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

# ---------------------------------------------------------------------------
# Dimension pools
# ---------------------------------------------------------------------------

PAYERS = [
    # (payer_name, payer_type, base_denial_rate, reimbursement_ratio, avg_turnaround_days)
    ("Medicare",              "Government", 0.13, 0.55, 24),
    ("Medicaid",              "Government", 0.19, 0.45, 29),
    ("Aetna",                 "Commercial", 0.11, 0.72, 16),
    ("UnitedHealthcare",      "Commercial", 0.12, 0.70, 15),
    ("Cigna",                 "Commercial", 0.10, 0.74, 14),
    ("Blue Cross Blue Shield","Commercial", 0.11, 0.71, 17),
    ("Meridian Health Plan",  "Managed Care", 0.14, 0.66, 20),   # policy change payer
    ("Self-Pay",              "Self-Pay",   0.22, 0.30, 35),
]
PAYER_NAMES = [p[0] for p in PAYERS]

SERVICE_LINES = [
    # (service_line, base_denial_rate multiplier, avg_billed_amount)
    ("Emergency Medicine", 1.00, 2400),
    ("Internal Medicine",  0.85, 1200),
    ("Cardiology",         1.10, 6800),
    ("Orthopedics",        1.15, 9200),
    ("Radiology",          0.95, 1800),
    ("Oncology",           1.25, 14500),
    ("General Surgery",    1.05, 11800),
    ("OB/GYN",             0.90, 4200),
    ("Pediatrics",         0.80, 1600),
    ("Behavioral Health",  1.30, 1900),
]
SERVICE_LINE_NAMES = [s[0] for s in SERVICE_LINES]

FACILITIES = ["Main Campus", "North Clinic", "South Clinic", "East Medical Center"]
FACILITY_WEIGHTS = [0.45, 0.20, 0.20, 0.15]

DENIAL_REASONS = [
    # (code, description, category)
    ("CO-16",  "Claim/service lacks information needed for adjudication", "Missing Information"),
    ("CO-18",  "Duplicate claim/service",                                  "Duplicate Claim"),
    ("CO-22",  "Coordination of benefits / other payer responsible",       "Eligibility"),
    ("CO-29",  "Timely filing limit expired",                              "Timely Filing"),
    ("CO-50",  "Non-covered service - not deemed a medical necessity",     "Medical Necessity"),
    ("CO-97",  "Benefit included in payment for another service",         "Bundling"),
    ("CO-109", "Claim not covered by this payer/contractor",              "Eligibility"),
    ("CO-11",  "Diagnosis inconsistent with procedure",                   "Coding Error"),
    ("CO-197", "Precertification/authorization absent",                  "Authorization"),
    ("CO-45",  "Charge exceeds fee schedule/contracted amount",           "Contractual"),
]
REASON_LOOKUP = {c[0]: (c[1], c[2]) for c in DENIAL_REASONS}

PROVIDERS = [f"PROV-{i:03d}" for i in range(1, 61)]
PATIENTS = [f"PAT-{i:05d}" for i in range(1, 4001)]

CPT_BY_SERVICE_LINE = {
    "Emergency Medicine": ["99283", "99284", "99285"],
    "Internal Medicine":  ["99213", "99214", "99215"],
    "Cardiology":         ["93000", "93306", "92928"],
    "Orthopedics":        ["27447", "29881", "20610"],
    "Radiology":          ["70450", "72148", "71046"],
    "Oncology":           ["96413", "77301", "96415"],
    "General Surgery":    ["44970", "47562", "49505"],
    "OB/GYN":             ["59400", "58150", "76805"],
    "Pediatrics":         ["99392", "99391", "90460"],
    "Behavioral Health":  ["90837", "90853", "90791"],
}

ICD10_BY_SERVICE_LINE = {
    "Emergency Medicine": ["R07.9", "S09.90XA", "R10.9"],
    "Internal Medicine":  ["I10", "E11.9", "J45.909"],
    "Cardiology":         ["I25.10", "I48.91", "I50.9"],
    "Orthopedics":        ["M17.11", "S83.511A", "M54.5"],
    "Radiology":          ["R91.8", "R93.1", "R94.31"],
    "Oncology":           ["C50.911", "C34.90", "C18.9"],
    "General Surgery":    ["K80.20", "K35.80", "K40.90"],
    "OB/GYN":             ["O80", "N92.0", "Z34.90"],
    "Pediatrics":         ["Z00.129", "J06.9", "H66.90"],
    "Behavioral Health":  ["F32.9", "F41.1", "F43.10"],
}

# ---------------------------------------------------------------------------
# Build claims
# ---------------------------------------------------------------------------

rows = []
payer_lookup = {p[0]: p for p in PAYERS}
sl_lookup = {s[0]: s for s in SERVICE_LINES}

for i in range(1, N_CLAIMS + 1):
    claim_id = f"CLM-{i:06d}"
    offset_days = int(rng.integers(0, TOTAL_DAYS))
    service_date = START_DATE + timedelta(days=offset_days)
    submission_lag = int(rng.integers(1, 10))
    submission_date = service_date + timedelta(days=submission_lag)

    payer_name = rng.choice(PAYER_NAMES, p=[0.16, 0.14, 0.13, 0.13, 0.11, 0.12, 0.11, 0.10])
    _, payer_type, payer_base_denial, reimb_ratio, avg_turnaround = payer_lookup[payer_name]

    service_line = rng.choice(SERVICE_LINE_NAMES)
    _, sl_multiplier, avg_billed = sl_lookup[service_line]

    facility = rng.choice(FACILITIES, p=FACILITY_WEIGHTS)

    provider_id = rng.choice(PROVIDERS)
    patient_id = rng.choice(PATIENTS)

    cpt_code = rng.choice(CPT_BY_SERVICE_LINE[service_line])
    icd10_code = rng.choice(ICD10_BY_SERVICE_LINE[service_line])

    billed_amount = round(float(rng.gamma(shape=4.0, scale=avg_billed / 4.0)), 2)
    billed_amount = max(billed_amount, 75.0)

    # ---- Denial probability model -----------------------------------
    denial_prob = payer_base_denial * sl_multiplier

    # Root cause 1: Meridian Health Plan tightens prior auth 2025-01-01+
    # for Orthopedics and Oncology -> big jump in Authorization denials
    meridian_auth_spike = (
        payer_name == "Meridian Health Plan"
        and service_line in ("Orthopedics", "Oncology")
        and submission_date >= datetime(2025, 1, 1)
    )
    if meridian_auth_spike:
        denial_prob += 0.28

    # Root cause 2: Behavioral Health chronically elevated (already
    # captured via sl_multiplier=1.30, add a bit more)
    if service_line == "Behavioral Health":
        denial_prob += 0.03

    # Root cause 3: East Medical Center weaker eligibility verification
    if facility == "East Medical Center":
        denial_prob += 0.05

    denial_prob = float(np.clip(denial_prob, 0.02, 0.75))
    is_denied_first_pass = rng.random() < denial_prob

    # ---- Denial reason assignment (weighted by root-cause context) ---
    denial_reason_code = None
    denial_reason_desc = None
    denial_category = None

    if is_denied_first_pass:
        if meridian_auth_spike:
            reason_weights = {
                "CO-197": 0.55, "CO-16": 0.12, "CO-50": 0.10, "CO-22": 0.08,
                "CO-29": 0.05, "CO-97": 0.04, "CO-109": 0.02, "CO-11": 0.02,
                "CO-18": 0.01, "CO-45": 0.01,
            }
        elif service_line == "Behavioral Health":
            reason_weights = {
                "CO-50": 0.40, "CO-16": 0.15, "CO-197": 0.12, "CO-22": 0.08,
                "CO-29": 0.08, "CO-97": 0.05, "CO-109": 0.04, "CO-11": 0.04,
                "CO-18": 0.02, "CO-45": 0.02,
            }
        elif facility == "East Medical Center":
            reason_weights = {
                "CO-22": 0.30, "CO-109": 0.22, "CO-16": 0.14, "CO-197": 0.10,
                "CO-29": 0.08, "CO-50": 0.06, "CO-97": 0.04, "CO-11": 0.03,
                "CO-18": 0.02, "CO-45": 0.01,
            }
        else:
            reason_weights = {
                "CO-16": 0.20, "CO-22": 0.14, "CO-29": 0.13, "CO-50": 0.13,
                "CO-197": 0.12, "CO-97": 0.09, "CO-109": 0.07, "CO-11": 0.06,
                "CO-18": 0.04, "CO-45": 0.02,
            }
        codes = list(reason_weights.keys())
        weights = np.array(list(reason_weights.values()))
        weights = weights / weights.sum()
        denial_reason_code = rng.choice(codes, p=weights)
        denial_reason_desc, denial_category = REASON_LOOKUP[denial_reason_code]

    # ---- Resubmission / final outcome ---------------------------------
    is_resubmitted = False
    resubmission_count = 0
    final_status = "Paid"
    paid_amount = 0.0
    turnaround_days = 0

    base_turnaround = max(3, int(rng.normal(avg_turnaround, 5)))

    if not is_denied_first_pass:
        final_status = "Paid"
        paid_amount = round(billed_amount * reimb_ratio * float(rng.uniform(0.94, 1.02)), 2)
        turnaround_days = base_turnaround
    else:
        # Some denials never get worked / appealed -> stay denied (written off)
        # Non-appealable categories (timely filing, duplicate) almost never recovered
        if denial_category in ("Timely Filing", "Duplicate Claim"):
            recovery_prob = 0.05
        elif denial_category == "Authorization":
            recovery_prob = 0.55
        elif denial_category == "Eligibility":
            recovery_prob = 0.40
        elif denial_category == "Medical Necessity":
            recovery_prob = 0.35
        else:
            recovery_prob = 0.50

        is_resubmitted = rng.random() < (recovery_prob + 0.15)  # attempt rate slightly higher than recovery
        if is_resubmitted:
            resubmission_count = int(rng.integers(1, 3))
            recovered = rng.random() < recovery_prob
            extra_cycle_days = int(rng.integers(15, 45)) * resubmission_count
            turnaround_days = base_turnaround + extra_cycle_days
            if recovered:
                final_status = "Paid"
                paid_amount = round(billed_amount * reimb_ratio * float(rng.uniform(0.90, 1.00)), 2)
            else:
                final_status = "Denied - Written Off"
                paid_amount = 0.0
        else:
            final_status = "Denied - Written Off"
            paid_amount = 0.0
            turnaround_days = base_turnaround + int(rng.integers(5, 15))

    # Small % still pending / in appeal as of data pull
    if submission_date >= datetime(2025, 6, 1) and is_denied_first_pass and rng.random() < 0.35:
        final_status = "Pending Appeal"
        paid_amount = 0.0

    is_clean_claim = not is_denied_first_pass

    rows.append({
        "claim_id": claim_id,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "facility": facility,
        "payer_name": payer_name,
        "payer_type": payer_type,
        "service_line": service_line,
        "cpt_code": cpt_code,
        "icd10_code": icd10_code,
        "date_of_service": service_date.strftime("%Y-%m-%d"),
        "claim_submission_date": submission_date.strftime("%Y-%m-%d"),
        "billed_amount": billed_amount,
        "paid_amount": paid_amount,
        "is_clean_claim": is_clean_claim,
        "first_pass_status": "Denied" if is_denied_first_pass else "Paid",
        "denial_reason_code": denial_reason_code,
        "denial_reason_description": denial_reason_desc,
        "denial_category": denial_category,
        "is_resubmitted": is_resubmitted,
        "resubmission_count": resubmission_count,
        "final_status": final_status,
        "turnaround_days": turnaround_days,
    })

df = pd.DataFrame(rows)
df.sort_values("claim_submission_date", inplace=True)
df.reset_index(drop=True, inplace=True)

out_path = "/home/claude/healthcare-bi/data/claims.csv"
df.to_csv(out_path, index=False)

print(f"Wrote {len(df):,} rows to {out_path}")
print("\n--- Quick sanity check ---")
print("Overall denial rate:", round((df.first_pass_status == "Denied").mean() * 100, 2), "%")
print("Overall clean claim rate:", round(df.is_clean_claim.mean() * 100, 2), "%")
print("\nDenial rate by payer:")
print((df.first_pass_status == "Denied").groupby(df.payer_name).mean().sort_values(ascending=False).round(3))
print("\nMeridian Ortho/Onc denial rate before vs after 2025-01-01:")
m = df[(df.payer_name == "Meridian Health Plan") & (df.service_line.isin(["Orthopedics", "Oncology"]))].copy()
m["period"] = np.where(m.claim_submission_date >= "2025-01-01", "After", "Before")
print((m.first_pass_status == "Denied").groupby(m.period).mean().round(3))
