"""
generate_dashboard_charts.py
-----------------------------
Builds the static chart images used in dashboard.html from the actual
claims dataset (no placeholders / mockups) — matches the pattern used by
the ed-throughput-analysis project's dashboard page.
"""

import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---- Brand-neutral, professional palette (navy / teal / coral accents) ----
NAVY = "#1f3a5f"
TEAL = "#2a9d8f"
CORAL = "#e76f51"
GRAY = "#6b7280"
LIGHTGRID = "#e5e7eb"
BG = "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": LIGHTGRID,
    "axes.labelcolor": "#374151",
    "text.color": "#1f2937",
    "xtick.color": "#374151",
    "ytick.color": "#374151",
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
})

conn = sqlite3.connect("data/claims.db")
df = pd.read_sql("SELECT * FROM fact_claims", conn)
conn.close()

df["claim_submission_date"] = pd.to_datetime(df["claim_submission_date"])
df["month"] = df["claim_submission_date"].dt.to_period("M").astype(str)

OUT = "assets"
import os
os.makedirs(OUT, exist_ok=True)

# 1. Denial rate trend by month -------------------------------------------
monthly = df.groupby("month").apply(
    lambda g: 100 * (g.first_pass_status == "Denied").mean()
).reset_index(name="denial_rate")

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(monthly["month"], monthly["denial_rate"], color=CORAL, linewidth=2.5, marker="o", markersize=4)
ax.axhline(10, color=GRAY, linestyle="--", linewidth=1, label="10% target")
ax.set_title("Denial Rate Trend by Month", fontsize=13, fontweight="bold", loc="left", color=NAVY)
ax.set_ylabel("Denial rate (%)")
ax.set_xticks(range(0, len(monthly), 2))
ax.set_xticklabels(monthly["month"][::2], rotation=45, ha="right", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.8)
ax.legend(frameon=False, loc="upper left", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUT}/denial_rate_trend.png", dpi=160)
plt.close()

# 2. Denial reason Pareto ---------------------------------------------------
denied = df[df.first_pass_status == "Denied"]
reason_counts = denied.denial_reason_code.value_counts().sort_values(ascending=False)
cum_pct = 100 * reason_counts.cumsum() / reason_counts.sum()

fig, ax1 = plt.subplots(figsize=(9, 4.2))
bars = ax1.bar(reason_counts.index, reason_counts.values, color=CORAL)
ax1.set_ylabel("Denied claims", color=CORAL)
ax1.tick_params(axis="y", labelcolor=CORAL)
ax1.set_title("Denial Reason Pareto (80/20)", fontsize=13, fontweight="bold", loc="left", color=NAVY)
ax1.spines[["top"]].set_visible(False)

ax2 = ax1.twinx()
ax2.plot(reason_counts.index, cum_pct.values, color=NAVY, marker="o", markersize=4, linewidth=2)
ax2.set_ylabel("Cumulative % of denials", color=NAVY)
ax2.tick_params(axis="y", labelcolor=NAVY)
ax2.yaxis.set_major_formatter(mticker.PercentFormatter())
ax2.set_ylim(0, 105)
ax2.spines[["top"]].set_visible(False)

plt.tight_layout()
plt.savefig(f"{OUT}/denial_reason_pareto.png", dpi=160)
plt.close()

# 3. Denial rate by payer ---------------------------------------------------
payer_denial = (
    df.groupby("payer_name")
    .apply(lambda g: 100 * (g.first_pass_status == "Denied").mean())
    .sort_values(ascending=False)
)
fig, ax = plt.subplots(figsize=(8, 4.5))
colors = [CORAL if v > payer_denial.mean() else TEAL for v in payer_denial.values]
ax.barh(payer_denial.index[::-1], payer_denial.values[::-1], color=colors[::-1])
ax.set_title("Denial Rate by Payer", fontsize=13, fontweight="bold", loc="left", color=NAVY)
ax.set_xlabel("Denial rate (%)")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color=LIGHTGRID, linewidth=0.8)
plt.tight_layout()
plt.savefig(f"{OUT}/denial_rate_by_payer.png", dpi=160)
plt.close()

# 4. Payer x Service line heatmap -------------------------------------------
pivot = df.pivot_table(
    index="service_line", columns="payer_name",
    values="first_pass_status", aggfunc=lambda s: 100 * (s == "Denied").mean()
)
fig, ax = plt.subplots(figsize=(9.5, 5.5))
im = ax.imshow(pivot.values, cmap="Reds", aspect="auto", vmin=0, vmax=pivot.values.max())
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
ax.set_title("Payer × Service Line Denial Rate Heatmap", fontsize=13, fontweight="bold", loc="left", color=NAVY)
cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cbar.set_label("Denial rate (%)", fontsize=9)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        val = pivot.values[i, j]
        if not pd.isna(val):
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                     fontsize=7, color="white" if val > pivot.values.max()*0.55 else "#374151")
plt.tight_layout()
plt.savefig(f"{OUT}/payer_service_line_heatmap.png", dpi=160)
plt.close()

# 5. Root cause: Meridian before/after ---------------------------------------
m = df[(df.payer_name == "Meridian Health Plan") & (df.service_line.isin(["Orthopedics", "Oncology"]))].copy()
m["period"] = m.claim_submission_date.apply(lambda d: "After Jan 2025" if d >= pd.Timestamp("2025-01-01") else "Before Jan 2025")
period_rate = m.groupby("period").apply(lambda g: 100 * (g.first_pass_status == "Denied").mean())
period_rate = period_rate.reindex(["Before Jan 2025", "After Jan 2025"])

fig, ax = plt.subplots(figsize=(5, 4.5))
bars = ax.bar(period_rate.index, period_rate.values, color=[TEAL, CORAL], width=0.55)
for b, v in zip(bars, period_rate.values):
    ax.text(b.get_x() + b.get_width()/2, v + 1.5, f"{v:.0f}%", ha="center", fontsize=12, fontweight="bold")
ax.set_title("Root Cause: Meridian Prior-Auth\nPolicy Change (Ortho + Oncology)", fontsize=12, fontweight="bold", loc="left", color=NAVY)
ax.set_ylabel("Denial rate (%)")
ax.set_ylim(0, max(period_rate.values) + 15)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.8)
plt.tight_layout()
plt.savefig(f"{OUT}/meridian_root_cause.png", dpi=160)
plt.close()

# 6. Facility eligibility gap -------------------------------------------------
fac = df[df.first_pass_status == "Denied"].groupby("facility").apply(
    lambda g: 100 * (g.denial_category == "Eligibility").mean()
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7, 4))
colors = [CORAL if v == fac.max() else TEAL for v in fac.values]
ax.barh(fac.index[::-1], fac.values[::-1], color=colors[::-1])
ax.set_title("Facility Eligibility Gap\n(% of denials that are Eligibility-related)", fontsize=12, fontweight="bold", loc="left", color=NAVY)
ax.set_xlabel("% of denials")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color=LIGHTGRID, linewidth=0.8)
plt.tight_layout()
plt.savefig(f"{OUT}/facility_eligibility_gap.png", dpi=160)
plt.close()

# 7. Turnaround time: clean vs denied-and-reworked ----------------------------
tat = df.groupby("is_clean_claim")["turnaround_days"].mean()
labels = ["Denied & reworked", "Clean (first-pass paid)"]
values = [tat.get(0, 0), tat.get(1, 0)]
fig, ax = plt.subplots(figsize=(5, 4.5))
bars = ax.bar(labels, values, color=[CORAL, TEAL], width=0.55)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width()/2, v + 1, f"{v:.1f}d", ha="center", fontsize=12, fontweight="bold")
ax.set_title("Turnaround Time:\nClean vs. Denied & Reworked", fontsize=12, fontweight="bold", loc="left", color=NAVY)
ax.set_ylabel("Avg. days to final adjudication")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=LIGHTGRID, linewidth=0.8)
plt.tight_layout()
plt.savefig(f"{OUT}/turnaround_comparison.png", dpi=160)
plt.close()

print("All charts written to", OUT)
print("Overall avg turnaround:", round(df.turnaround_days.mean(), 1), "days")
print("Clean claim avg turnaround:", round(tat.get(1), 1))
print("Denied avg turnaround:", round(tat.get(0), 1))
