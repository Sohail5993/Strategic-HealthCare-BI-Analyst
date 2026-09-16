-- ============================================================================
-- FILE: 03_analytics_queries.sql
-- PROJECT: Length-of-Stay / Cost-of-Care Prediction
-- DIALECT: PostgreSQL 14+
-- PURPOSE: Standalone analytical queries that power the "business value"
--          section of the case study and the Power BI dashboard. These are
--          the queries worth walking an interviewer through.
-- ============================================================================


-- ============================================================================
-- QUERY 1: 30-day rolling readmission rate by month
-- Shows trend over time — the kind of query hospital ops teams track weekly.
-- Uses a window function over a monthly bucket, not just a GROUP BY, so it
-- can be extended to a true rolling (moving) average across periods.
-- ============================================================================
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', start_ts) AS admit_month,
        COUNT(*)                       AS total_admissions,
        SUM(is_30day_readmission)      AS readmissions
    FROM analytics.model_features
    GROUP BY 1
)
SELECT
    admit_month,
    total_admissions,
    readmissions,
    ROUND(100.0 * readmissions / NULLIF(total_admissions, 0), 2) AS readmission_rate_pct,
    -- 3-month rolling average readmission rate, smooths month-to-month noise
    ROUND(
        AVG(100.0 * readmissions / NULLIF(total_admissions, 0))
        OVER (ORDER BY admit_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),
        2
    ) AS rolling_3mo_avg_readmission_rate_pct
FROM monthly
ORDER BY admit_month;


-- ============================================================================
-- QUERY 2: Department/encounter-class LOS ranking with percentile context
-- Ranks each encounter class by average LOS, and shows what percentile
-- each individual encounter falls into within its own class — useful for
-- flagging outlier stays for case review.
-- ============================================================================
SELECT
    encounter_id,
    encounterclass,
    los_days,
    ROUND(AVG(los_days) OVER (PARTITION BY encounterclass), 2)      AS class_avg_los,
    ROUND(PERCENT_RANK() OVER (PARTITION BY encounterclass ORDER BY los_days) * 100, 1)
                                                                     AS los_percentile_in_class,
    RANK() OVER (PARTITION BY encounterclass ORDER BY los_days DESC) AS los_rank_in_class
FROM analytics.model_features
ORDER BY encounterclass, los_days DESC;


-- ============================================================================
-- QUERY 3: Cost concentration ("top-decile patients") analysis
-- This is the query behind the classic "top 10% of patients drive X% of
-- cost" statistic used in the case study's impact section.
-- ============================================================================
WITH patient_costs AS (
    SELECT
        patient_id,
        SUM(total_claim_cost) AS total_cost
    FROM analytics.model_features
    GROUP BY patient_id
),
ranked AS (
    SELECT
        patient_id,
        total_cost,
        NTILE(10) OVER (ORDER BY total_cost DESC) AS cost_decile
    FROM patient_costs
)
SELECT
    cost_decile,
    COUNT(*)                                   AS patient_count,
    ROUND(SUM(total_cost), 2)                  AS decile_total_cost,
    ROUND(
        100.0 * SUM(total_cost) / SUM(SUM(total_cost)) OVER (), 2
    )                                           AS pct_of_total_cost
FROM ranked
GROUP BY cost_decile
ORDER BY cost_decile;


-- ============================================================================
-- QUERY 4: Prior-admission trajectory per patient (LOS trend across a
-- patient's admission history) — flags patients whose LOS is increasing
-- stay-over-stay, a common care-management target.
-- ============================================================================
SELECT
    patient_id,
    encounter_id,
    start_ts,
    los_days,
    LAG(los_days) OVER (PARTITION BY patient_id ORDER BY start_ts)  AS prev_los_days,
    los_days - LAG(los_days) OVER (PARTITION BY patient_id ORDER BY start_ts)
                                                                     AS los_change_vs_prev,
    ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY start_ts)   AS admission_sequence
FROM analytics.model_features
ORDER BY patient_id, start_ts;


-- ============================================================================
-- QUERY 5: Payer-type comparison — average LOS, cost, and out-of-pocket
-- burden. Useful single table for the dashboard's "cost view" page.
-- ============================================================================
SELECT
    payer_type,
    COUNT(*)                                        AS encounter_count,
    ROUND(AVG(los_days), 2)                          AS avg_los_days,
    ROUND(AVG(total_claim_cost), 2)                  AS avg_total_cost,
    ROUND(AVG(comorbidity_count), 2)                 AS avg_comorbidity_count,
    ROUND(100.0 * AVG(is_extended_stay), 2)          AS pct_extended_stay
FROM analytics.model_features
GROUP BY payer_type
ORDER BY avg_total_cost DESC;
