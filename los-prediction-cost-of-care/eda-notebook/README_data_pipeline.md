# Data Pipeline: How This Was Built

1. **Generate synthetic data**: `java -jar synthea-with-dependencies.jar --exporter.csv.export=true -p 500 Massachusetts`
   Produces raw EHR-style CSVs (patients, encounters, conditions, procedures, medications, payers).

2. **Run the SQL pipeline** (`/sql`), in order:
   - `01_schema.sql` — staging tables + star schema (dim_patients, dim_payers, fact_encounters)
   - `02_feature_engineering.sql` — builds `model_features`, one row per admission-type encounter
   - `03_analytics_queries.sql` — standalone window-function queries for the case study / dashboard

   Written for PostgreSQL. This was validated end-to-end using DuckDB (same ANSI SQL, zero server
   setup) against the generated Synthea data — see `notebooks/eda_notebook.ipynb` for the executed
   output.

3. **`data/model_features.csv`** is the exported output of step 2 — 4,415 admission-type encounters
   (emergency/inpatient/urgentcare) with engineered features, ready to load into the Python notebook.

4. **`notebooks/eda_notebook.ipynb`** — executed EDA notebook (real Synthea data, real rendered
   plots) covering target distributions, cost concentration, comorbidity/LOS relationship, and the
   prior-admission → readmission-risk finding.

## Key EDA findings (feeding the modeling stage)
- LOS and cost are both right-skewed → model on `log1p()` transforms.
- Inpatient encounters behave very differently from ED/urgent care → consider separate models.
- 30-day readmission rate rises sharply with prior admission count (0% → ~59% for 6+ priors) — a
  concrete, data-backed hook for a care-management recommendation.
- Extended stays (>7 days) are ~3% of admissions — classification model will need class weighting.
