# Emergency Department Throughput Bottleneck Analysis

**Finding which resource is actually the bottleneck in ED wait times — and testing a specific
staffing fix before recommending it.**

## The business problem

A mid-size community ED was losing patients to left-without-being-seen (LWBS) and running average
door-to-provider times well above published benchmarks, concentrated in a specific shift.
Leadership had budget for one additional staff position and needed evidence for where to put it —
more triage nurses, more beds, or more physician coverage — rather than a generic "hire more
people" recommendation.

## Approach

A synthetic year of ED encounters (~20,000 visits) was built with realistic arrival seasonality,
ESI acuity mix, and shift-dependent staffing, then analyzed in SQL to break door-to-provider time
into its three stages — door-to-triage, triage-to-room, room-to-physician — by shift. A
queueing-utilization pass and Kruskal-Wallis/Tukey HSD/chi-square testing confirmed which resource
was actually saturated, rather than assuming. A discrete-event simulation (SimPy) then modeled the
ED as a three-stage queueing network and tested a specific staffing intervention across 20
replications for statistical confidence.

## Result

Physician capacity — not beds or triage nursing — was the binding constraint on the Evening shift
(utilization ρ = 0.82 vs. 0.14 for beds), confirmed statistically (Kruskal-Wallis p < 0.001).
Adding one physician-equivalent (an advanced practice provider) to that shift alone reduced average
door-to-provider time by **20.7%** (74.3 → 59.0 min) and cut the LWBS rate by **59.7% relative**
(3.98% → 1.60%), with non-overlapping 95% confidence intervals between baseline and scenario. Net
of the added staffing cost, the simulated fix recovers an estimated **$565.8K in annual revenue**
at a 20,000-visit ED.

## Dashboard

[`dashboard.html`](./dashboard.html) — the live dashboard for this project.

## A note on what's in this repo

The analysis above was built with SQL (stage-by-stage wait-time breakdown, Kruskal-Wallis/Tukey
HSD testing) and a SimPy discrete-event simulation. Those SQL scripts and the simulation notebook
aren't currently uploaded to this repo — only this write-up and the dashboard are. Flagging this
honestly rather than implying there's a reproducible pipeline here to inspect; if the underlying
code gets uploaded later, this note should be replaced with a real repo-structure section like the
LOS Prediction and Care-Gap Prediction projects have.
