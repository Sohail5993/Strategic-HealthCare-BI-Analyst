-- =============================================================================
-- 05_root_cause_analysis.sql
-- Digs past "what is the denial rate" into "why" -- the analysis that turns
-- a KPI dashboard into an action plan for the revenue cycle team.
-- =============================================================================

-- 5a. Denial reason Pareto (80/20): which handful of reason codes account for
--     the majority of denials? -> tells you where to focus root-cause fixes.
WITH reason_counts AS (
    SELECT
        denial_reason_code,
        denial_reason_description,
        denial_category,
        COUNT(*) AS denied_claims
    FROM fact_claims
    WHERE first_pass_status = 'Denied'
    GROUP BY denial_reason_code, denial_reason_description, denial_category
)
SELECT
    denial_reason_code,
    denial_reason_description,
    denial_category,
    denied_claims,
    ROUND(100.0 * denied_claims / SUM(denied_claims) OVER (), 2)                    AS pct_of_denials,
    ROUND(100.0 * SUM(denied_claims) OVER (ORDER BY denied_claims DESC)
          / SUM(denied_claims) OVER (), 2)                                          AS cumulative_pct
FROM reason_counts
ORDER BY denied_claims DESC;

-- 5b. ROOT CAUSE #1 -- Payer policy change detection:
-- Compare a payer/service-line combination's denial rate before vs. after a
-- given date, to detect payer behavior shifts (e.g. a prior-auth policy
-- tightening). Parameterize payer_name / service_line / cutoff date as needed.
SELECT
    payer_name,
    service_line,
    CASE WHEN claim_submission_date >= '2025-01-01' THEN 'After 2025-01-01' ELSE 'Before 2025-01-01' END AS period,
    COUNT(*)                                                              AS total_claims,
    ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                 AS denial_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN denial_category = 'Authorization' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END), 0), 2)
                                                                           AS pct_denials_that_are_auth
FROM fact_claims
WHERE payer_name = 'Meridian Health Plan'
  AND service_line IN ('Orthopedics', 'Oncology')
GROUP BY payer_name, service_line, period
ORDER BY service_line, period;

-- 5c. ROOT CAUSE #2 -- Clinical documentation gap:
-- Service lines with disproportionately high Medical Necessity denials
-- point to a documentation/order-set problem, not a billing problem.
SELECT
    service_line,
    SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)         AS total_denials,
    SUM(CASE WHEN denial_category = 'Medical Necessity' THEN 1 ELSE 0 END) AS medical_necessity_denials,
    ROUND(100.0 * SUM(CASE WHEN denial_category = 'Medical Necessity' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END), 0), 2)
                                                                            AS pct_denials_medical_necessity
FROM fact_claims
GROUP BY service_line
HAVING SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END) >= 10
ORDER BY pct_denials_medical_necessity DESC;

-- 5d. ROOT CAUSE #3 -- Front-end registration/eligibility gap by facility:
-- If one facility's denials skew heavily toward Eligibility, the fix is
-- front-desk insurance verification training, not a coding/billing fix.
SELECT
    facility,
    SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)          AS total_denials,
    SUM(CASE WHEN denial_category = 'Eligibility' THEN 1 ELSE 0 END)       AS eligibility_denials,
    ROUND(100.0 * SUM(CASE WHEN denial_category = 'Eligibility' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END), 0), 2)
                                                                             AS pct_denials_eligibility
FROM fact_claims
GROUP BY facility
ORDER BY pct_denials_eligibility DESC;

-- 5e. Recoverable vs. structurally unrecoverable denials:
-- Timely Filing and Duplicate Claim denials are almost never overturned --
-- they represent a pure process failure (submit late / submit twice) and
-- 100% preventable revenue loss, as opposed to Authorization/Eligibility
-- denials which are frequently recoverable through appeal.
SELECT
    denial_category,
    COUNT(*)                                                                AS denied_claims,
    SUM(is_resubmitted)                                                     AS resubmitted_claims,
    SUM(CASE WHEN final_status = 'Paid' THEN 1 ELSE 0 END)                  AS ultimately_recovered,
    ROUND(100.0 * SUM(CASE WHEN final_status = 'Paid' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                    AS pct_ultimately_recovered,
    ROUND(SUM(CASE WHEN final_status = 'Denied - Written Off' THEN billed_amount ELSE 0 END), 2)
                                                                             AS billed_amount_permanently_lost
FROM fact_claims
WHERE first_pass_status = 'Denied'
GROUP BY denial_category
ORDER BY pct_ultimately_recovered ASC;
