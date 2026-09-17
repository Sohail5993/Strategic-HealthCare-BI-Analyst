"""
generate_data.py
-----------------
Generates synthetic health plan provider network data and member enrollment
data for a Provider Network Adequacy Analysis.

Simulates a mid-size regional health plan operating across a mix of
urban, suburban, and rural counties (modeled loosely on a US metro +
surrounding rural service area, using relative lat/long offsets so the
data is fully synthetic and does not represent real providers or patients).

Outputs (written to ../data/):
    providers.csv          - network providers by specialty/location/capacity
    members.csv             - synthetic member population by home location
    adequacy_standards.csv  - CMS/NCQA-style time & distance + wait-time
                               standards used as the benchmark
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. Service area definition: counties with a center point, county type, and
#    member population weight. Coordinates are synthetic offsets (not real
#    geocodes) around an arbitrary origin so the project stays fully
#    self-contained sample data.
# ---------------------------------------------------------------------------
COUNTIES = pd.DataFrame([
    # name,             type,       lat,     lon,     pop_weight
    ("Central Metro",   "Urban",    40.0000, -85.0000, 0.28),
    ("North Metro",     "Urban",    40.1800, -84.9200, 0.14),
    ("East Suburban",   "Suburban", 39.9700, -84.7300, 0.16),
    ("West Suburban",   "Suburban", 40.0200, -85.2600, 0.13),
    ("South Suburban",  "Suburban", 39.8200, -85.0100, 0.10),
    ("Millbrook County","Rural",    39.6000, -85.4500, 0.07),
    ("Cedar Ridge Cty", "Rural",    40.3500, -85.6000, 0.06),
    ("Prairie County",  "Rural",    39.7200, -84.4000, 0.06),
], columns=["county", "county_type", "lat", "lon", "pop_weight"])

# ---------------------------------------------------------------------------
# 2. Specialties tracked for adequacy, with relative network sizing weights
#    (primary care and behavioral health are intentionally undersized vs.
#    demand in rural counties to create realistic adequacy gaps to analyze).
# ---------------------------------------------------------------------------
SPECIALTIES = pd.DataFrame([
    # specialty,                category,          urban_n, suburban_n, rural_n, avg_panel_cap
    ("Primary Care",             "Primary Care",     55,      34,         9,      1800),
    ("OB/GYN",                   "Primary Care",     18,      11,         2,      1500),
    ("Behavioral Health",        "Behavioral",        22,      12,         2,      900),
    ("Cardiology",                "Specialty",        16,      8,          1,      1200),
    ("Endocrinology",             "Specialty",        9,       4,          0,      1100),
    ("Oncology",                  "Specialty",        8,       3,          0,      1000),
    ("Orthopedics",                "Specialty",        14,      7,          1,      1300),
    ("Dermatology",                "Specialty",        12,      6,          1,      1400),
    ("General Surgery",            "Specialty",        10,      5,          1,      1200),
    ("Neurology",                   "Specialty",        7,       3,          0,      1000),
], columns=["specialty", "category", "urban_n", "suburban_n", "rural_n", "avg_panel_cap"])

COUNTY_TYPE_N_COL = {"Urban": "urban_n", "Suburban": "suburban_n", "Rural": "rural_n"}

# ---------------------------------------------------------------------------
# 3. Generate providers: scatter around each county center with jitter,
#    assign panel capacity, accepting-new-patients flag, and a synthetic
#    "next available appointment" wait time (days) skewed by specialty
#    and county type (rural + high-demand specialties wait longer).
# ---------------------------------------------------------------------------
WAIT_TIME_BASE = {
    "Primary Care": 6, "OB/GYN": 10, "Behavioral Health": 14,
    "Cardiology": 12, "Endocrinology": 15, "Oncology": 5,
    "Orthopedics": 9, "Dermatology": 16, "General Surgery": 8, "Neurology": 18,
}
COUNTY_TYPE_WAIT_MULT = {"Urban": 1.0, "Suburban": 1.15, "Rural": 1.6}
COUNTY_TYPE_JITTER_DEG = {"Urban": 0.06, "Suburban": 0.10, "Rural": 0.22}

rows = []
provider_id = 1000
for _, county in COUNTIES.iterrows():
    for _, spec in SPECIALTIES.iterrows():
        n = spec[COUNTY_TYPE_N_COL[county["county_type"]]]
        for _ in range(int(n)):
            jitter = COUNTY_TYPE_JITTER_DEG[county["county_type"]]
            lat = county["lat"] + RNG.normal(0, jitter)
            lon = county["lon"] + RNG.normal(0, jitter)
            base_wait = WAIT_TIME_BASE[spec["specialty"]]
            mult = COUNTY_TYPE_WAIT_MULT[county["county_type"]]
            wait_days = max(1, int(RNG.gamma(shape=3.2, scale=(base_wait * mult) / 3.2)))
            panel_cap = int(RNG.normal(spec["avg_panel_cap"], spec["avg_panel_cap"] * 0.15))
            panel_cap = max(200, panel_cap)
            accepting = RNG.random() > (0.22 if county["county_type"] == "Rural" else 0.10)
            provider_id += 1
            rows.append({
                "provider_id": f"PRV-{provider_id}",
                "specialty": spec["specialty"],
                "category": spec["category"],
                "county": county["county"],
                "county_type": county["county_type"],
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "panel_capacity": panel_cap,
                "accepting_new_patients": accepting,
                "next_available_appt_days": wait_days,
                "telehealth_available": bool(RNG.random() > 0.45),
            })

providers = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 4. Generate members: population scattered around county centers,
#    proportional to county pop_weight, total plan membership ~48,000.
# ---------------------------------------------------------------------------
TOTAL_MEMBERS = 48000
member_rows = []
member_id = 500000
for _, county in COUNTIES.iterrows():
    n_members = int(TOTAL_MEMBERS * county["pop_weight"])
    jitter = COUNTY_TYPE_JITTER_DEG[county["county_type"]] * 1.3
    lats = county["lat"] + RNG.normal(0, jitter, n_members)
    lons = county["lon"] + RNG.normal(0, jitter, n_members)
    for i in range(n_members):
        member_id += 1
        member_rows.append({
            "member_id": f"MBR-{member_id}",
            "county": county["county"],
            "county_type": county["county_type"],
            "latitude": round(lats[i], 5),
            "longitude": round(lons[i], 5),
            "plan_type": RNG.choice(["HMO", "PPO", "Medicaid MCO", "Medicare Advantage"],
                                     p=[0.34, 0.26, 0.24, 0.16]),
        })

members = pd.DataFrame(member_rows)

# ---------------------------------------------------------------------------
# 5. Adequacy standards benchmark table (modeled on CMS Medicare Advantage
#    Network Adequacy time & distance criteria and common state Medicaid
#    MCO appointment wait-time standards; simplified for portfolio use).
# ---------------------------------------------------------------------------
standards = pd.DataFrame([
    # specialty,              county_type, max_distance_miles, max_drive_minutes, max_wait_days, min_providers_per_1000
    ("Primary Care",          "Urban",     10,  20, 10, 0.55),
    ("Primary Care",          "Suburban",  15,  30, 10, 0.55),
    ("Primary Care",          "Rural",     30,  60, 14, 0.45),
    ("OB/GYN",                 "Urban",     10,  20, 14, 0.20),
    ("OB/GYN",                 "Suburban",  20,  30, 14, 0.18),
    ("OB/GYN",                 "Rural",     45,  75, 21, 0.12),
    ("Behavioral Health",      "Urban",     10,  20, 10, 0.30),
    ("Behavioral Health",      "Suburban",  20,  30, 10, 0.25),
    ("Behavioral Health",      "Rural",     45,  75, 14, 0.15),
    ("Cardiology",              "Urban",     15,  30, 14, 0.15),
    ("Cardiology",              "Suburban",  30,  45, 14, 0.12),
    ("Cardiology",              "Rural",     60,  90, 21, 0.08),
    ("Endocrinology",           "Urban",     15,  30, 21, 0.08),
    ("Endocrinology",           "Suburban",  30,  45, 21, 0.06),
    ("Endocrinology",           "Rural",     70,  100,30, 0.03),
    ("Oncology",                 "Urban",     15,  30, 10, 0.06),
    ("Oncology",                 "Suburban",  30,  45, 10, 0.05),
    ("Oncology",                 "Rural",     75,  100,14, 0.02),
    ("Orthopedics",               "Urban",     15,  30, 14, 0.10),
    ("Orthopedics",               "Suburban",  30,  45, 14, 0.09),
    ("Orthopedics",               "Rural",     60,  90, 21, 0.05),
    ("Dermatology",                "Urban",     15,  30, 21, 0.09),
    ("Dermatology",                "Suburban",  30,  45, 21, 0.08),
    ("Dermatology",                "Rural",     70,  100,28, 0.04),
    ("General Surgery",             "Urban",     15,  30, 14, 0.08),
    ("General Surgery",             "Suburban",  30,  45, 14, 0.07),
    ("General Surgery",             "Rural",     60,  90, 21, 0.04),
    ("Neurology",                    "Urban",     20,  35, 21, 0.05),
    ("Neurology",                    "Suburban",  35,  50, 21, 0.04),
    ("Neurology",                    "Rural",     80,  110,30, 0.02),
], columns=["specialty", "county_type", "max_distance_miles", "max_drive_minutes",
            "max_wait_days", "min_providers_per_1000"])

# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
providers.to_csv("../data/providers.csv", index=False)
members.to_csv("../data/members.csv", index=False)
standards.to_csv("../data/adequacy_standards.csv", index=False)

print(f"Providers generated: {len(providers):,}")
print(f"Members generated:   {len(members):,}")
print(f"Standards rows:      {len(standards):,}")
print("\nProvider counts by specialty x county type:")
print(providers.groupby(["specialty", "county_type"]).size().unstack(fill_value=0))
