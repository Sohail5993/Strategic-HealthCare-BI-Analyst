"""
coverage_map.py
----------------
Renders a simple synthetic geospatial view of the service area: member
density, Behavioral Health provider locations, and counties shaded by
compliance rate. Uses plain matplotlib scatter (no external map tiles)
since the coordinates are synthetic, not real-world geocodes.
"""

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 150

providers = pd.read_csv("../data/providers.csv")
members = pd.read_csv("../data/members.csv")
gap = pd.read_csv("../outputs/network_gap_summary.csv")

FOCUS_SPECIALTY = "Behavioral Health"

fig, ax = plt.subplots(figsize=(9, 7))

# Member density (light background scatter, sampled for render speed)
m_sample = members.sample(6000, random_state=3)
ax.scatter(m_sample["longitude"], m_sample["latitude"], s=3, alpha=0.12,
           color="#8896a8", label="Members (sampled)")

# Providers for the focus specialty
spec_p = providers[(providers["specialty"] == FOCUS_SPECIALTY)]
accepting = spec_p[spec_p["accepting_new_patients"]]
not_accepting = spec_p[~spec_p["accepting_new_patients"]]

ax.scatter(not_accepting["longitude"], not_accepting["latitude"], s=45, marker="x",
           color="#c0392b", label=f"{FOCUS_SPECIALTY} — network closed", zorder=4)
ax.scatter(accepting["longitude"], accepting["latitude"], s=55, marker="o",
           color="#1a7a5e", edgecolor="white", linewidth=0.6,
           label=f"{FOCUS_SPECIALTY} — accepting patients", zorder=5)

# Annotate county centers with compliance rate for the focus specialty.
# Manual offsets keep labels legible around the dense urban/suburban cluster.
LABEL_OFFSETS = {
    "Central Metro":   (-1.35, 0.55),
    "North Metro":     (0.95, 0.55),
    "East Suburban":   (1.55, -0.05),
    "West Suburban":   (-1.65, -0.15),
    "South Suburban":  (0.15, -0.75),
    "Millbrook County":(-1.45, -0.85),
    "Cedar Ridge Cty": (-0.05, 0.35),
    "Prairie County":  (1.15, -0.05),
}

county_gap = gap[gap["specialty"] == FOCUS_SPECIALTY].set_index("county")
counties = members.groupby("county").agg(lat=("latitude", "mean"), lon=("longitude", "mean"))
for county, row in counties.iterrows():
    if county in county_gap.index:
        pct = county_gap.loc[county, "pct_fully_compliant"]
        color = "#c0392b" if pct < 60 else ("#d68910" if pct < 80 else "#1a7a5e")
        dx, dy = LABEL_OFFSETS.get(county, (0.3, 0.3))
        ax.annotate(
            f"{county}\n{pct:.0f}% compliant",
            xy=(row["lon"], row["lat"]), xytext=(row["lon"] + dx, row["lat"] + dy),
            fontsize=7.8, ha="center", color=color, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, alpha=0.95),
            arrowprops=dict(arrowstyle="-", color=color, lw=0.8, alpha=0.8),
        )

ax.set_title(f"{FOCUS_SPECIALTY} Network Coverage vs. Member Distribution",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Longitude (synthetic service-area coordinates)")
ax.set_ylabel("Latitude (synthetic service-area coordinates)")
ax.legend(loc="upper right", fontsize=8, frameon=True)
ax.set_aspect("equal")
plt.tight_layout()
plt.savefig("../outputs/charts/06_coverage_map_behavioral_health.png")
plt.close()
print("Saved coverage map chart.")
