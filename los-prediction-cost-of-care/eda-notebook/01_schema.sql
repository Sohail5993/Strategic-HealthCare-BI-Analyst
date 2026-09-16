-- ============================================================================
-- FILE: 01_schema.sql
-- PROJECT: Length-of-Stay / Cost-of-Care Prediction
-- DIALECT: PostgreSQL 14+
-- PURPOSE: (1) Staging tables that mirror raw Synthea CSV exports as-is
--          (2) A dimensional (star schema) layer built on top of staging,
--              which the feature-engineering and BI layers query against.
--
-- Source data: Synthea synthetic patient generator
--   https://github.com/synthetichealth/synthea
--   Load order matters due to FKs: patients -> payers -> encounters ->
--   conditions/procedures/medications/observations
-- ============================================================================


-- ============================================================================
-- SECTION 1: STAGING TABLES
-- Raw 1:1 mirrors of Synthea CSV columns. Load with COPY / \copy.
-- Keep these untouched (no cleaning here) so you always have an audit trail
-- back to the original export.
-- ============================================================================

DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;

CREATE TABLE staging.patients (
    id                  UUID PRIMARY KEY,
    birthdate           DATE,
    deathdate           DATE,
    ssn                 TEXT,           -- synthetic, but drop before any sharing anyway
    first               TEXT,
    last                TEXT,
    race                TEXT,
    ethnicity           TEXT,
    gender              TEXT,
    birthplace          TEXT,
    address             TEXT,
    city                TEXT,
    state               TEXT,
    zip                 TEXT,
    healthcare_expenses NUMERIC(12,2),
    healthcare_coverage NUMERIC(12,2)
);

CREATE TABLE staging.payers (
    id          UUID PRIMARY KEY,
    name        TEXT,
    ownership   TEXT            -- e.g. GOVERNMENT, PRIVATE, NO_INSURANCE
);

CREATE TABLE staging.encounters (
    id                  UUID PRIMARY KEY,
    start_ts            TIMESTAMPTZ,
    stop_ts             TIMESTAMPTZ,
    patient_id          UUID REFERENCES staging.patients(id),
    organization_id     UUID,
    payer_id            UUID REFERENCES staging.payers(id),
    encounterclass      TEXT,       -- ambulatory, emergency, inpatient, urgentcare, wellness
    code                TEXT,
    description         TEXT,
    base_encounter_cost NUMERIC(12,2),
    total_claim_cost    NUMERIC(12,2),
    payer_coverage      NUMERIC(12,2),
    reasoncode          TEXT,
    reasondescription   TEXT
);

CREATE TABLE staging.conditions (
    start_date  DATE,
    stop_date   DATE,
    patient_id  UUID REFERENCES staging.patients(id),
    encounter_id UUID REFERENCES staging.encounters(id),
    code        TEXT,
    description TEXT
);

CREATE TABLE staging.procedures (
    start_ts    TIMESTAMPTZ,
    stop_ts     TIMESTAMPTZ,
    patient_id  UUID REFERENCES staging.patients(id),
    encounter_id UUID REFERENCES staging.encounters(id),
    code        TEXT,
    description TEXT,
    base_cost   NUMERIC(12,2),
    reasoncode  TEXT,
    reasondescription TEXT
);

CREATE TABLE staging.observations (
    date_ts     TIMESTAMPTZ,
    patient_id  UUID REFERENCES staging.patients(id),
    encounter_id UUID REFERENCES staging.encounters(id),
    code        TEXT,
    description TEXT,
    value       TEXT,       -- Synthea mixes numeric + text values in one column
    units       TEXT,
    type        TEXT        -- numeric, text, coded
);

CREATE TABLE staging.medications (
    start_ts    TIMESTAMPTZ,
    stop_ts     TIMESTAMPTZ,
    patient_id  UUID REFERENCES staging.patients(id),
    payer_id    UUID REFERENCES staging.payers(id),
    encounter_id UUID REFERENCES staging.encounters(id),
    code        TEXT,
    description TEXT,
    base_cost   NUMERIC(12,2),
    payer_coverage NUMERIC(12,2),
    dispenses   INTEGER,
    totalcost   NUMERIC(12,2),
    reasoncode  TEXT,
    reasondescription TEXT
);

-- Example load (run from psql, adjust paths):
-- \copy staging.patients FROM 'data/synthea/csv/patients.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.payers FROM 'data/synthea/csv/payers.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.encounters FROM 'data/synthea/csv/encounters.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.conditions FROM 'data/synthea/csv/conditions.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.procedures FROM 'data/synthea/csv/procedures.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.observations FROM 'data/synthea/csv/observations.csv' WITH (FORMAT csv, HEADER true)
-- \copy staging.medications FROM 'data/synthea/csv/medications.csv' WITH (FORMAT csv, HEADER true)


-- ============================================================================
-- SECTION 2: DIMENSIONAL MODEL (STAR SCHEMA)
-- fact_encounters is the grain of one row per hospital encounter/admission.
-- This is what the feature-engineering layer and Power BI both point to.
-- ============================================================================

DROP SCHEMA IF EXISTS analytics CASCADE;
CREATE SCHEMA analytics;

-- ---------- DIM: Patients (with basic cleaning applied) ----------
CREATE TABLE analytics.dim_patients AS
SELECT
    id                                   AS patient_id,
    birthdate,
    deathdate,
    INITCAP(gender)                      AS gender,
    INITCAP(race)                        AS race,
    INITCAP(ethnicity)                   AS ethnicity,
    city,
    state,
    zip,
    ROUND(healthcare_expenses, 2)        AS lifetime_expenses,
    ROUND(healthcare_coverage, 2)        AS lifetime_coverage
FROM staging.patients
WHERE id IS NOT NULL;

ALTER TABLE analytics.dim_patients ADD PRIMARY KEY (patient_id);

-- ---------- DIM: Payers ----------
CREATE TABLE analytics.dim_payers AS
SELECT DISTINCT
    id           AS payer_id,
    name         AS payer_name,
    COALESCE(ownership, 'UNKNOWN') AS payer_type
FROM staging.payers;

ALTER TABLE analytics.dim_payers ADD PRIMARY KEY (payer_id);

-- ---------- DIM: Conditions (deduplicated code/description lookup) ----------
CREATE TABLE analytics.dim_conditions AS
SELECT DISTINCT
    code            AS condition_code,
    description     AS condition_description
FROM staging.conditions
WHERE code IS NOT NULL;

ALTER TABLE analytics.dim_conditions ADD PRIMARY KEY (condition_code);

-- ---------- DIM: Procedures (deduplicated code/description lookup) ----------
CREATE TABLE analytics.dim_procedures AS
SELECT DISTINCT
    code            AS procedure_code,
    description     AS procedure_description
FROM staging.procedures
WHERE code IS NOT NULL;

ALTER TABLE analytics.dim_procedures ADD PRIMARY KEY (procedure_code);

-- ---------- BRIDGE: Encounter <-> Conditions (many-to-many) ----------
CREATE TABLE analytics.bridge_encounter_conditions AS
SELECT DISTINCT
    encounter_id,
    code AS condition_code
FROM staging.conditions
WHERE encounter_id IS NOT NULL AND code IS NOT NULL;

-- ---------- BRIDGE: Encounter <-> Procedures (many-to-many) ----------
CREATE TABLE analytics.bridge_encounter_procedures AS
SELECT DISTINCT
    encounter_id,
    code AS procedure_code
FROM staging.procedures
WHERE encounter_id IS NOT NULL AND code IS NOT NULL;

-- ---------- FACT: Encounters ----------
-- Grain: one row per encounter. LOS is derived here so every downstream
-- query (features, BI, model export) uses one consistent LOS definition.
CREATE TABLE analytics.fact_encounters AS
SELECT
    e.id                                            AS encounter_id,
    e.patient_id,
    e.payer_id,
    e.organization_id,
    e.encounterclass,
    e.code                                          AS encounter_code,
    e.description                                   AS encounter_description,
    e.start_ts,
    e.stop_ts,
    -- LOS in fractional days; inpatient/emergency stays under 1 day still
    -- register as > 0 rather than rounding to zero.
    ROUND(EXTRACT(EPOCH FROM (e.stop_ts - e.start_ts)) / 86400.0, 3) AS los_days,
    ROUND(e.base_encounter_cost, 2)                 AS base_encounter_cost,
    ROUND(e.total_claim_cost, 2)                    AS total_claim_cost,
    ROUND(e.payer_coverage, 2)                      AS payer_coverage,
    ROUND(e.total_claim_cost - e.payer_coverage, 2) AS patient_out_of_pocket,
    e.reasoncode,
    e.reasondescription
FROM staging.encounters e
WHERE e.stop_ts IS NOT NULL
  AND e.stop_ts >= e.start_ts;      -- drop any malformed/negative-duration rows

ALTER TABLE analytics.fact_encounters ADD PRIMARY KEY (encounter_id);
CREATE INDEX idx_fact_encounters_patient ON analytics.fact_encounters(patient_id);
CREATE INDEX idx_fact_encounters_start   ON analytics.fact_encounters(start_ts);
CREATE INDEX idx_fact_encounters_class   ON analytics.fact_encounters(encounterclass);

-- Sanity checks worth running right after build (put screenshots of these
-- in your README/EDA notebook as a "data quality" section):
-- SELECT COUNT(*) FROM analytics.fact_encounters WHERE los_days <= 0;
-- SELECT encounterclass, COUNT(*), AVG(los_days) FROM analytics.fact_encounters GROUP BY 1 ORDER BY 2 DESC;
-- SELECT COUNT(*) FROM analytics.fact_encounters WHERE total_claim_cost IS NULL;
