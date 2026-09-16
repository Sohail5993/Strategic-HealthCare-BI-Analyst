# Predicting Length of Stay and Cost of Care at Admission

**A synthetic-data case study in early identification of high-cost, long-stay hospital admissions.**

## The business problem

Hospitals lose money and beds in predictable ways: a small share of patients account for a
disproportionate share of cost, and long-stay patients are usually identifiable early — if anyone
is looking. Two operational questions drive this project:

1. **Capacity planning** — which admissions are likely to become long stays, so discharge
   planning and bed management can start on day one instead of day seven?
2. **Financial forecasting** — which admissions are likely to be expensive, so care management
   and utilization review can prioritize the right patients?

This project builds an end-to-end pipeline — SQL data modeling → exploratory analysis → machine
learning → BI dashboard — to answer both questions using only information available **at the
moment of admission**, since that's the only point at which a prediction is operationally useful.

## Data & ethics note

All data is synthetic, generated with [Synthea](https://github.com/synthetichealth/synthea) (500
simulated Massachusetts patients). No real patient data was used at any stage — there is no PHI and
no HIPAA scope here. That said, the pipeline is built as if it eventually needs to meet that bar:
feature engineering is scoped to admission-time information, and a fairness check is included
below rather than treated as an afterthought. A production version of this project on real EHR
data would require de-identification per HIPAA Safe Harbor or Expert Determination before any of
this analysis could run.

## Repo structure

```
/sql          -- staging + star schema, feature engineering, window-function analytics queries
/notebooks    -- eda_notebook.ipynb, modeling_notebook.ipynb (both fully executed, real outputs)
/data         -- model_features.csv, model_predictions.csv, fact_encounters.csv, dim_date.csv
/dashboard    -- Power BI build guide, DAX measures, data exports
README.md     -- this file
```

## Methodology at a glance

| Stage | What was built | Tooling |
|---|---|---|
| Data modeling | Star schema (`dim_patients`, `dim_payers`, `fact_encounters`) + a wide `model_features` table, admission-time features only | PostgreSQL-dialect SQL, validated end-to-end in DuckDB |
| Exploratory analysis | 10-section EDA notebook: distributions, skew, cost concentration, comorbidity/LOS relationship, readmission patterns | Python (pandas, seaborn) |
| Modeling | LOS regression, extended-stay classification, cost regression — baseline vs. XGBoost, SHAP explainability | scikit-learn, XGBoost, SHAP |
| Dashboard | Capacity / Cost / Model Performance pages | Power BI (DAX measures + build guide provided) |

**A modeling decision that shapes everything downstream:** features that are only known *during*
a stay — procedures performed, new diagnoses made mid-visit — are deliberately excluded from the
admission-time model, even though including them barely changed accuracy on this particular
synthetic sample (MAE 0.330 vs. 0.291 days — see Modeling below). A model that "predicts" LOS
using information from partway through the stay isn't deployable at the decision point that
matters. This is stated explicitly rather than buried, because it's the difference between a
model that works in a demo and one that works in production.

## Key EDA findings

- **LOS and cost are both heavily right-skewed** (LOS skewness 5.31 raw, cost even more so — mean
  cost $5,267 against a $216,090 maximum). Both were modeled on a `log1p()` transform for this
  reason.
- **LOS and cost correlate at 0.67** — related but not interchangeable; a short stay with heavy
  procedures can still be expensive, which is part of why the cost model underperforms the LOS
  model (see below).
- **Cost is concentrated**: the top cost decile accounts for **78.4%** of total spend across the
  4,415 admission-type encounters — the classic healthcare-analytics finding that supports
  targeting a small patient segment for care management rather than spreading resources evenly.
- **Comorbidity count correlates with LOS for inpatient encounters** (r = 0.18) — a real but modest
  relationship, consistent with clinical intuition without being a magic predictor on its own.
- **Encounter type matters enormously**: inpatient stays behave completely differently from
  emergency/urgent-care visits, which are near-zero LOS by definition. The dashboard and models
  both treat `encounterclass` as a first-class feature rather than pooling all encounter types as
  if they were comparable.

## Modeling results — reported honestly

### LOS regression (target: `log1p(los_days)`, back-transformed to days)

| Model | MAE (days) | RMSE (days) | R² (log scale) |
|---|---|---|---|
| Linear Regression (baseline) | 0.385 | 1.618 | 0.617 |
| XGBoost | **0.330** | 1.640 | 0.668 |

XGBoost improves MAE by 14.4% over the linear baseline. RMSE is roughly flat between the two —
expected, since RMSE penalizes the long tail of complex stays that neither model fully captures on
a sample this size.

### Extended-stay classification (target: `LOS > 7 days`, ~3% of admissions)

| Model | ROC-AUC | PR-AUC |
|---|---|---|
| Logistic Regression (baseline) | 0.926 | 0.139 |
| XGBoost | **0.942** | **0.174** |

ROC-AUC looks strong for both models — but with a positive class this rare, **PR-AUC is the more
honest number**, and 0.174 reflects how hard this problem genuinely is with ~4,400 rows and 16
positive cases in the test set. At an operating threshold chosen to prioritize recall (missing a
long-stay patient costs more than an unnecessary review):

- **81% recall** — catches 13 of 16 true extended-stay cases in the test set
- **15% precision** — flags 84 of 909 test encounters (9.2%) for review to find those 13
- This is a genuinely usable **screening tool**, not a diagnostic one: it's built to cast a wide
  net cheaply, not to be trusted at the individual-patient level.

### Cost regression — flagged as the weakest model, on purpose

| Metric | Value |
|---|---|
| MAE | $1,975 |
| Mean actual cost (test set) | $2,563 |
| MAE as % of mean cost | **77.1%** |

This model is weak, and the EDA already explained why: cost is driven heavily by *what happens
during* an encounter (procedures, imaging, medications) — information an admission-time-only
model can't see by design. The honest framing is that this cost model is useful for **relative
triage** (ranking patients by predicted-cost decile) rather than **dollar-precise forecasting**.
Reporting a misleadingly small error here would have been easy and wrong.

## Business impact translation

Using the chosen classifier threshold and this test set's actual cost gap between extended and
non-extended stays ($56,311 vs. $3,681 average — a $52,630 gap):

> If early discharge-planning intervention on flagged patients reduced their excess LOS-driven
> cost by even 15%, that's roughly **$7,895 saved per correctly-flagged extended-stay encounter** —
> scaled to the 13 true positives in this test set alone, **~$102,629**.

**This is illustrative, not a guaranteed outcome.** The 15% intervention-effectiveness figure is an
assumption, not something measured in this data — a real deployment would need a pilot program or
a literature-backed effectiveness estimate before this number goes in front of a budget committee.

## Fairness — a concrete finding, not a disclaimer

SHAP analysis of the extended-stay classifier surfaced non-trivial influence from **race** on
predictions. This wasn't something we set out looking for — it showed up in the feature-importance
output, and it's reported here for that reason. It doesn't necessarily mean the model is unfairly
biased against this synthetic population, but it is a **specific, concrete audit trigger**: before
any real deployment, error rates should be compared across race, ethnicity, and payer-type
subgroups to check for disparate false-negative or false-positive rates. This is included as an
explicit next step below rather than a generic "we care about fairness" statement.

## Dashboard

Three Power BI pages (Capacity, Cost, Model Performance) built on `fact_encounters.csv`,
`model_predictions_bi.csv`, and a `dim_date` date table — full build guide and DAX measures in
`/dashboard`. One data quirk worth knowing: Synthea simulates a patient's entire lifetime, so a
small number of encounters date back to the 1930s–1990s. Trend visuals filter to `Year >= 2016`
(covering 67% of encounters) rather than let that long tail flatten the charts.

## Limitations

1. **Small sample for a rare event** — 500 synthetic patients / 4,415 admission encounters, with
   only 16 positive extended-stay cases in the test set. Treat all point-estimate metrics above as
   directional, not final; confidence intervals on the classifier's precision/recall would be wide.
2. **Synthetic-data ceiling** — Synthea's generative rules don't reproduce every real-world
   correlation. The 30-day readmission rate in this data is **49%**, far above the real-world
   10–20% range — traced to a small number of synthetic "high-utilizer" patients with unusually
   frequent encounters. This is disclosed rather than smoothed into the narrative.
3. **Single synthetic population** — no cross-facility or cross-region variation, so nothing here
   has been tested for generalization across different care settings.
4. **Cost model is directionally useful only** — see Modeling above. Don't present the $1,975 MAE
   without the 77% relative-error context next to it.
5. **Fairness check flagged, not completed** — the SHAP finding above is a to-do, not a clean bill
   of health.

## What would come next

- Regenerate at a larger population size (2,000–5,000 patients) to stabilize the extended-stay
  classifier's precision estimate.
- Run the fairness subgroup analysis flagged above before treating this as deployment-ready.
- Validate the pipeline against a real de-identified dataset (e.g., MIMIC-IV) to check whether the
  admission-time feature set holds up outside Synthea's generative assumptions.
- Pilot the discharge-planning intervention itself to replace the 15% effectiveness assumption
  with a measured number.

---

*Built with Synthea, PostgreSQL/DuckDB, Python (pandas, scikit-learn, XGBoost, SHAP), and Power BI.
All data synthetic — no PHI.*
