-- ============================================================================
-- FILE: 02_feature_engineering.sql
-- PROJECT: Length-of-Stay / Cost-of-Care Prediction
-- DIALECT: PostgreSQL 14+
-- PURPOSE: Build a single wide table, one row per admission-eligible
--          encounter, with every feature the model needs. This is the table
--          you export to CSV/Parquet and load into the Python notebook.
--
-- Scope: we model only encounters that represent an actual "stay"
--        (emergency, inpatient, urgentcare) since LOS is meaningless for a
--        same-day wellness visit.
-- ============================================================================

DROP TABLE IF EXISTS analytics.model_features;

CREATE TABLE analytics.model_features AS

WITH admissions AS (
    -- Restrict to encounter types where LOS/cost prediction is actually
    -- clinically meaningful.
    SELECT *
    FROM analytics.fact_encounters
    WHERE encounterclass IN ('emergency', 'inpatient', 'urgentcare')
),

-- ---------------------------------------------------------------
-- Comorbidity burden at time of admission: count of DISTINCT active
-- conditions the patient carried into this encounter (diagnosed on or
-- before admission start, not yet resolved).
-- ---------------------------------------------------------------
comorbidity_counts AS (
    SELECT
        a.encounter_id,
        COUNT(DISTINCT c.code) AS comorbidity_count
    FROM admissions a
    JOIN staging.conditions c
      ON c.patient_id = a.patient_id
     AND c.start_date <= a.start_ts::date
     AND (c.stop_date IS NULL OR c.stop_date >= a.start_ts::date)
    GROUP BY a.encounter_id
),

-- ---------------------------------------------------------------
-- Conditions diagnosed specifically AT this encounter (severity signal,
-- e.g. how many new problems were found during work-up).
-- ---------------------------------------------------------------
new_conditions_this_visit AS (
    SELECT
        encounter_id,
        COUNT(DISTINCT condition_code) AS new_conditions_count
    FROM analytics.bridge_encounter_conditions
    GROUP BY encounter_id
),

-- ---------------------------------------------------------------
-- Procedure volume performed during this encounter (proxy for
-- clinical complexity/intensity of the stay).
-- ---------------------------------------------------------------
procedure_counts AS (
    SELECT
        encounter_id,
        COUNT(DISTINCT procedure_code) AS procedure_count
    FROM analytics.bridge_encounter_procedures
    GROUP BY encounter_id
),

-- ---------------------------------------------------------------
-- Prior utilization history: how many admissions this patient had
-- BEFORE this one, and how many days since their last discharge.
-- This is one of the strongest real-world LOS/readmission predictors.
-- ---------------------------------------------------------------
prior_utilization AS (
    SELECT
        a.encounter_id,
        COUNT(prior.encounter_id) AS prior_admission_count,
        MAX(prior.stop_ts)        AS last_discharge_ts
    FROM admissions a
    LEFT JOIN admissions prior
           ON prior.patient_id = a.patient_id
          AND prior.stop_ts < a.start_ts
    GROUP BY a.encounter_id
),

-- ---------------------------------------------------------------
-- Medication burden in the 90 days prior to admission (polypharmacy
-- proxy — higher counts often correlate with more complex stays).
-- ---------------------------------------------------------------
recent_medication_counts AS (
    SELECT
        a.encounter_id,
        COUNT(DISTINCT m.code) AS meds_last_90_days
    FROM admissions a
    LEFT JOIN staging.medications m
           ON m.patient_id = a.patient_id
          AND m.start_ts <= a.start_ts
          AND m.start_ts >= a.start_ts - INTERVAL '90 days'
    GROUP BY a.encounter_id
)

SELECT
    a.encounter_id,
    a.patient_id,

    -- ---------- TARGETS ----------
    a.los_days,
    a.total_claim_cost,
    (a.los_days > 7)::INT                              AS is_extended_stay,   -- classification target option

    -- ---------- ADMISSION CONTEXT ----------
    a.encounterclass,
    a.start_ts,
    EXTRACT(DOW FROM a.start_ts)::INT                   AS admit_day_of_week, -- 0=Sunday
    (EXTRACT(DOW FROM a.start_ts) IN (0,6))::INT        AS admit_on_weekend,
    EXTRACT(HOUR FROM a.start_ts)::INT                  AS admit_hour,
    EXTRACT(MONTH FROM a.start_ts)::INT                 AS admit_month,
    CASE
        WHEN EXTRACT(MONTH FROM a.start_ts) IN (12,1,2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM a.start_ts) IN (3,4,5)  THEN 'Spring'
        WHEN EXTRACT(MONTH FROM a.start_ts) IN (6,7,8)  THEN 'Summer'
        ELSE 'Fall'
    END                                                  AS admit_season,

    -- ---------- PATIENT DEMOGRAPHICS ----------
    p.gender,
    p.race,
    p.ethnicity,
    DATE_PART('year', AGE(a.start_ts::date, p.birthdate))::INT AS age_at_admission,

    -- ---------- PAYER ----------
    pay.payer_type,

    -- ---------- CLINICAL SEVERITY / COMPLEXITY ----------
    COALESCE(cc.comorbidity_count, 0)                   AS comorbidity_count,
    COALESCE(nc.new_conditions_count, 0)                AS new_conditions_count,
    COALESCE(pc.procedure_count, 0)                     AS procedure_count,
    COALESCE(rm.meds_last_90_days, 0)                   AS meds_last_90_days,

    -- ---------- PRIOR UTILIZATION ----------
    COALESCE(pu.prior_admission_count, 0)               AS prior_admission_count,
    CASE
        WHEN pu.last_discharge_ts IS NULL THEN NULL
        ELSE ROUND(EXTRACT(EPOCH FROM (a.start_ts - pu.last_discharge_ts)) / 86400.0, 1)
    END                                                  AS days_since_last_discharge,
    -- Readmission within 30 days of a prior discharge — common hospital KPI
    CASE
        WHEN pu.last_discharge_ts IS NOT NULL
         AND a.start_ts - pu.last_discharge_ts <= INTERVAL '30 days'
        THEN 1 ELSE 0
    END                                                  AS is_30day_readmission

FROM admissions a
JOIN analytics.dim_patients p        ON p.patient_id = a.patient_id
LEFT JOIN analytics.dim_payers pay   ON pay.payer_id  = a.payer_id
LEFT JOIN comorbidity_counts cc      ON cc.encounter_id = a.encounter_id
LEFT JOIN new_conditions_this_visit nc ON nc.encounter_id = a.encounter_id
LEFT JOIN procedure_counts pc        ON pc.encounter_id = a.encounter_id
LEFT JOIN prior_utilization pu       ON pu.encounter_id = a.encounter_id
LEFT JOIN recent_medication_counts rm ON rm.encounter_id = a.encounter_id
-- Drop rows with an implausible age (data artifact in a small % of Synthea
-- records where birthdate postdates encounter) rather than silently modeling on them
WHERE DATE_PART('year', AGE(a.start_ts::date, p.birthdate)) >= 0;

-- Index for fast export / joins
CREATE INDEX idx_model_features_patient ON analytics.model_features(patient_id);

-- ---------------------------------------------------------------
-- Export for Python (run from psql or a script):
-- \copy analytics.model_features TO 'data/model_features.csv' WITH (FORMAT csv, HEADER true)
-- ---------------------------------------------------------------

-- ---------------------------------------------------------------
-- Quick feature sanity checks worth screenshotting for your EDA notebook:
-- SELECT COUNT(*), AVG(los_days), AVG(total_claim_cost) FROM analytics.model_features;
-- SELECT is_extended_stay, COUNT(*) FROM analytics.model_features GROUP BY 1;   -- class balance check
-- SELECT admit_season, ROUND(AVG(los_days),2) AS avg_los FROM analytics.model_features GROUP BY 1 ORDER BY 2 DESC;
-- ---------------------------------------------------------------
