-- =============================================================================
-- 06_opportunity_sizing.sql
-- Converts the root-cause findings into a dollar-quantified opportunity list --
-- the deliverable a CFO/VP Revenue Cycle actually acts on.
-- =============================================================================

-- 6a. Total revenue currently at risk from denials (billed amount tied up in
--     anything other than a first-pass clean payment)
SELECT
    ROUND(SUM(CASE WHEN first_pass_status = 'Denied' THEN billed_amount ELSE 0 END), 2) AS billed_amount_denied_first_pass,
    ROUND(SUM(CASE WHEN final_status = 'Denied - Written Off' THEN billed_amount ELSE 0 END), 2) AS billed_amount_permanently_written_off,
    ROUND(SUM(CASE WHEN final_status = 'Pending Appeal' THEN billed_amount ELSE 0 END), 2) AS billed_amount_pending_appeal
FROM fact_claims;

-- 6b. "If we fixed the #1 preventable root cause" -- Meridian prior-auth spike:
-- estimate the revenue that would have been protected if Meridian's
-- Ortho/Oncology denial rate had stayed at its pre-2025 baseline.
WITH baseline AS (
    SELECT
        ROUND(100.0 * SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)
              / COUNT(*), 4) AS baseline_denial_rate
    FROM fact_claims
    WHERE payer_name = 'Meridian Health Plan'
      AND service_line IN ('Orthopedics', 'Oncology')
      AND claim_submission_date < '2025-01-01'
),
after_period AS (
    SELECT
        COUNT(*)                                                            AS claims_after,
        SUM(CASE WHEN first_pass_status = 'Denied' THEN 1 ELSE 0 END)       AS denials_after,
        SUM(CASE WHEN first_pass_status = 'Denied' THEN billed_amount ELSE 0 END) AS billed_denied_after
    FROM fact_claims
    WHERE payer_name = 'Meridian Health Plan'
      AND service_line IN ('Orthopedics', 'Oncology')
      AND claim_submission_date >= '2025-01-01'
)
SELECT
    b.baseline_denial_rate                                                   AS baseline_denial_rate_pct,
    a.claims_after,
    a.denials_after,
    ROUND(a.claims_after * b.baseline_denial_rate / 100.0, 0)                AS expected_denials_at_baseline_rate,
    ROUND(a.denials_after - (a.claims_after * b.baseline_denial_rate / 100.0), 0) AS excess_denials_from_policy_change,
    a.billed_denied_after                                                    AS billed_amount_currently_denied,
    ROUND(
        (a.denials_after - (a.claims_after * b.baseline_denial_rate / 100.0))
        / NULLIF(a.denials_after, 0) * a.billed_denied_after
    , 2)                                                                     AS estimated_recoverable_billed_amount
FROM baseline b, after_period a;

-- 6c. Opportunity ranking: expected annualized $ recovered if each denial
--     category's denial rate were cut in half through targeted fixes
--     (a standard "opportunity sizing" framing for a denial-management plan)
WITH by_category AS (
    SELECT
        denial_category,
        COUNT(*)                                                           AS denied_claims,
        SUM(billed_amount)                                                 AS billed_amount_denied,
        AVG(billed_amount)                                                 AS avg_billed_per_claim
    FROM fact_claims
    WHERE first_pass_status = 'Denied'
    GROUP BY denial_category
)
SELECT
    denial_category,
    denied_claims,
    ROUND(billed_amount_denied, 2)                                         AS billed_amount_denied,
    ROUND(denied_claims * 0.5, 0)                                          AS claims_recoverable_if_halved,
    ROUND(denied_claims * 0.5 * avg_billed_per_claim * 0.65, 2)            AS est_dollars_recovered_if_halved
        -- 0.65 approximates a blended reimbursement ratio applied to newly-clean claims
FROM by_category
ORDER BY est_dollars_recovered_if_halved DESC;

-- 6d. Simple prioritization matrix: denial volume vs. recoverability, to
--     rank root causes by "fix this first" (Tableau scatter plot source --
--     x = denial volume, y = % ultimately recovered, size = $ at risk)
SELECT
    denial_category,
    COUNT(*)                                                               AS denial_volume,
    ROUND(100.0 * SUM(CASE WHEN final_status = 'Paid' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                  AS pct_recovered,
    ROUND(SUM(CASE WHEN final_status = 'Denied - Written Off' THEN billed_amount ELSE 0 END), 2)
                                                                            AS dollars_at_risk_if_unaddressed
FROM fact_claims
WHERE first_pass_status = 'Denied'
GROUP BY denial_category
ORDER BY dollars_at_risk_if_unaddressed DESC;
