# Emergency Department Throughput Bottleneck Analysis

**Category:** Access & Network / Operations

Traces where patients lose time between arrival and physician contact — door-to-triage, triage-to-room, room-to-physician — and simulates staffing changes against a limited budget to find the shift where one added provider cuts wait time the most, rather than spreading headcount thin across every hour.

**[→ Open the interactive dashboard](./dashboard.html)**

## Headline results

| Metric | Value |
|---|---|
| Avg door-to-provider time reduction | **-20.7%** (74.3 → 59.0 min, simulated) |
| LWBS rate reduction | **-59.7% relative** (3.98% → 1.60%) |
| Est. net annual benefit | **$565,793** (revenue recovered − added staffing cost) |

---

## 1. Problem

A mid-size community ED (~20,000 annual visits) is losing patients to left-without-being-seen (LWBS) and running average door-to-provider times well above published benchmarks, concentrated in a specific shift. Leadership has budget for **one** additional staff position and needs evidence for *where* to put it — more triage nurses, more beds, or more physician coverage — rather than a generic "hire more people" recommendation.

## 2. Data

Since real ED-level timestamp data is protected health information, this project uses a **synthetic dataset** (`data/ed_visits_synthetic.csv`, 19,867 visits over one simulated year) built to match published operational patterns:

- Non-homogeneous Poisson arrivals with realistic hour-of-day / day-of-week seasonality (afternoon/evening peaks, Monday-heaviest week)
- ESI acuity mix based on national distributions (ESI 1: 1%, ESI 2: 20%, ESI 3: 50%, ESI 4: 24%, ESI 5: 5%)
- Right-skewed (lognormal) stage-time distributions, shift-dependent staffing levels, and an acuity-weighted LWBS mechanism
- Overall LWBS rate calibrated to **3.68%**, average door-to-provider **136 minutes** — both within the range reported in CDC/NHAMCS and ACEP ED-operations benchmarks for a moderately crowded ED

Generator: `scripts/01_generate_synthetic_data.py`

## 3. Bottleneck identification (descriptive + statistical)

Loaded into SQLite and analyzed with SQL + Python (`scripts/02_bottleneck_analysis.py`):

| Shift | Avg door-to-provider | LWBS rate |
|---|---|---|
| Night (00–08) | 69 min | 0.24% |
| Day (08–16) | 134 min | 2.73% |
| **Evening (16–24)** | **162 min** | **5.89%** |

**The Evening shift is the bottleneck**, and the gap versus overnight is driven disproportionately by room-to-physician time (+42.0 min) — more than triage-to-room (+30.0 min) or door-to-triage (+21.5 min) individually.

A queueing-utilization pass confirms this: physician utilization (ρ) runs at **0.80–0.82** on Day/Evening shifts, versus 0.14 for beds and ~0.5 for triage nurses — physician bandwidth, not beds or nursing, is the binding constraint.

Statistical tests confirm this isn't noise:
- **Kruskal-Wallis**: shift has a significant effect on room-to-physician time (H = 2414.1, p < 0.001)
- **Tukey HSD post-hoc**: Evening is significantly worse than Day (+12.6 min, p < 0.001) and Night (+42.0 min, p < 0.001)
- **Chi-square**: shift significantly predicts LWBS outcome (χ² = 219.3, p < 0.001)

## 4. Simulation (prescriptive)

A discrete-event queueing simulation (`scripts/03_simulation.py`, built with SimPy) models the ED as a three-stage network — triage nurses → beds → physicians — with shift-varying capacity and acuity-weighted patient reneging (leaving before being seen). It was calibrated to reproduce the same qualitative pattern as the historical data (Evening worst, physician-driven) and then used to test a concrete intervention.

**Tested scenario:** add one physician-equivalent (an advanced practice provider) to the Evening shift only, leaving triage and bed staffing unchanged.

Run as 20 independent 120-day replications per arm for statistical confidence:

| | Baseline | +1 Evening APP | Change |
|---|---|---|---|
| Avg door-to-provider | 74.3 min (95% CI 73.3–75.4) | 59.0 min (95% CI 57.5–60.4) | **-15.4 min (-20.7%)** |
| LWBS rate | 3.98% (95% CI 3.78–4.17%) | 1.60% (95% CI 1.40–1.81%) | **-2.37 pts (-59.7% relative)** |

The 95% confidence intervals do not overlap for either metric — this is a statistically robust effect, not simulation noise.

## 5. Revenue impact

| | Value |
|---|---|
| Est. annual visits | 20,104 |
| Est. LWBS visits avoided/year | 477 |
| Revenue recovered/year (@ $1,500/visit assumption*) | $715,793 |
| Added provider cost/year (blended APP, ~1.4 FTE to cover 1 daily 8h shift) | $150,000 |
| **Net annual benefit** | **$565,793** |

*\*$1,500/visit is a stated, documented assumption for average net revenue per completed ED encounter, used for illustration — not a claim about any specific hospital's payer mix or reimbursement rates. In a real engagement this would be pulled from the hospital's own revenue-cycle data.*

## 6. Recommendations

1. **Add one physician-equivalent (APP/PA) to the Evening shift**, not more triage nurses or beds — the utilization analysis shows those resources have headroom; physician bandwidth is the binding constraint.
2. **Pilot a low-acuity fast-track lane** staffed by the added APP to pull ESI 4–5 patients out of the main physician queue, protecting capacity for higher-acuity patients.
3. **Re-run this analysis quarterly** as seasonal volume shifts — the Evening bottleneck reflects current demand, not a fixed structural fact.
4. **Track LWBS rate as a leading indicator** alongside average wait time — it responded far more sharply to the intervention (-60% relative vs. -21%), making it a more sensitive signal of crowding relief.

## Repo structure

```
ed-throughput-analysis/
├── README.md                  # this file
├── dashboard.html             # interactive dashboard (Chart.js, static — open directly or via GitHub Pages)
├── data/
│   └── ed_visits_synthetic.csv
├── scripts/
│   ├── 01_generate_synthetic_data.py
│   ├── 02_bottleneck_analysis.py    # SQL + Kruskal-Wallis/Tukey/chi-square
│   └── 03_simulation.py             # SimPy discrete-event simulation
├── output/
│   ├── shift_summary.csv
│   ├── utilization_by_shift.csv
│   └── simulation_results.json
└── images/
    ├── stage_breakdown_by_shift.png
    ├── lwbs_by_shift.png
    ├── utilization_by_shift.png
    └── simulation_before_after.png
```

## Tools

Python (pandas, numpy, scipy, statsmodels, SimPy) for data generation, statistical testing, and simulation; SQLite for the descriptive SQL layer; Chart.js for the dashboard. The same `shift_summary.csv` / `utilization_by_shift.csv` outputs are structured to drop directly into Power BI or Tableau if a native `.pbix`/`.twbx` file is preferred for a specific audience.

## Limitations

This uses synthetic data calibrated to published benchmark *ranges*, not a real hospital's records — the specific minute-values and dollar figures are illustrative of the method, not a claim about any actual facility. The historical dataset (Section 3) and the simulation engine (Section 4) use independently calibrated mechanics — they agree on the qualitative story (Evening shift, physician-driven) but are not numerically identical by construction, which is standard practice when a simulation is a separate what-if tool rather than a literal replay of history.
