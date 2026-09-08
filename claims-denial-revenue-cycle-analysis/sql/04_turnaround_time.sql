-- =============================================================================
-- 04_turnaround_time.sql
-- KPI: Turnaround Time (TAT) = Days between claim submission and final
-- adjudication (payment or write-off). Denials roughly double TAT because
-- of the rework/appeal cycle, which directly hurts days-in-A/R and cash flow.
-- =============================================================================

-- 4a. Overall average turnaround time, clean vs. denied-then-reworked claims
--     (in Postgres, swap the AVG-based median proxy below for a real
--      PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY turnaround_days))
SELECT
    is_clean_claim,
    COUNT(*)                                    AS claims,
    ROUND(AVG(turnaround_days), 1)              AS avg_turnaround_days,
    MIN(turnaround_days)                        AS min_turnaround_days,
    MAX(turnaround_days)                        AS max_turnaround_days
FROM fact_claims
GROUP BY is_clean_claim;

-- 4b. Average turnaround time by payer
SELECT
    payer_name,
    payer_type,
    ROUND(AVG(turnaround_days), 1)               AS avg_turnaround_days
FROM fact_claims
GROUP BY payer_name, payer_type
ORDER BY avg_turnaround_days DESC;

-- 4c. Average turnaround time by denial category (which denial types cost the
--     most days, i.e. slow down cash the most when they occur?)
SELECT
    denial_category,
    COUNT(*)                                      AS denied_claims,
    ROUND(AVG(turnaround_days), 1)                AS avg_turnaround_days
FROM fact_claims
WHERE first_pass_status = 'Denied'
GROUP BY denial_category
ORDER BY avg_turnaround_days DESC;

-- 4d. Turnaround time by service line
SELECT
    service_line,
    ROUND(AVG(turnaround_days), 1)                AS avg_turnaround_days
FROM fact_claims
GROUP BY service_line
ORDER BY avg_turnaround_days DESC;

-- 4e. % of claims exceeding a 30-day TAT target, by payer
SELECT
    payer_name,
    COUNT(*)                                                              AS total_claims,
    SUM(CASE WHEN turnaround_days > 30 THEN 1 ELSE 0 END)                 AS over_30_days,
    ROUND(100.0 * SUM(CASE WHEN turnaround_days > 30 THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                  AS pct_over_target
FROM fact_claims
GROUP BY payer_name
ORDER BY pct_over_target DESC;
