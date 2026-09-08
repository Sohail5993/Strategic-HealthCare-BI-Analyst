# Tableau Workbook Build Guide

> **Note on this folder:** Tableau Desktop/Public isn't available in the environment
> this repo was built in, so instead of a black-box `.twbx` file, this folder gives
> you everything needed to build the exact workbook yourself in Tableau Desktop or
> Tableau Public in about 15–20 minutes: the data model, every calculated field
> (copy/paste-ready), and a sheet-by-sheet + dashboard-layout build guide. This is
> also more valuable for a portfolio repo — a reviewer can see your *reasoning*,
> not just a finished file.
>
> Once built, save as `Denial_Rate_Analysis.twbx` (packaged workbook, embeds the
> data) in this folder, or publish to Tableau Public and link it from the main
> README.

---

## 1. Data source

Connect Tableau directly to **`/data/claims.csv`**. It's a single flat
(denormalized) fact table — one row per claim — which is the ideal shape for
Tableau; no joins are required.

| Field | Tableau role | Data type | Notes |
|---|---|---|---|
| `claim_id` | Dimension | String | Unique key |
| `patient_id`, `provider_id` | Dimension | String | |
| `facility` | Dimension | String | 4 values |
| `payer_name`, `payer_type` | Dimension | String | |
| `service_line` | Dimension | String | 10 values |
| `cpt_code`, `icd10_code` | Dimension | String | |
| `date_of_service` | Dimension | Date | |
| `claim_submission_date` | Dimension | **Date** — set this as your primary Date field for trending | |
| `billed_amount` | Measure | Number (decimal) | Gross charge |
| `paid_amount` | Measure | Number (decimal) | Actual reimbursement |
| `is_clean_claim` | Dimension | Boolean → convert to Integer for aggregation (`0`/`1`) | |
| `first_pass_status` | Dimension | String | `Paid` / `Denied` — outcome of the *first* submission |
| `denial_reason_code`, `denial_reason_description` | Dimension | String | Null when not denied |
| `denial_category` | Dimension | String | Root-cause bucket — this is your primary "why" field |
| `is_resubmitted`, `resubmission_count` | Dimension/Measure | | |
| `final_status` | Dimension | String | `Paid` / `Denied - Written Off` / `Pending Appeal` |
| `turnaround_days` | Measure | Number (integer) | Submission → final adjudication |

On import: right-click `claim_submission_date` → confirm **Date** type. Right-click
`is_clean_claim` and `is_resubmitted` → if Tableau reads them as True/False strings,
create integer versions via calculated fields (below) rather than relying on
boolean aggregation, which is easier to control in chart formatting.

---

## 2. Calculated fields

Create these under **Analysis → Create Calculated Field**. Paste the formula
exactly as written.

### Core KPIs

**`Clean Claim Rate`**
```
SUM(IF [is_clean_claim] = "True" OR [is_clean_claim] = "1" THEN 1 ELSE 0 END)
/ COUNT([Claim Id])
```
*(If Tableau already reads `is_clean_claim` as a native Boolean, simplify to
`SUM(INT([is_clean_claim])) / COUNT([Claim Id])`.)*

**`Denial Rate`**
```
1 - [Clean Claim Rate]
```

**`Collection Rate`**
```
SUM([Paid Amount]) / SUM([Billed Amount])
```

**`Avg Turnaround Days`**
```
AVG([Turnaround Days])
```

**`Denied Claims (count)`**
```
SUM(IF [First Pass Status] = "Denied" THEN 1 ELSE 0 END)
```

### Financial impact

**`Billed Amount Denied`**
```
SUM(IF [First Pass Status] = "Denied" THEN [Billed Amount] END)
```

**`Billed Amount Written Off`**
```
SUM(IF [Final Status] = "Denied - Written Off" THEN [Billed Amount] END)
```

**`Recovery Rate (of denials)`**
```
SUM(IF [First Pass Status] = "Denied" AND [Final Status] = "Paid" THEN 1 ELSE 0 END)
/ [Denied Claims (count)]
```

### Root-cause / Pareto helpers

**`% of Total Denials`** *(table calculation — set “Compute Using” to the reason
code dimension)*
```
SUM([Denied Claims (count)]) / TOTAL(SUM([Denied Claims (count)]))
```

**`Cumulative % of Denials`** *(table calc, running total of the above, sorted
descending by denial count — used for the Pareto chart)*
```
RUNNING_SUM([% of Total Denials])
```

**`Meridian Auth Spike Period`** *(supports the root-cause drill-down)*
```
IF [Payer Name] = "Meridian Health Plan"
   AND [Claim Submission Date] >= #2025-01-01#
THEN "After Policy Change (2025+)"
ELSE "Before Policy Change"
END
```

### Benchmark reference line

**`Clean Claim Benchmark (90%)`**
```
0.90
```
Use as a constant reference line on any Clean Claim Rate chart.

---

## 3. Sheets to build

Build each of these as its own worksheet, then assemble into the dashboard in
Section 4.

1. **KPI Scorecard (4 BANs / Big Number cards)**
   Text table or 4 separate single-value sheets: `Denial Rate`, `Clean Claim
   Rate`, `Collection Rate`, `Avg Turnaround Days`. Format as large bold
   numbers with a small label underneath. Color the Clean Claim Rate number
   red if `< 0.90`, green otherwise (use a calculated field for the color).

2. **Denial Rate by Payer** — Horizontal bar chart.
   Rows: `Payer Name`, Columns: `Denial Rate`. Sort descending. Color by
   `Payer Type`. Add a reference line at the overall denial rate (constant,
   ~15.5%) so payers above/below the mean are obvious at a glance.

3. **Denial Rate Trend by Month** — Line chart.
   Columns: `MONTH(Claim Submission Date)` (continuous), Rows: `Denial Rate`.
   Add a reference band or line for the 90% clean-claim-rate target (inverse:
   ~10% denial rate target). This is where the Meridian policy-change spike
   becomes visible if you add a dual-axis line filtered to Meridian +
   Ortho/Oncology.

4. **Denial Reason Pareto** — Dual-axis combo chart.
   Rows (bar): `Denied Claims (count)` by `Denial Reason Code`, sorted
   descending. Rows (line, dual axis): `Cumulative % of Denials`. This is the
   classic 80/20 chart — shows which 3–4 codes drive most of the problem.

5. **Payer × Service Line Heatmap**
   Rows: `Service Line`, Columns: `Payer Name`, Color: `Denial Rate`
   (diverging color scale, e.g. white → red). Instantly shows the Meridian /
   Orthopedics and Meridian / Oncology hot spots.

6. **Root Cause Drill-down: Meridian Prior-Auth Policy Change**
   Bar chart filtered to `Payer Name = Meridian Health Plan` and
   `Service Line` in (Orthopedics, Oncology). Columns:
   `Meridian Auth Spike Period`. Rows: `Denial Rate`. This single chart is
   your best "here's a specific, provable root cause" story for the write-up.

7. **Facility Eligibility Gap**
   Bar chart. Rows: `Facility`, Columns: `% of denials that are Eligibility
   category` (filtered calc). Surfaces the East Medical Center front-desk
   verification issue.

8. **Turnaround Time: Clean vs. Denied-and-Reworked**
   Box plot or bar chart comparing `Avg Turnaround Days` where
   `is_clean_claim = True` vs. `False`. Makes the cash-flow cost of denials
   visceral (clean ≈ 20 days vs. denied-and-reworked ≈ 52 days in this
   dataset).

---

## 4. Dashboard layout

Combine into one dashboard, **"Denial Management & Clean Claim Rate — Executive
View"**, roughly 1400×900:

```
┌───────────────────────────────────────────────────────────────────┐
│  Denial Rate │ Clean Claim Rate │ Collection Rate │ Avg TAT (days)  │  <- KPI Scorecard row
├───────────────────────────────┬──────────────────────────────────┤
│  Denial Rate Trend by Month   │   Denial Reason Pareto            │
├────────────────────┬──────────┴──────────────────────────────────┤
│  Denial Rate by     │        Payer × Service Line Heatmap         │
│  Payer               │                                            │
├────────────────────┴──────────┬─────────────────────────────────┤
│  Root Cause: Meridian Spike     │  Facility Eligibility Gap        │
└──────────────────────────────┴───────────────────────────────────┘
```
See `dashboard_wireframe.svg` in this folder for a visual reference.

**Filters to add (top of dashboard, applied to all sheets):**
- `Claim Submission Date` (relative or range date filter)
- `Payer Name` (multi-select)
- `Service Line` (multi-select)
- `Facility` (multi-select)

**Actions:** Add a dashboard filter action from the Payer × Service Line
heatmap → the other sheets, so clicking a cell (e.g. Meridian/Oncology)
cross-filters the whole dashboard to that combination.

---

## 5. What to write in the dashboard's title/subtitle

Something like: *"Denial rate is 15.5% against a 90% clean-claim-rate target.
$8.2M in billed charges were denied on first submission over the trailing 18
months, of which $6.2M was ultimately written off. The single largest
identifiable driver is a Q1 2025 prior-authorization policy change from
Meridian Health Plan affecting Orthopedics and Oncology claims — denial rate
for that payer/service-line combination jumped from ~21% to ~56%."*

That sentence is the whole point of the project: not just "here's a KPI
dashboard" but "here's a KPI dashboard that found a specific, actionable root
cause."
