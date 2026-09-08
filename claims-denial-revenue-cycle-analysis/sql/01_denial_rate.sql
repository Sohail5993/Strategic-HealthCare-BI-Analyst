-- =============================================================================
-- 01_denial_rate.sql
-- KPI: Denial Rate = Denied Claims (first pass) / Total Submitted Claims
-- =============================================================================

-- 1a. Overall denial rate
SELECT
    COUNT(*)                                                       AS total_claims,
    SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)  AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                           AS denial_rate_pct
FROM fact_claims;

-- 1b. Denial rate by payer (highest first) -- "who is denying us the most?"
SELECT
    payer_name,
    payer_type,
    COUNT(*)                                                        AS total_claims,
    SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS denial_rate_pct
FROM fact_claims
GROUP BY payer_name, payer_type
ORDER BY denial_rate_pct DESC;

-- 1c. Denial rate by service line -- "which clinical area drives the most denials?"
SELECT
    service_line,
    COUNT(*)                                                        AS total_claims,
    SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)   AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS denial_rate_pct
FROM fact_claims
GROUP BY service_line
ORDER BY denial_rate_pct DESC;

-- 1d. Denial rate by reason code -- Pareto input (top codes driving denials)
SELECT
    denial_reason_code,
    denial_reason_description,
    denial_category,
    COUNT(*)                                                        AS denied_claims,
    ROUND(100.0 * COUNT(*) /
          (SELECT COUNT(*) FROM fact_claims WHERE first_pass_status = 'Denied'), 2)
                                                                     AS pct_of_all_denials,
    ROUND(SUM(billed_amount), 2)                                    AS billed_amount_at_risk
FROM fact_claims
WHERE first_pass_status = 'Denied'
GROUP BY denial_reason_code, denial_reason_description, denial_category
ORDER BY denied_claims DESC;

-- 1e. Denial rate by facility -- front-end (registration/eligibility) diagnostic
SELECT
    facility,
    COUNT(*)                                                        AS total_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS denial_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN denial_category = 'Eligibility' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END), 0), 2)
                                                                     AS pct_denials_eligibility
FROM fact_claims
GROUP BY facility
ORDER BY denial_rate_pct DESC;

-- 1f. Monthly denial rate trend (for a Tableau line chart / dashboard headline KPI)
SELECT
    strftime('%Y-%m', claim_submission_date)                       AS submission_month,   -- SQLite dialect - use TO_CHAR/DATE_TRUNC in Postgres
    COUNT(*)                                                        AS total_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS denial_rate_pct
FROM fact_claims
GROUP BY submission_month
ORDER BY submission_month;

-- 1g. Payer x Service Line denial rate matrix (heatmap source for Tableau)
SELECT
    payer_name,
    service_line,
    COUNT(*)                                                        AS total_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS denial_rate_pct
FROM fact_claims
GROUP BY payer_name, service_line
HAVING COUNT(*) >= 15   -- suppress noisy small cells
ORDER BY denial_rate_pct DESC;
