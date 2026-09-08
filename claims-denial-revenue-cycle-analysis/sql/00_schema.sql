-- =============================================================================
-- 00_schema.sql
-- Strategic Healthcare BI Analyst Portfolio Project
-- Denial Rate & Clean Claim Rate Analysis
--
-- Star schema: one fact table (fact_claims) + four dimension tables.
-- Written in ANSI/PostgreSQL-flavored SQL. The repo's data/claims.db
-- (SQLite) was generated from this same logical model via
-- scripts/build_database.py so every query below is runnable as-is.
-- =============================================================================

DROP TABLE IF EXISTS dim_payer;
CREATE TABLE dim_payer (
    payer_id     INTEGER PRIMARY KEY,
    payer_name   VARCHAR(50) NOT NULL,
    payer_type   VARCHAR(20) NOT NULL   -- Government | Commercial | Managed Care | Self-Pay
);

DROP TABLE IF EXISTS dim_service_line;
CREATE TABLE dim_service_line (
    service_line_id INTEGER PRIMARY KEY,
    service_line     VARCHAR(50) NOT NULL
);

DROP TABLE IF EXISTS dim_facility;
CREATE TABLE dim_facility (
    facility_id   INTEGER PRIMARY KEY,
    facility      VARCHAR(50) NOT NULL
);

DROP TABLE IF EXISTS dim_denial_reason;
CREATE TABLE dim_denial_reason (
    denial_reason_code        VARCHAR(10) PRIMARY KEY,   -- CARC-style code, e.g. CO-197
    denial_reason_description VARCHAR(120) NOT NULL,
    denial_category           VARCHAR(30) NOT NULL       -- Authorization | Eligibility | Coding Error | ...
);

DROP TABLE IF EXISTS fact_claims;
CREATE TABLE fact_claims (
    claim_id                    VARCHAR(12) PRIMARY KEY,
    patient_id                  VARCHAR(10) NOT NULL,
    provider_id                 VARCHAR(10) NOT NULL,

    facility_id                 INTEGER REFERENCES dim_facility(facility_id),
    facility                    VARCHAR(50) NOT NULL,

    payer_id                    INTEGER REFERENCES dim_payer(payer_id),
    payer_name                  VARCHAR(50) NOT NULL,
    payer_type                  VARCHAR(20) NOT NULL,

    service_line_id             INTEGER REFERENCES dim_service_line(service_line_id),
    service_line                VARCHAR(50) NOT NULL,

    cpt_code                    VARCHAR(10),
    icd10_code                  VARCHAR(10),

    date_of_service              DATE NOT NULL,
    claim_submission_date        DATE NOT NULL,

    billed_amount                NUMERIC(12,2) NOT NULL,
    paid_amount                  NUMERIC(12,2) NOT NULL DEFAULT 0,

    is_clean_claim                BOOLEAN NOT NULL,   -- TRUE if paid on first submission, no denial
    first_pass_status             VARCHAR(10) NOT NULL,   -- Paid | Denied  (result of FIRST submission)

    denial_reason_code            VARCHAR(10) REFERENCES dim_denial_reason(denial_reason_code),
    denial_reason_description     VARCHAR(120),
    denial_category               VARCHAR(30),

    is_resubmitted                 BOOLEAN NOT NULL DEFAULT FALSE,
    resubmission_count             INTEGER NOT NULL DEFAULT 0,

    final_status                   VARCHAR(25) NOT NULL,  -- Paid | Denied - Written Off | Pending Appeal
    turnaround_days                INTEGER NOT NULL       -- submission -> final adjudication, in days
);

-- Helpful indexes for the KPI queries in this folder
CREATE INDEX IF NOT EXISTS idx_fact_payer            ON fact_claims(payer_name);
CREATE INDEX IF NOT EXISTS idx_fact_service_line      ON fact_claims(service_line);
CREATE INDEX IF NOT EXISTS idx_fact_submission_date   ON fact_claims(claim_submission_date);
CREATE INDEX IF NOT EXISTS idx_fact_status            ON fact_claims(first_pass_status);
