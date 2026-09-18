# Electronic Health Records (EHR) / Patient Outcomes Analysis

**Cleaning a deliberately messy EHR extract with a full audit trail, then finding who a
limited-capacity care-management team should call first.**

## The business problem

Most healthcare analyst roles start here: a raw EHR extract that's genuinely messy — inconsistent
formatting, missing values, duplicate records, mixed date formats from merged source systems —
before any of the interesting demographic, diagnosis, or cost-driver analysis can happen. A
limited-capacity care-management team needed a concrete answer to who to call first, not just a
clean dataset.

## Approach

A synthetic 8,323-encounter dataset was built with realistic clinical data-quality problems on
purpose — 10 different gender formattings, 3 mixed date formats, impossible ages and lengths of
stay, duplicate records — then cleaned with every decision logged to an audit trail rather than
applied silently. The cleaned data was analyzed for cost drivers (ANOVA, linear regression) and
length-of-stay patterns by comorbidity burden (Kruskal-Wallis), then used to define a rule-based
cohort of high-cost, high-complexity patients.

## Result

Just **3.7% of patients (149 people)** account for **25% of total spend**, and that same cohort
carries a **47% 30-day readmission rate** versus 22.5% for everyone else — more than double the
risk. Length of stay turned out to be the dominant cost lever (**+$3,539 per additional day**),
with comorbidity count driving cost mainly indirectly, through its effect on length of stay rather
than as an independent factor.

## Dashboard

[`dashboard.html`](./dashboard.html) — the live dashboard for this project.

## A note on what's in this repo

The analysis above was built with a Python data-cleaning pipeline (with audit-trail logging) and
statistical testing (ANOVA, linear regression, Kruskal-Wallis). That code and the underlying
dataset aren't currently uploaded to this repo — only this write-up and the dashboard are.
Flagging this honestly rather than implying there's a reproducible pipeline here to inspect; if the
underlying code gets uploaded later, this note should be replaced with a real repo-structure
section like the LOS Prediction and Care-Gap Prediction projects have.
