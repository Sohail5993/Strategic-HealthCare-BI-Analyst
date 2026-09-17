# Care-Gap Prediction for Chronic Disease Management

**Identifying which chronic-disease patients are most likely to miss their next screening or
follow-up service — before the gap opens.**

## The business problem

Chronic disease programs (diabetes, CKD, hypertension, COPD) run on a steady cadence of screenings
and follow-ups — HbA1c tests, retinal exams, flu vaccinations, medication refills. Care management
teams can't call every patient in a 50,000-person panel every month, so the real question isn't
"who has an open care gap" (that's just a query) — it's **who is actually going to miss their next
one, so outreach capacity gets spent on the patients who need it, not the ones who'd have shown up
anyway.**

This project builds a model to answer that question and translates it into a capacity-constrained
outreach plan: given a fixed number of outreach calls a care team can realistically make, who
should get one?

## Data note

All data is synthetic (15,000 simulated chronic-disease patients with condition mix, adherence
history, no-show history, and access barriers like transportation and language). No real patient
data was used at any stage.

## Repo structure

```
data/      -- patients.csv (15,000 synthetic patients, 19 raw features)
src/       -- feature_engineering.py, train_pipeline.py, evaluate.py,
              shap_interactions.py, cost_impact.py
models/    -- best_care_gap_model.joblib (trained model + held-out test predictions)
reports/   -- one-pager PDF, build script, figures/, metrics/ (all CSV/JSON, real output)
README.md  -- this file
```

## Methodology at a glance

| Stage | What was built |
|---|---|
| Feature engineering | 39 features from 19 raw fields — adherence history, no-show pattern, access barriers, engagement signals |
| Modeling | Logistic Regression, Random Forest, XGBoost — compared on a 12,000/3,000 train/test split |
| Explainability | SHAP feature importance on the best model |
| Business translation | Capacity-tiered outreach simulation with a documented, illustrative cost model |

## Modeling results

**Target:** will this patient miss their next scheduled service? (`missed_next_service`, base rate
**34.6%** — not a rare-event problem like the extended-stay classifiers elsewhere in this
portfolio, which is part of why simpler models hold up well here.)

| Model | ROC-AUC | PR-AUC | Precision @ top 10% | Precision @ top 20% |
|---|---|---|---|---|
| **Logistic Regression** | **0.716** | **0.583** | **0.70** | 0.613 |
| Random Forest | 0.711 | 0.569 | 0.66 | 0.595 |
| XGBoost | 0.707 | 0.567 | 0.683 | **0.602** |

The linear model wins here, and it's worth saying plainly why rather than defaulting to "XGBoost is
usually better": with a 35% base rate and mostly monotonic risk factors (longer since last visit,
more prior no-shows → higher risk), there isn't much non-linear interaction for a tree ensemble to
exploit, and the simpler model generalizes at least as well on this synthetic panel. **Precision at
the top 10% (0.70)** is the operationally relevant number — call the 10% of the panel the model
flags as highest-risk, and 7 in 10 of those calls reach someone who genuinely would have missed
their service.

### What drives the prediction (SHAP)

Ranked by mean absolute SHAP value, the top drivers are **days since last visit**, **prior no-show
history**, **days since the last reminder was sent**, **number of open care gaps**, and
**medication adherence (PDC)** — followed by access barriers (transportation, distance to clinic,
having a reminder contact on file, having an assigned PCP, language barrier). This matches clinical
intuition: recency and engagement history dominate, and structural access barriers matter but are
secondary to whether the patient is already disengaging.

## Business impact translation — capacity-tiered, not one number

Rather than a single "here's the savings" figure, the model is evaluated at five different outreach
capacity levels, because a care team's real constraint is *how many calls they can make*, not
whether the model works:

| Outreach capacity (% of panel enrolled) | Precision | Annualized net savings* | ROI |
|---|---|---|---|
| 5% | 78.7% | $878,300 | **6.4x** |
| 10% | 70.0% | $1,527,200 | 5.7x |
| 15% | 64.4% | $2,070,300 | 5.25x |
| 20% | 61.3% | $2,595,800 | 4.99x |
| 30% | 56.1% | $3,479,100 | 4.57x |

*Annualized to a 50,000-patient panel, using the test set's precision at each tier scaled up.

**The honest read of this table:** ROI is highest at the smallest, most targeted tier and declines
as more of the panel gets enrolled — exactly what you'd expect, since the model is ranking patients
by risk and the marginal patient enrolled at 30% capacity is a much weaker bet than the marginal
patient enrolled at 5%. There's no single "right" tier; it's a genuine trade-off between total
dollars saved and efficiency per dollar that a care management team would decide based on actual
staffing capacity, not something this model can decide for them.

**Assumptions behind the dollar figures (stated explicitly, not buried):** an average complication
cost of $8,400 for a persistently missed chronic-disease service, a $65 cost per patient enrolled in
outreach, a 35% relative risk reduction from outreach (drawn from care-gap-closure program
literature, not measured in this data), and an 18% probability of a complication given a missed
service over 12 months. Change any of these and the dollar figures move — the ROI *ordering* across
tiers is more robust than the absolute numbers.

## Limitations

1. **Synthetic population** — 15,000 simulated patients with generated behavior patterns; real
   patient populations will have messier, less monotonic relationships between the features here
   and actual no-show behavior.
2. **Cost assumptions are illustrative, not measured** — the 35% risk-reduction figure in particular
   is a literature-based assumption, not something observed in a pilot. Any real budget conversation
   needs a pilot program or a literature review specific to the services in question, not this
   number taken at face value.
3. **No fairness/subgroup audit yet** — access-barrier features (transportation, language,
   distance) are meaningful predictors here, which is clinically expected, but also means an audit
   of false-negative rates across these same subgroups hasn't been done. This is the same category
   of gap flagged in the LOS Prediction project's fairness section, and should be treated the same
   way before deployment: a concrete to-do, not a footnote.
4. **Single time horizon** — the model predicts missing the *next* service, not a longer-term
   trajectory of disengagement; it doesn't distinguish a one-off missed appointment from a patient
   who's dropping out of care entirely.

## What would come next

- Run the fairness/subgroup audit flagged above (transportation barrier, language barrier, and
  insurance type, at minimum) before treating this as deployment-ready.
- Replace the 35% risk-reduction assumption with a measured number from a small pilot cohort.
- Test whether a longer-horizon "disengagement risk" target (missing 2+ consecutive services)
  identifies a meaningfully different, and possibly higher-value, patient group than single-miss
  prediction.

---

*Built with pandas, scikit-learn, XGBoost, SHAP, and matplotlib. All data synthetic.*
