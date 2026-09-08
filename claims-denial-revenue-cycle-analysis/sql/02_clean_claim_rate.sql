-- =============================================================================
-- 02_clean_claim_rate.sql
-- KPI: Clean Claim Rate = Claims paid on FIRST submission (no edits, no denial)
--                          / Total Claims Submitted
-- This is the inverse of the denial rate but tracked separately because it's
-- the metric revenue cycle leadership is usually held to (target is typically
-- 90-95% in a healthy RCM operation).
-- =============================================================================

-- 2a. Overall clean claim rate vs. industry benchmark (~90-95%)
SELECT
    COUNT(*)                                                AS total_claims,
    SUM(is_clean_claim)                                     AS clean_claims,
    ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2)        AS clean_claim_rate_pct,
    CASE
        WHEN ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2) >= 90 THEN 'At/Above Benchmark'
        ELSE 'Below Benchmark (target: 90-95%)'
    END                                                      AS benchmark_flag
FROM fact_claims;

-- 2b. Clean claim rate trend by month (are process improvements working?)
SELECT
    strftime('%Y-%m', claim_submission_date)                AS submission_month,
    COUNT(*)                                                 AS total_claims,
    ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2)         AS clean_claim_rate_pct
FROM fact_claims
GROUP BY submission_month
ORDER BY submission_month;

-- 2c. Clean claim rate by payer
SELECT
    payer_name,
    ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2)         AS clean_claim_rate_pct
FROM fact_claims
GROUP BY payer_name
ORDER BY clean_claim_rate_pct ASC;

-- 2d. Clean claim rate by facility (front-end registration/coding quality proxy)
SELECT
    facility,
    ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2)         AS clean_claim_rate_pct
FROM fact_claims
GROUP BY facility
ORDER BY clean_claim_rate_pct ASC;

-- 2e. Clean claim rate by provider (bottom 10 -- targets for provider education /
--     documentation coaching)
SELECT
    provider_id,
    COUNT(*)                                                  AS total_claims,
    ROUND(100.0 * SUM(is_clean_claim) / COUNT(*), 2)          AS clean_claim_rate_pct
FROM fact_claims
GROUP BY provider_id
HAVING COUNT(*) >= 30   -- only providers with a meaningful volume
ORDER BY clean_claim_rate_pct ASC
LIMIT 10;
