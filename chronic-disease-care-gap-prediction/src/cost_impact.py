"""
cost_impact.py
----------------
Simulates the financial return of a care-gap outreach program (proactive
calls/reminders to close screening/follow-up gaps) at different enrollment
capacity tiers, mirroring the readmission project's cost/impact framework.

Assumptions (documented, illustrative):
    - Avg. cost of a downstream complication from a persistently missed
      chronic-disease screening/follow-up: $8,400 (blended across
      diabetic retinopathy, CKD progression, uncontrolled HTN events, etc.)
    - Cost per patient enrolled in outreach (nurse call + reminder logistics): $65
    - Relative risk reduction in missing the service for enrolled patients: 35%
      (proactive outreach literature for care-gap closure programs)
    - Complication probability given a missed service, over a 12-month horizon: 18%
    - Annualized to a panel of 50,000 chronic disease patients

Outputs:
    ../reports/metrics/cost_impact_analysis.csv
    ../reports/figures/05_roi_by_capacity.png
"""

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 150

# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------
COST_PER_COMPLICATION = 8400
COST_PER_ENROLLED = 65
RELATIVE_RISK_REDUCTION = 0.35
COMPLICATION_PROB_IF_MISSED = 0.18
PANEL_SIZE = 50000

artifact = joblib.load("../models/best_care_gap_model.joblib")
y_test = artifact["y_test"].to_numpy()
proba = artifact["proba_test"]

n_test = len(y_test)
scale = PANEL_SIZE / n_test  # scale the test cohort's economics up to a full panel

capacity_tiers = [0.05, 0.10, 0.15, 0.20, 0.30]
rows = []

order = np.argsort(-proba)
y_sorted = y_test[order]

for tier in capacity_tiers:
    k = int(n_test * tier)
    enrolled_true_misses = y_sorted[:k].sum()  # true positives enrolled
    n_enrolled = k

    complications_averted = enrolled_true_misses * COMPLICATION_PROB_IF_MISSED * RELATIVE_RISK_REDUCTION
    gross_savings = complications_averted * COST_PER_COMPLICATION
    program_cost = n_enrolled * COST_PER_ENROLLED
    net_savings = gross_savings - program_cost
    roi = gross_savings / program_cost if program_cost > 0 else np.nan

    rows.append({
        "capacity_tier_pct": int(tier * 100),
        "n_enrolled_test": n_enrolled,
        "true_misses_enrolled_test": int(enrolled_true_misses),
        "precision_at_tier": round(enrolled_true_misses / n_enrolled, 3),
        "annualized_n_enrolled": int(n_enrolled * scale),
        "annualized_gross_savings": round(gross_savings * scale, -2),
        "annualized_program_cost": round(program_cost * scale, -2),
        "annualized_net_savings": round(net_savings * scale, -2),
        "roi": round(roi, 2),
    })

df = pd.DataFrame(rows)
df.to_csv("../reports/metrics/cost_impact_analysis.csv", index=False)
print(df.to_string(index=False))

best_tier = df.loc[df["roi"].idxmax()]
print(f"\nBest ROI tier: {int(best_tier['capacity_tier_pct'])}% "
      f"({best_tier['roi']:.2f}x ROI, ${best_tier['annualized_net_savings']:,.0f} annual net savings)")

# ---------------------------------------------------------------------------
# Chart: ROI and net savings by capacity tier
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = ["#C96F14" if t == best_tier["capacity_tier_pct"] else "#2C5F8A" for t in df["capacity_tier_pct"]]
bars = ax.bar([f"{t}%" for t in df["capacity_tier_pct"]], df["roi"], color=colors)

for bar, roi_val, savings in zip(bars, df["roi"], df["annualized_net_savings"]):
    ax.text(bar.get_x() + bar.get_width() / 2, roi_val + 0.05, f"{roi_val:.2f}x ROI",
            ha="center", fontsize=10, fontweight="bold")
    ax.text(bar.get_x() + bar.get_width() / 2, roi_val * 0.5, f"${savings/1000:,.0f}K",
            ha="center", fontsize=9, color="white")

ax.set_ylabel("Return on Investment (ROI)")
ax.set_xlabel("Outreach Program Capacity Tier (% of chronic disease panel enrolled)")
ax.set_title("ROI vs. Net Savings by Outreach Capacity Tier\n(labels: ROI multiple / annualized net savings)",
              fontsize=12, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("../reports/figures/05_roi_by_capacity.png")
plt.close()
print("\nSaved ROI chart.")
