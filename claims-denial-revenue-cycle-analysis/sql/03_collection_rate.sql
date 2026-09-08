-- =============================================================================
-- 03_collection_rate.sql
-- KPI: Net Collection Rate = Total Paid Amount / Total Billed Amount
-- Ties denial performance directly to dollars -- the metric that gets a
-- revenue cycle analyst a seat at the CFO's table.
-- =============================================================================

-- 3a. Overall collection rate
SELECT
    ROUND(SUM(billed_amount), 2)                              AS total_billed,
    ROUND(SUM(paid_amount), 2)                                AS total_collected,
    ROUND(SUM(billed_amount) - SUM(paid_amount), 2)           AS total_uncollected,
    ROUND(100.0 * SUM(paid_amount) / SUM(billed_amount), 2)   AS collection_rate_pct
FROM fact_claims;

-- 3b. Collection rate by payer -- who pays the smallest share of what's billed?
SELECT
    payer_name,
    payer_type,
    ROUND(SUM(billed_amount), 2)                              AS total_billed,
    ROUND(SUM(paid_amount), 2)                                AS total_collected,
    ROUND(100.0 * SUM(paid_amount) / SUM(billed_amount), 2)   AS collection_rate_pct
FROM fact_claims
GROUP BY payer_name, payer_type
ORDER BY collection_rate_pct ASC;

-- 3c. Collection rate by service line
SELECT
    service_line,
    ROUND(SUM(billed_amount), 2)                              AS total_billed,
    ROUND(SUM(paid_amount), 2)                                AS total_collected,
    ROUND(100.0 * SUM(paid_amount) / SUM(billed_amount), 2)   AS collection_rate_pct
FROM fact_claims
GROUP BY service_line
ORDER BY collection_rate_pct ASC;

-- 3d. Revenue written off due to denials that were never recovered
SELECT
    denial_category,
    COUNT(*)                                                  AS written_off_claims,
    ROUND(SUM(billed_amount), 2)                              AS billed_amount_written_off
FROM fact_claims
WHERE final_status = 'Denied - Written Off'
GROUP BY denial_category
ORDER BY billed_amount_written_off DESC;

-- 3e. Monthly net collection rate trend
SELECT
    strftime('%Y-%m', claim_submission_date)                 AS submission_month,
    ROUND(100.0 * SUM(paid_amount) / SUM(billed_amount), 2)  AS collection_rate_pct
FROM fact_claims
GROUP BY submission_month
ORDER BY submission_month;
