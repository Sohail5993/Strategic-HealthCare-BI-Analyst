-- =============================================================================
-- Star Schema Redesign — Example 2: Healthcare Patient Encounters
-- Grain: one row per patient encounter (visit) — not per diagnosis.
-- Target: PostgreSQL (portable to any standard SQL engine with minor tweaks)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- DIM_DATE — conformed, role-playing dimension: same physical table
-- referenced twice from the fact table (admit / discharge) via views below.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key        INT PRIMARY KEY,
    full_date       DATE NOT NULL,
    day_of_week     VARCHAR(10) NOT NULL,
    month           SMALLINT NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    is_holiday      BOOLEAN NOT NULL DEFAULT FALSE
);

-- Role-playing views — same underlying table, two business-facing aliases.
-- Keeps holiday calendars and fiscal-period logic defined exactly once.
CREATE VIEW dim_admit_date AS SELECT * FROM dim_date;
CREATE VIEW dim_discharge_date AS SELECT * FROM dim_date;

-- ---------------------------------------------------------------------------
-- DIM_PATIENT — SCD Type 2 on insurance/address: "which payer was active
-- at time of service" is a compliance requirement, not a reporting nicety.
-- De-identified: only a surrogate key and non-identifying attributes are
-- carried into the analytical layer (privacy-by-design, not bolted on later).
-- ---------------------------------------------------------------------------
CREATE TABLE dim_patient (
    patient_key     SERIAL PRIMARY KEY,
    patient_id      VARCHAR(20) NOT NULL,   -- de-identified natural key
    age_band        VARCHAR(10) NOT NULL,   -- e.g. '40-49' — never raw DOB
    gender          VARCHAR(10),
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_dim_patient_natural_key ON dim_patient (patient_id, is_current);

-- ---------------------------------------------------------------------------
-- DIM_PROVIDER — SCD Type 1
-- ---------------------------------------------------------------------------
CREATE TABLE dim_provider (
    provider_key    SERIAL PRIMARY KEY,
    provider_id     VARCHAR(20) NOT NULL UNIQUE,
    provider_name   VARCHAR(120) NOT NULL,
    specialty       VARCHAR(80)
);

-- ---------------------------------------------------------------------------
-- DIM_PAYER — SCD Type 1
-- ---------------------------------------------------------------------------
CREATE TABLE dim_payer (
    payer_key       SERIAL PRIMARY KEY,
    payer_name      VARCHAR(80) NOT NULL UNIQUE,
    payer_type      VARCHAR(30)             -- e.g. Government, Commercial
);

-- ---------------------------------------------------------------------------
-- DIM_DIAGNOSIS — referenced via bridge table, not directly on the fact,
-- since one encounter can carry multiple diagnoses.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_diagnosis (
    diagnosis_key   SERIAL PRIMARY KEY,
    icd10_code      VARCHAR(10) NOT NULL UNIQUE,
    description     VARCHAR(200) NOT NULL,
    category        VARCHAR(60)
);

-- ---------------------------------------------------------------------------
-- FACT_ENCOUNTER — grain: one row per patient encounter.
-- This is the fix for the source extract's double-counting bug: TotalCharges
-- is only safe to SUM because the grain is locked to one row per encounter.
-- ---------------------------------------------------------------------------
CREATE TABLE fact_encounter (
    admit_date_key      INT NOT NULL REFERENCES dim_date (date_key),
    discharge_date_key  INT NOT NULL REFERENCES dim_date (date_key),
    patient_key         INT NOT NULL REFERENCES dim_patient (patient_key),
    provider_key         INT NOT NULL REFERENCES dim_provider (provider_key),
    payer_key            INT NOT NULL REFERENCES dim_payer (payer_key),
    encounter_id          VARCHAR(20) NOT NULL UNIQUE, -- degenerate dimension

    -- Fully additive, only because the grain is fixed to one row per encounter
    length_of_stay_days   INT NOT NULL,
    total_charges         NUMERIC(12,2) NOT NULL,
    total_paid             NUMERIC(12,2) NOT NULL
);

CREATE INDEX idx_fact_encounter_patient ON fact_encounter (patient_key);
CREATE INDEX idx_fact_encounter_admit_date ON fact_encounter (admit_date_key);

-- ---------------------------------------------------------------------------
-- BRIDGE_ENCOUNTER_DIAGNOSIS — resolves the many-to-many relationship
-- between encounters and diagnoses without repeating (and double-counting)
-- the fact row per diagnosis.
-- ---------------------------------------------------------------------------
CREATE TABLE bridge_encounter_diagnosis (
    encounter_id    VARCHAR(20) NOT NULL REFERENCES fact_encounter (encounter_id),
    diagnosis_key   INT NOT NULL REFERENCES dim_diagnosis (diagnosis_key),
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    weighting_factor NUMERIC(4,3),          -- optional: for explicit cost allocation across diagnoses
    PRIMARY KEY (encounter_id, diagnosis_key)
);

-- ---------------------------------------------------------------------------
-- Sample data — mirrors the flat extract shown in the README
-- ---------------------------------------------------------------------------
INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year)
VALUES
    (20240211, '2024-02-11', 'Sunday', 2, 1, 2024),
    (20240213, '2024-02-13', 'Tuesday', 2, 1, 2024);

INSERT INTO dim_patient (patient_id, age_band, gender, effective_date)
VALUES
    ('P8842', '40-49', 'F', '2024-01-01'),
    ('P9013', '30-39', 'M', '2024-01-01');

INSERT INTO dim_provider (provider_id, provider_name, specialty)
VALUES
    ('DR221', 'Dr. Naveed', 'Cardiology'),
    ('DR118', 'Dr. Aslam', 'Emergency');

INSERT INTO dim_payer (payer_name, payer_type)
VALUES
    ('Sehat Card', 'Government'),
    ('Commercial', 'Private');

INSERT INTO dim_diagnosis (icd10_code, description, category)
VALUES
    ('I10', 'Essential hypertension', 'Cardiovascular'),
    ('E11.9', 'Type 2 diabetes', 'Endocrine'),
    ('S06.0', 'Concussion', 'Injury');

INSERT INTO fact_encounter (admit_date_key, discharge_date_key, patient_key, provider_key, payer_key, encounter_id, length_of_stay_days, total_charges, total_paid)
VALUES
    (20240211, 20240213,
     (SELECT patient_key FROM dim_patient WHERE patient_id = 'P8842'),
     (SELECT provider_key FROM dim_provider WHERE provider_id = 'DR221'),
     (SELECT payer_key FROM dim_payer WHERE payer_name = 'Sehat Card'),
     'E5510', 2, 42000.00, 38500.00),
    (20240211, 20240211,
     (SELECT patient_key FROM dim_patient WHERE patient_id = 'P9013'),
     (SELECT provider_key FROM dim_provider WHERE provider_id = 'DR118'),
     (SELECT payer_key FROM dim_payer WHERE payer_name = 'Commercial'),
     'E5511', 0, 15200.00, 15200.00);

INSERT INTO bridge_encounter_diagnosis (encounter_id, diagnosis_key, is_primary)
VALUES
    ('E5510', (SELECT diagnosis_key FROM dim_diagnosis WHERE icd10_code = 'I10'), TRUE),
    ('E5510', (SELECT diagnosis_key FROM dim_diagnosis WHERE icd10_code = 'E11.9'), FALSE),
    ('E5511', (SELECT diagnosis_key FROM dim_diagnosis WHERE icd10_code = 'S06.0'), TRUE);

-- ---------------------------------------------------------------------------
-- Example query: total charges by payer — correct because the fact grain
-- is one row per encounter, so no diagnosis fan-out double-counts revenue.
-- ---------------------------------------------------------------------------
-- SELECT
--     pay.payer_name,
--     COUNT(*)                    AS encounters,
--     SUM(f.total_charges)        AS total_charges
-- FROM fact_encounter f
-- JOIN dim_payer pay ON f.payer_key = pay.payer_key
-- GROUP BY pay.payer_name
-- ORDER BY total_charges DESC;

-- ---------------------------------------------------------------------------
-- Example query: diagnosis frequency — only possible via the bridge table,
-- without disturbing the fact table's grain or its additive measures.
-- ---------------------------------------------------------------------------
-- SELECT
--     d.description,
--     COUNT(*) AS times_diagnosed
-- FROM bridge_encounter_diagnosis b
-- JOIN dim_diagnosis d ON b.diagnosis_key = d.diagnosis_key
-- GROUP BY d.description
-- ORDER BY times_diagnosed DESC;
