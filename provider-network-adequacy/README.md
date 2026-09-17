# Provider Network Adequacy Analysis

**Evaluating whether a payer's provider network meets access standards across specialty, distance, and wait-time thresholds.**

*Strategic HealthCare BI Analyst Portfolio Project — Sohail*
*Transforming HealthCare Complexities into Growth Blueprints*

---

## Business Problem

Health plans are required — by CMS (Medicare Advantage), state Medicaid contracts, and NCQA accreditation standards — to prove their provider networks give members *reasonable access* to care. "Reasonable access" is typically defined across three dimensions:

1. **Distance / drive time** — how far is the nearest in-network, accepting provider?
2. **Appointment wait time** — how long until the next available appointment?
3. **Provider-to-member ratio** — is there enough capacity per specialty per 1,000 members?

Failing these standards risks regulatory penalties, corrective action plans, and — more importantly — real barriers to member care. This project simulates a regional payer's network and tests it against all three dimensions simultaneously, the way a network adequacy or provider strategy team would ahead of a state filing or CMS bid submission.

## Headline Finding

> **The network looks adequate on paper but isn't adequate in practice.**

| Dimension | Compliance Rate |
|---|---|
| Distance to nearest provider | **99.7%** ✅ |
| Provider-to-member ratio (headcount) | **100%** ✅ |
| Appointment wait time | **78.6%** ⚠️ |
| **Fully compliant (all standards met)** | **78.3%** |

The plan has plenty of providers within driving distance and technically meets minimum panel-size ratios — but a sizable share of members can't get an appointment within the required window. **Capacity on the roster isn't the same as capacity a member can actually use.** This is the single most common gap real network adequacy filings run into, and it's the one distance-only analyses miss entirely.

### Where it breaks down
- **Neurology and Behavioral Health** are non-compliant across nearly every county type (as low as 19–43% compliant), driven almost entirely by long waits (22–46 days) rather than distance.
- **Suburban counties compliance (70.5%) is worse than rural (85.7%)** — a counterintuitive result. Suburban demand is dense enough to overwhelm a comparatively thin specialist panel, while rural counties, despite having far fewer providers, also have far fewer members competing for those slots.
- **OB/GYN** access lags in the two rural counties (Millbrook, Cedar Ridge) — worth flagging given the acuity of delayed prenatal care.

See `outputs/network_gap_summary.csv` for the full ranked list of every county × specialty combination.

## Methodology

1. **Synthetic data generation** (`scripts/generate_data.py`)
   - 672 providers across 10 specialties, 8 counties (urban/suburban/rural mix), with panel capacity, accepting-new-patients status, and a simulated "next available appointment" wait time skewed by specialty demand and geography.
   - 48,000 synthetic members geographically distributed to mirror realistic county population density.
   - A benchmark standards table modeled on **CMS Medicare Advantage Time & Distance criteria** and common **state Medicaid MCO appointment wait-time standards** (simplified for portfolio use — not an official regulatory table).

2. **Adequacy analysis** (`scripts/network_adequacy_analysis.py`)
   - For a stratified sample of members (250/county), calculates **haversine distance** to the nearest accepting, in-network provider per specialty and compares it to the distance standard.
   - Compares each provider's simulated next-available-appointment wait time to the wait-time standard.
   - Aggregates **provider-to-member ratios** per county × specialty and checks against minimum ratio standards.
   - Produces a **gap score** ranking every county × specialty combination by severity, combining compliance rate and ratio failure.

3. **Geospatial visualization** (`scripts/coverage_map.py`)
   - Plots member density against provider locations for the worst-performing specialty (Behavioral Health), annotated with per-county compliance rates.

## Repository Structure

```
Provider-Network-Adequacy-Analysis/
├── README.md
├── requirements.txt
├── assets/
│   └── logo.png                   # Brand logo (transparent PNG)
├── data/
│   ├── providers.csv              # 672 synthetic network providers
│   ├── members.csv                # 48,000 synthetic member population
│   └── adequacy_standards.csv     # Distance/wait/ratio benchmark table
├── scripts/
│   ├── generate_data.py           # Synthetic data generator
│   ├── network_adequacy_analysis.py  # Core adequacy calculations + charts
│   ├── coverage_map.py            # Geospatial coverage visualization
│   ├── brand_charts.py            # Adds logo/title/tagline header to charts
│   └── build_one_pager.py         # Builds the branded PDF executive summary
└── outputs/
    ├── member_adequacy_detail.csv     # Per-member, per-specialty pass/fail
    ├── county_specialty_summary.csv   # Aggregated compliance % by county x specialty
    ├── provider_ratio_summary.csv     # Provider-to-member ratio compliance
    ├── network_gap_summary.csv        # Ranked list of worst adequacy gaps
    ├── Provider_Network_Adequacy_One_Pager.pdf   # Branded executive summary
    ├── charts/                    # Unbranded charts (6 PNGs)
    └── charts_branded/            # Same charts with logo/title/tagline header
```

## How to Run

```bash
cd scripts
python3 generate_data.py              # regenerates data/*.csv
python3 network_adequacy_analysis.py  # computes compliance + charts
python3 coverage_map.py               # renders the geospatial coverage chart
python3 brand_charts.py               # adds logo/title/tagline header to charts
python3 build_one_pager.py            # builds the branded PDF one-pager
```

Requires: `pandas`, `numpy`, `matplotlib`, `scipy`.

## Recommendations a Network Strategy Team Would Take From This

1. **Prioritize Behavioral Health and Neurology recruitment or telehealth expansion** in North Metro, West/South Suburban, and both rural counties — the wait-time gap is the binding constraint, not geography, so adding telehealth-only capacity would close most of it without new brick-and-mortar sites.
2. **Re-examine "adequate" provider ratios as a filing metric alone.** This network passes ratio standards almost everywhere yet still fails members on wait time — ratio compliance should be paired with an appointment-availability audit before every regulatory filing.
3. **Investigate suburban specialist capacity specifically** — the counterintuitive suburban-worse-than-rural pattern suggests demand modeling for future recruitment should be done at the county level, not lumped into an urban/suburban/rural bucket.

## Data Disclaimer

All provider, member, and location data in this project is **synthetically generated** for portfolio demonstration purposes. Coordinates are arbitrary offsets and do not represent real geographic locations, providers, or patients. The adequacy standards table is modeled loosely on public CMS/NCQA/Medicaid MCO frameworks but is simplified and should not be used as an authoritative regulatory reference.

---
**Contact:** strategichealthcarebianalyst@gmail.com | [LinkedIn](https://linkedin.com/in/aimms-consulting-35895439) | [Portfolio](https://sohail5993.github.io/Strategic-HealthCare-BI-Analyst/)
