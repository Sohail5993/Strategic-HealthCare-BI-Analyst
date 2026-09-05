# Care-Gap Prediction for Chronic Disease Management

**Identifying patients likely to miss recommended screenings or follow-ups, to close gaps before they become costly complications.**

*Strategic HealthCare BI Analyst Portfolio Project — Sohail*

## The problem

Chronic disease management runs on guideline-recommended screenings and follow-ups — HbA1c
tests, diabetic eye and foot exams, nephropathy screening, lipid panels, cardiology and
pulmonary follow-ups. When a patient misses one, the miss is usually silent until it turns
into a complication: diabetic retinopathy that could have been caught early, a CKD patient
who progresses further before the next visit, a heart failure patient re-hospitalized after a
missed weight/fluid check. A care-management team can only proactively call a fraction of an
open care-gap registry each cycle — so the real question isn't "who has an open gap," it's
"who is actually going to miss it if we don't call first."

## The approach

A synthetic population of 15,000 chronic disease patients (diabetes, hypertension, CHF, CKD,
COPD) was built with realistic utilization, adherence, and access features — appointment
no-show history, medication adherence (proportion of days covered), transportation barriers,
telehealth enrollment, reminder contact and timing, and distance to clinic. Three models
(logistic regression, random forest, XGBoost) were trained to predict whether a patient will
miss their next guideline-due service, with class imbalance handled via class weighting
rather than resampling to keep predicted probabilities trustworthy for risk-tiering. Models
were compared on precision at realistic outreach-capacity thresholds (top 10–20% of the
panel), not just ROC-AUC, since that's what determines whether a limited-capacity outreach
program actually reaches the right patients. SHAP explanations were layered on top so a care
coordinator can see *why* a specific patient was flagged.

## The result

The best model (logistic regression) reached **0.716 ROC-AUC** and **0.583 PR-AUC**, with
**70% precision in the top 10% highest-risk tier** against a 34.6% base rate — a 2x lift.
The top SHAP drivers — days since last visit, prior no-show history, reminder staleness,
number of open care gaps, and medication adherence — are almost entirely operational levers,
not clinical severity markers, meaning most of this gap is closeable through outreach timing
and channel rather than requiring a different care plan. Simulating an outreach program
targeted at just the top 5% highest-risk patients produced the best return of any capacity
tier tested: **6.40x ROI**, an estimated **$878K in annual net savings** for a 50,000-patient
chronic disease panel.

| Metric | Value |
|---|---|
| Best ROC-AUC (Logistic Regression) | 0.716 |
| Best PR-AUC | 0.583 |
| Precision @ top 10% risk tier | 70.0% vs. 34.6% base rate (2x lift) |
| Best ROI tier | 5% capacity — 6.40x ROI |
| Est. annual net savings (50K-patient panel, top 5% tier) | $878K |

See `reports/Care_Gap_Prediction_One_Pager.pdf` for the full model comparison, SHAP risk
drivers, cost/ROI simulation across capacity tiers, key modeling decisions, and honest
limitations.

## Repository structure

```
chronic-disease-care-gap-prediction/
├── README.md
├── data/
│   └── patients.csv                    # 15,000 synthetic chronic disease patients
├── src/
│   ├── feature_engineering.py          # Encoding, feature construction, train/test split
│   ├── train_pipeline.py               # Trains and compares the three models
│   ├── evaluate.py                     # ROC/PR curves, confusion matrix
│   ├── shap_interactions.py            # SHAP beeswarm + bar chart, feature importance
│   └── cost_impact.py                  # ROI/net-savings simulation by outreach capacity
├── scripts/
│   └── generate_synthetic_data.py      # Synthetic population + label generator
├── models/
│   └── best_care_gap_model.joblib      # Best model + test split + predictions
├── reports/
│   ├── build_one_pager.py              # Builds the branded PDF one-pager
│   ├── Care_Gap_Prediction_One_Pager.pdf
│   ├── figures/                        # ROC/PR curves, confusion matrix, SHAP plots, ROI chart
│   └── metrics/                        # metrics.json, model comparison, SHAP importances, cost/impact CSVs
```

## How to run

```bash
cd scripts && python3 generate_synthetic_data.py    # regenerates data/patients.csv
cd ../src
python3 train_pipeline.py     # trains + compares models, saves best model
python3 evaluate.py           # ROC/PR curves + confusion matrix
python3 shap_interactions.py  # SHAP explainability charts
python3 cost_impact.py        # ROI simulation by outreach capacity
cd ../reports && python3 build_one_pager.py   # builds the PDF one-pager
```

Requires: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `shap`, `matplotlib`, `reportlab`.

## Key modeling decisions

- **Precision@K over ROC-AUC alone** — an outreach team can only call a fixed share of the
  panel each cycle, so precision at the 10–20% capacity threshold reflects what matters
  operationally: how often the flagged list is actually right.
- **Target label matches the guideline window exactly** — "missed next service" is defined
  against each condition's specific guideline window (e.g., annual eye exam, semi-annual
  HbA1c), not a generic 30/60/90-day cutoff, so the label means what a real care-gap registry
  would flag.
- **Class weighting over resampling** — imbalance (34.6% positive rate) was handled via
  `class_weight="balanced"` rather than synthetic oversampling, to keep predicted
  probabilities calibrated for risk-tiering.

## Honest limitations & next steps

Risk-factor directions (no-show history, adherence, reminder timing) reflect published
care-gap and appointment-adherence literature, but the specific coefficients are illustrative,
not fit to a real patient population. Before production deployment: validate against an
actual care-gap registry with a temporal (not random) holdout, confirm the outreach
relative-risk-reduction assumption (35%) against the specific program's own pilot data, and
audit for disparate impact across insurance type and language-access subgroups before setting
enrollment thresholds.

## Data disclaimer

All patient data in this project is synthetically generated for portfolio demonstration and
contains no real patient records.

---
**Contact:** strategichealthcarebianalyst@gmail.com | [LinkedIn](https://linkedin.com/in/aimms-consulting-35895439) | [Portfolio](https://sohail5993.github.io/Strategic-HealthCare-BI-Analyst/)
