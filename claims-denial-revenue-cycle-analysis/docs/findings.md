# Findings & Recommendations
### Claims Denial & Revenue Cycle Analysis

*Analysis period: Jan 2024 – Jun 2025 (18 months), 9,000 claims, ~$50.2M in billed
charges. All figures below come directly from the queries in `/sql` run against
`/data/claims.db`.*

## Headline KPIs

| KPI | Value | Benchmark |
|---|---|---|
| Denial Rate (first pass) | **15.5%** | Industry target: <10% |
| Clean Claim Rate | **84.5%** | Industry target: 90–95% |
| Gross Collection Rate | **52.0%** | (paid ÷ billed; see data dictionary note on gross vs. net) |
| Avg. Turnaround Time — clean claims | **20.5 days** | |
| Avg. Turnaround Time — denied & reworked claims | **51.6 days** | 2.5x slower |
| Billed charges denied on first pass | **$8.24M** | |
| Billed charges permanently written off | **$6.20M** | |

Clean claim rate is sitting **5.5–10.5 points below the standard 90–95% target**,
and every point of that gap is directly costing both cash and staff time —
denied claims take **2.5x longer** to resolve than clean ones.

## Root cause #1 — A specific, dated payer policy change (highest-confidence finding)

Meridian Health Plan's denial rate for **Orthopedics and Oncology claims**
jumped from **21.4% before 2025-01-01 to 55.9% after** — while every other
payer/service-line combination stayed roughly flat over the same window, and
**58% of Meridian's post-January denials carry an Authorization (CO-197)
reason code**, versus effectively 0% before.

**Read:** this isn't a general quality problem — it's a single payer that
tightened prior-authorization requirements at a specific point in time, most
likely for these two service lines specifically. That's the kind of finding
that turns into a concrete action: get Meridian's updated prior-auth policy
in writing, and build a pre-submission authorization checklist specifically
for Ortho/Oncology claims going to Meridian.

**Estimated impact:** modeling the "excess" denials above what Meridian's own
pre-2025 baseline would predict recovers an estimated **~$250K in billed
charges** that a fixed pre-auth workflow could protect going forward (see
`sql/06_opportunity_sizing.sql`, query 6b).

## Root cause #2 — Behavioral Health has a documentation gap, not a billing problem

Behavioral Health has the **highest service-line denial rate (20.0%)**, and
**44.9% of its denials are Medical Necessity (CO-50)** — more than double the
rate of almost every other service line. This pattern (high denial volume,
concentrated in one reason category, tied to one clinical area) points at
clinical documentation / order-set standardization, not claims processing.

**Recommendation:** partner with Behavioral Health clinical leadership on
documentation templates that pre-empt medical necessity criteria, rather than
routing this to the billing team — billing can't fix a documentation problem.

## Root cause #3 — East Medical Center has a front-end eligibility gap

East Medical Center has both the **highest overall denial rate of any
facility (19.6% vs. 15.2% at Main Campus)** and the **highest share of those
denials tied to Eligibility (46.0% vs. 20.7% at Main Campus)**. This is a
textbook front-desk / registration insurance-verification issue, not a
coding or clinical issue.

**Recommendation:** audit East Medical Center's registration workflow and
real-time eligibility verification tooling; this is typically the
cheapest denial category to fix (process/training, not systems).

## Root cause #4 — Not all denials are equally recoverable

Timely Filing and Duplicate Claim denials are almost never overturned on
appeal (**1.3% and 4.4% ultimate recovery rate**, respectively) — they
represent **pure process failure** (submitted late or submitted twice) and
essentially 100% preventable, permanent revenue loss (**~$1.24M combined
written off** in this dataset). By contrast, Authorization and Eligibility
denials are recovered at much higher rates when appealed, meaning staff time
spent working those is worth it — staff time spent *appealing* Timely Filing
denials is largely wasted; the fix belongs upstream, in the submission
workflow (e.g., automated filing-deadline alerts).

## Prioritized opportunity list

Ranking denial categories by an "if we cut this category's denial volume in
half" framing (`sql/06_opportunity_sizing.sql`, query 6c):

| Denial Category | Denied Claims | Billed $ at Risk | Est. $ Recovered if Halved |
|---|---|---|---|
| Eligibility | 340 | $2.13M | ~$692K |
| Missing Information | 274 | $1.57M | ~$509K |
| Medical Necessity | 212 | $1.02M | ~$332K |
| Authorization | 190 | (Meridian-driven, see above) | — |
| Timely Filing | 157 | $956K | *Not appeal-recoverable — fix at submission stage* |

## Bottom line

Three concrete, ownable fixes — a Meridian pre-auth checklist, a Behavioral
Health documentation template, and an East Medical Center front-desk
eligibility audit — collectively touch the largest denial categories in this
dataset and have a plausible path to closing a meaningful share of the gap
between the current 84.5% clean claim rate and the 90%+ industry benchmark.
