"""
network_adequacy_analysis.py
-----------------------------
Evaluates whether the synthetic payer's provider network meets access
standards across three dimensions:
    1. Distance  - nearest in-network, accepting provider by specialty
                   vs. max_distance_miles standard
    2. Wait time - next available appointment vs. max_wait_days standard
    3. Provider ratio - accepting providers per 1,000 members vs.
                   min_providers_per_1000 standard

Outputs (written to ../outputs/):
    member_adequacy_detail.csv   - per-member, per-specialty pass/fail detail
                                    (sampled — see SAMPLE_MEMBERS_PER_COUNTY)
    county_specialty_summary.csv - aggregated compliance % by county x specialty
    network_gap_summary.csv      - ranked list of the worst adequacy gaps
    charts/*.png                 - supporting visuals
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams["figure.dpi"] = 150
RNG = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
providers = pd.read_csv("../data/providers.csv")
members = pd.read_csv("../data/members.csv")
standards = pd.read_csv("../data/adequacy_standards.csv")

# Only accepting, in-network providers count toward access standards
active_providers = providers[providers["accepting_new_patients"]].copy()


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles between arrays of points."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# 1. DISTANCE + WAIT-TIME COMPLIANCE (member-level, sampled for tractability)
# ---------------------------------------------------------------------------
SAMPLE_MEMBERS_PER_COUNTY = 250  # sampling keeps the O(members x providers) join fast

sampled = (
    members.groupby("county", as_index=False, group_keys=False)[members.columns.tolist()]
    .apply(lambda g: g.sample(min(len(g), SAMPLE_MEMBERS_PER_COUNTY), random_state=1))
    .reset_index(drop=True)
)

detail_rows = []
for specialty in standards["specialty"].unique():
    spec_providers = active_providers[active_providers["specialty"] == specialty]
    if spec_providers.empty:
        continue
    p_lat = spec_providers["latitude"].to_numpy()
    p_lon = spec_providers["longitude"].to_numpy()
    p_wait = spec_providers["next_available_appt_days"].to_numpy()

    for _, m in sampled.iterrows():
        dists = haversine_miles(m["latitude"], m["longitude"], p_lat, p_lon)
        nearest_idx = np.argmin(dists)
        nearest_dist = dists[nearest_idx]
        nearest_wait = p_wait[nearest_idx]

        std_row = standards[(standards["specialty"] == specialty) &
                             (standards["county_type"] == m["county_type"])]
        if std_row.empty:
            continue
        std_row = std_row.iloc[0]

        distance_pass = nearest_dist <= std_row["max_distance_miles"]
        wait_pass = nearest_wait <= std_row["max_wait_days"]

        detail_rows.append({
            "member_id": m["member_id"],
            "county": m["county"],
            "county_type": m["county_type"],
            "specialty": specialty,
            "nearest_distance_miles": round(nearest_dist, 2),
            "distance_standard_miles": std_row["max_distance_miles"],
            "distance_pass": distance_pass,
            "nearest_wait_days": int(nearest_wait),
            "wait_standard_days": std_row["max_wait_days"],
            "wait_pass": wait_pass,
            "fully_compliant": distance_pass and wait_pass,
        })

detail = pd.DataFrame(detail_rows)
detail.to_csv("../outputs/member_adequacy_detail.csv", index=False)

# ---------------------------------------------------------------------------
# 2. AGGREGATE: county x specialty compliance %
# ---------------------------------------------------------------------------
county_specialty = (
    detail.groupby(["county", "county_type", "specialty"])
    .agg(
        members_sampled=("member_id", "count"),
        pct_distance_compliant=("distance_pass", "mean"),
        pct_wait_compliant=("wait_pass", "mean"),
        pct_fully_compliant=("fully_compliant", "mean"),
        avg_nearest_distance=("nearest_distance_miles", "mean"),
        avg_nearest_wait=("nearest_wait_days", "mean"),
    )
    .reset_index()
)
for col in ["pct_distance_compliant", "pct_wait_compliant", "pct_fully_compliant"]:
    county_specialty[col] = (county_specialty[col] * 100).round(1)
county_specialty[["avg_nearest_distance", "avg_nearest_wait"]] = \
    county_specialty[["avg_nearest_distance", "avg_nearest_wait"]].round(1)

county_specialty.to_csv("../outputs/county_specialty_summary.csv", index=False)

# ---------------------------------------------------------------------------
# 3. PROVIDER-TO-MEMBER RATIO COMPLIANCE
# ---------------------------------------------------------------------------
member_counts = members.groupby("county").size().rename("member_count")
provider_counts = (
    active_providers.groupby(["county", "specialty"]).size().rename("provider_count").reset_index()
)
county_meta = members[["county", "county_type"]].drop_duplicates()

ratio = provider_counts.merge(county_meta, on="county").merge(member_counts, on="county")
ratio["providers_per_1000"] = (ratio["provider_count"] / ratio["member_count"] * 1000).round(3)
ratio = ratio.merge(
    standards[["specialty", "county_type", "min_providers_per_1000"]],
    on=["specialty", "county_type"], how="left"
)
ratio["ratio_pass"] = ratio["providers_per_1000"] >= ratio["min_providers_per_1000"]
ratio.to_csv("../outputs/provider_ratio_summary.csv", index=False)

# ---------------------------------------------------------------------------
# 4. NETWORK GAP SUMMARY — worst offenders, ranked
# ---------------------------------------------------------------------------
gap = county_specialty.merge(
    ratio[["county", "specialty", "providers_per_1000", "min_providers_per_1000", "ratio_pass"]],
    on=["county", "specialty"], how="left"
)
gap["gap_score"] = (100 - gap["pct_fully_compliant"]) + (~gap["ratio_pass"].fillna(False)).astype(int) * 15
gap = gap.sort_values("gap_score", ascending=False)
gap.to_csv("../outputs/network_gap_summary.csv", index=False)

overall_compliance = detail["fully_compliant"].mean() * 100
print(f"Overall network adequacy (distance + wait, sampled members): {overall_compliance:.1f}%")
print("\nTop 10 adequacy gaps (county x specialty):")
print(gap[["county", "specialty", "pct_fully_compliant", "avg_nearest_distance",
           "avg_nearest_wait", "ratio_pass"]].head(10).to_string(index=False))

# ===========================================================================
# CHARTS
# ===========================================================================
COLOR_PASS = "#1a7a5e"
COLOR_FAIL = "#c0392b"
COLOR_ACCENT = "#2c5f8a"
COLOR_NEUTRAL = "#6b7280"

# --- Chart 1: Overall compliance by county type -----------------------------
fig, ax = plt.subplots(figsize=(7.5, 4.5))
county_type_order = ["Urban", "Suburban", "Rural"]
compliance_by_type = (
    detail.groupby("county_type")["fully_compliant"].mean().reindex(county_type_order) * 100
)
bars = ax.bar(compliance_by_type.index, compliance_by_type.values,
              color=[COLOR_ACCENT, COLOR_ACCENT, COLOR_FAIL])
ax.axhline(90, color=COLOR_NEUTRAL, linestyle="--", linewidth=1, label="90% adequacy target")
for bar, val in zip(bars, compliance_by_type.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f"{val:.1f}%",
            ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, 100)
ax.set_ylabel("Fully Compliant Members (%)")
ax.set_title("Network Adequacy Compliance by Geography", fontsize=13, fontweight="bold")
ax.legend(loc="lower left", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("../outputs/charts/01_compliance_by_geography.png")
plt.close()

# --- Chart 2: Compliance heatmap-style bar by specialty ---------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
spec_order = (
    detail.groupby("specialty")["fully_compliant"].mean().sort_values().index
)
pivot = detail.pivot_table(index="specialty", columns="county_type",
                            values="fully_compliant", aggfunc="mean").reindex(spec_order) * 100
pivot = pivot[county_type_order]
im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(county_type_order)))
ax.set_xticklabels(county_type_order)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        val = pivot.values[i, j]
        ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                fontsize=9, color="black" if 30 < val < 80 else "white")
ax.set_title("Compliance Rate by Specialty x Geography", fontsize=13, fontweight="bold")
fig.colorbar(im, ax=ax, label="% Fully Compliant", shrink=0.8)
plt.tight_layout()
plt.savefig("../outputs/charts/02_specialty_geography_heatmap.png")
plt.close()

# --- Chart 3: Avg distance vs. wait time scatter, sized by gap -------------
fig, ax = plt.subplots(figsize=(8, 5.5))
gp = gap.dropna(subset=["avg_nearest_distance", "avg_nearest_wait"])
colors = gp["county_type"].map({"Urban": COLOR_ACCENT, "Suburban": "#5b9bd5", "Rural": COLOR_FAIL})
sizes = (100 - gp["pct_fully_compliant"]) * 4 + 20
scatter = ax.scatter(gp["avg_nearest_distance"], gp["avg_nearest_wait"],
                      c=colors, s=sizes, alpha=0.7, edgecolors="white", linewidth=0.5)
ax.set_xlabel("Avg. Distance to Nearest Provider (miles)")
ax.set_ylabel("Avg. Next Available Appointment (days)")
ax.set_title("Access Burden by County x Specialty\n(bubble size = compliance gap)",
              fontsize=13, fontweight="bold")
from matplotlib.lines import Line2D
legend_elems = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9, label=t)
                for t, c in zip(county_type_order, [COLOR_ACCENT, "#5b9bd5", COLOR_FAIL])]
ax.legend(handles=legend_elems, title="County Type", loc="upper left", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("../outputs/charts/03_access_burden_scatter.png")
plt.close()

# --- Chart 4: Provider-to-member ratio compliance ---------------------------
fig, ax = plt.subplots(figsize=(8, 5.5))
ratio_summary = ratio.groupby("county_type").apply(
    lambda g: (g["ratio_pass"].sum() / len(g)) * 100
).reindex(county_type_order)
bars = ax.barh(ratio_summary.index, ratio_summary.values,
               color=[COLOR_ACCENT, "#5b9bd5", COLOR_FAIL])
for bar, val in zip(bars, ratio_summary.values):
    ax.text(val + 1.5, bar.get_y() + bar.get_height() / 2, f"{val:.0f}%",
            va="center", fontsize=10, fontweight="bold")
ax.set_xlim(0, 100)
ax.set_xlabel("Specialty x County Combinations Meeting Min. Provider Ratio (%)")
ax.set_title("Provider-to-Member Ratio Adequacy by Geography", fontsize=13, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("../outputs/charts/04_provider_ratio_compliance.png")
plt.close()

# --- Chart 5: Top 10 worst gaps ---------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
top_gaps = gap.head(10).copy()
top_gaps["label"] = top_gaps["county"] + " — " + top_gaps["specialty"]
bars = ax.barh(top_gaps["label"][::-1], top_gaps["pct_fully_compliant"][::-1], color=COLOR_FAIL)
ax.set_xlim(0, 100)
ax.set_xlabel("Fully Compliant Members (%)")
ax.set_title("Top 10 Network Adequacy Gaps", fontsize=13, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
for bar, val in zip(bars, top_gaps["pct_fully_compliant"][::-1]):
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val:.0f}%", va="center", fontsize=9)
plt.tight_layout()
plt.savefig("../outputs/charts/05_top_gaps.png")
plt.close()

print("\nCharts written to ../outputs/charts/")
print("Analysis complete.")
