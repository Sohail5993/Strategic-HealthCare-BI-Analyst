# Electronic Health Records (EHR) / Patient Outcomes Analysis

**Category:** Cost & Quality

Explores patterns across demographics, diagnoses, procedures, and outcomes in a synthetic ~8,200-encounter EHR extract — cleaning a genuinely messy clinical dataset first, then identifying which patients are driving disproportionate cost and readmission risk, so a care-management team knows exactly who to call.

**[→ Open the interactive dashboard](./dashboard.html)**

## Headline results

| Metric | Value |
|---|---|
| Share of total spend from just 3.7% of patients | **25%** |
| Readmission rate, cohort vs. everyone else | **47% vs 22.5% (2.1x)** |
| Patients identified for targeted care-management outreach | **149** |

---

## 1. Problem

Most healthcare analyst roles start here: a raw EHR extract that's genuinely messy — inconsistent formatting, missing values, duplicate records, mixed date formats from merged source systems — before any of the interesting demographic, diagnosis, or cost-driver analysis can happen. This project treats that cleaning step as a first-class deliverable, not a throwaway preprocessing script, and then uses the cleaned data to answer a concrete operational question: which patients should a limited-capacity care-management team call first?

## 2. Data

A synthetic dataset of **8,323 raw encounters across 5,000 patients** (`data/ehr_encounters_raw.csv`) was built with realistic clinical data-quality problems on purpose:

- **Gender recorded 10 different ways** (`M`, `Male`, `m`, `MALE`, `"Male "`, and equivalents for female) — simulating a merge across multiple source EHR systems
- **3 mixed date formats** (ISO, MM/DD/YYYY, DD-Mon-YYYY) — another common merged-extract artifact
- **Impossible values**: ages ≤0 or >110, negative or 999-day lengths of stay — classic data-entry errors
- **123 duplicate encounter IDs**
- **Missing values concentrated non-randomly** — gender, diagnosis code, and cost missing at realistic rates (3-4%), not uniformly at random
- **Extreme cost outliers** from likely billing errors

Generator: `scripts/01_generate_raw_ehr_data.py`

## 3. Data cleaning (the core skill this project demonstrates)

`scripts/02_clean_ehr_data.py` produces an analysis-ready dataset **and a full audit trail** of every cleaning decision — because in clinical data work, silently dropping or altering records without a log is a governance problem, not just a coding shortcut.

| Issue | Rows affected | How it was handled |
|---|---|---|
| Duplicate encounter IDs | 123 | Dropped, kept first occurrence |
| Gender formatting (10 variants) | 6,403 | Standardized to M/F |
| Mixed date formats | 8,200 | Parsed into one datetime type |
| Impossible ages | 77 | **Nulled**, not guessed |
| Impossible length-of-stay values | 52 | **Nulled**, not guessed |
| Extreme cost outliers (>3x the 99th percentile) | 27 | **Flagged** for analyst review, not deleted |
| Missing diagnosis code / cost | 125 / 325 | Retained; excluded only from the specific analyses that need that field |

Full log: `output/data_quality_report.csv`. Result: **8,200 clean, analysis-ready rows** from 8,323 raw rows.

## 4. Exploratory analysis

`scripts/03_eda_and_cohort_analysis.py`:

- **Cost by diagnosis category**: Infectious disease ($69,002 avg) and injury-related admissions ($45,113 avg) carry the highest average cost per encounter — an order of magnitude above preventive care ($3,573 avg). ANOVA confirms diagnosis category significantly affects cost (F = 153.8, p < 0.001).
- **Length of stay scales with comorbidity burden**: average LOS rises from 3.03 days (0 comorbidities) to 6.76 days (4 comorbidities) — confirmed with a Kruskal-Wallis test (H = 511.2, p < 0.001).
- **Cost driver model**: a linear model (cost ~ LOS + comorbidity count + age) explains 43% of cost variation (R² = 0.43). Length of stay is the dominant lever (+$3,539/day). Comorbidity count shows a *negative* coefficient (−$829) once LOS is already in the model — not an error, but a sign that comorbidity's effect on cost runs mainly *through* length of stay (correlation 0.66 with LOS vs. only 0.11 directly with cost).

## 5. Cohort identification

**Definition:** annual cost ≥ 90th percentile ($60,345) **and** at least 3 comorbidities on any encounter.

| | Cohort | Everyone else |
|---|---|---|
| Patients | 149 (3.7%) | 3,873 (96.3%) |
| Share of total spend | **25.0%** | 75.0% |
| 30-day readmission rate | **47.0%** | 22.5% |
| Avg age | 54.8 | — |

This is a classic long-tail cost distribution: a small, identifiable group of patients accounts for a disproportionate share of both spend and readmission risk — exactly the group a capacity-constrained outreach program should prioritize first.

## 6. Recommendations

1. **Target the 149-patient cohort first.** They represent 25% of spend and nearly half are readmitted within 30 days — the highest-leverage group for a capacity-constrained care-management team.
2. **Treat length of stay as the primary cost lever**, not comorbidity count directly — discharge planning and case management for complex patients likely has more direct cost impact than comorbidity-focused programs alone.
3. **Fix data capture at the source** for gender, age, and LOS fields — the standardization work here is a recurring cost of upstream data-entry inconsistency, not a one-time cleanup.
4. **Re-run the cohort definition quarterly** — patients move in and out of the high-cost/high-complexity group as conditions resolve or progress.

## Repo structure

```
ehr-patient-outcomes/
├── README.md
├── dashboard.html
├── data/
│   ├── ehr_encounters_raw.csv
│   └── ehr_encounters_clean.csv
├── scripts/
│   ├── 01_generate_raw_ehr_data.py
│   ├── 02_clean_ehr_data.py
│   └── 03_eda_and_cohort_analysis.py
├── output/
│   ├── data_quality_report.csv
│   ├── diagnosis_category_summary.csv
│   ├── los_by_comorbidity.csv
│   ├── patient_level_summary.csv
│   └── high_cost_complex_cohort.csv
└── images/
    ├── cost_by_diagnosis.png
    ├── los_by_comorbidity.png
    ├── cost_concentration.png
    └── readmit_comparison.png
```

## Tools

Python (pandas, numpy, scipy, python-dateutil) for data generation, cleaning, and statistical testing; Chart.js for the dashboard. The cleaned dataset (`ehr_encounters_clean.csv`) and summary CSVs drop directly into Power BI, Tableau, or SQL for further analysis.

## Limitations

This uses a synthetic dataset built to mimic realistic EHR data-quality problems and clinical relationships (age, comorbidity, LOS, and cost interactions), not real patient records. The specific dollar figures, rates, and thresholds are illustrative of the method, not a claim about any real population. In a production setting, the cohort definition's thresholds (90th percentile cost, ≥3 comorbidities) would be tuned against the care-management team's actual outreach capacity rather than fixed arbitrarily.
