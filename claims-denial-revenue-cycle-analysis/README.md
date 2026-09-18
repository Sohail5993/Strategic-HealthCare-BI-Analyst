# Claims Denial & Revenue Cycle Analysis

**Root-cause analysis of hospital claim denials — turning "denial rate is up" into a
dollar-quantified, ownable action list.**

## The business problem

Denial rate and clean claim rate are two of the most closely watched revenue cycle metrics in any
hospital or payer operation — every point of denial is cash sitting in A/R, or written off
entirely, and every reworked claim ties up staff time a clean-on-first-pass claim never would. Most
denial dashboards stop at "denial rate is up" — a KPI without a cause, and without an owner. The
real question isn't whether denials are elevated; it's *which* specific, fixable process broke, and
who should fix it.

## Approach

9,000 claims (Jan 2024–Jun 2025, ~$50.2M billed) modeled across 8 payers, 10 service lines, and 4
facilities, with CMS CARC-style denial reason codes attached to every denied claim. Rather than
stopping at descriptive KPIs (denial rate, clean claim rate, collection rate, turnaround time), the
analysis pushed into root-cause territory: a before/after cohort comparison to detect payer policy
shifts, a reason-code Pareto to find the 80/20 of denial volume, and a payer × service-line heatmap
to isolate hot spots that aggregate rates wash out. Every root cause was translated into a
dollar-quantified opportunity, so the output is a prioritized action list, not just a chart.

## Result

Denial rate came in at **15.5%** against a <10% industry target, with clean claim rate at **84.5%**
— 5.5–10.5 points below the standard 90–95% benchmark. Rather than leaving that as one number, the
analysis isolated three specific, ownable root causes:

1. A **Meridian Health Plan prior-authorization policy change** that pushed
   Orthopedics/Oncology denials from 21.4% to 55.9% starting a specific date.
2. A **Behavioral Health documentation gap** driving a 44.9% medical-necessity denial share —
   roughly double every other service line.
3. A **front-desk eligibility-verification gap at one facility** (46.0% of its denials vs. 20.7%
   elsewhere).

Denied-and-reworked claims took **2.5x longer to resolve** than clean ones (51.6 vs. 20.5 days).
**$8.24M** in billed charges were denied on first submission, of which **$6.20M** was ultimately
written off — with an estimated **$250K recoverable** through a targeted pre-authorization fix
alone.

## Dashboard

[`dashboard.html`](./dashboard.html) embeds the live Tableau Public visualization. Explore the
filters inside the report directly for the full payer × service-line breakdown.

## A note on what's in this repo

The analysis above was built and lives in Tableau — the underlying claims dataset, the
CARC-code root-cause queries, and the cohort/Pareto calculations aren't currently committed to this
repo, only their output (this write-up and the embedded dashboard). That's different from every
other project in this portfolio, where the SQL/Python that produced the numbers is included
alongside the result. Flagging this honestly rather than implying there's a reproducible pipeline
here to inspect — if you're looking for the full methodology, the Tableau workbook itself is the
source of truth, not this folder.
