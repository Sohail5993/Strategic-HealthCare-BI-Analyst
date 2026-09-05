"""
build_one_pager.py
---------------------
Builds a single-page branded PDF executive summary for the Care-Gap
Prediction project, matching the portfolio's established one-pager style
(centered logo/title/tagline header, KPI strip, headline finding, charts,
recommended actions).
"""

import json

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.pdfmetrics import stringWidth

BRAND_TITLE = "Strategic HealthCare BI Analyst"
BRAND_TAGLINE = "Transforming HealthCare Complexities into Growth Blueprints"
LOGO_PATH = "../assets/logo.png"

NAVY = colors.HexColor("#1b2a4a")
TEAL = colors.HexColor("#6C3483")  # Chronic Disease brand tag color (purple)
RED = colors.HexColor("#c0392b")
GRAY = colors.HexColor("#5b6472")
LIGHT_BG = colors.HexColor("#f4f6f8")

with open("metrics/metrics.json") as f:
    metrics = json.load(f)
with open("metrics/cost_impact_analysis.csv") as f:
    import csv
    reader = csv.DictReader(f)
    cost_rows = list(reader)

best_model_metrics = next(m for m in metrics["models"] if m["model"] == metrics["best_model"])
best_roi_row = max(cost_rows, key=lambda r: float(r["roi"]))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1Custom", parent=styles["Heading1"], fontSize=17,
                           textColor=NAVY, spaceAfter=1, leading=18))
styles.add(ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=9.5,
                           textColor=GRAY, spaceAfter=6, leading=11))
styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], fontSize=11,
                           textColor=NAVY, spaceBefore=5, spaceAfter=2, leading=12))
styles.add(ParagraphStyle("BodySmall", parent=styles["Normal"], fontSize=8.3,
                           textColor=colors.HexColor("#2b2f36"), leading=10.2))
styles.add(ParagraphStyle("BulletSmall", parent=styles["Normal"], fontSize=8.5,
                           textColor=colors.HexColor("#2b2f36"), leading=11.2,
                           leftIndent=10))
styles.add(ParagraphStyle("KpiNum", parent=styles["Normal"], fontSize=18,
                           textColor=NAVY, alignment=TA_CENTER, leading=20, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("KpiLabel", parent=styles["Normal"], fontSize=7.1,
                           textColor=GRAY, alignment=TA_CENTER, leading=8.8))
styles.add(ParagraphStyle("FooterStyle", parent=styles["Normal"], fontSize=7.3,
                           textColor=GRAY, alignment=TA_CENTER, leading=9))
styles.add(ParagraphStyle("BrandTitle", parent=styles["Normal"], fontSize=17,
                           textColor=NAVY, fontName="Helvetica-Bold", leading=19))
styles.add(ParagraphStyle("BrandTagline", parent=styles["Normal"], fontSize=9.5,
                           textColor=GRAY, fontName="Helvetica-Oblique", leading=11))

doc = SimpleDocTemplate(
    "Care_Gap_Prediction_One_Pager.pdf",
    pagesize=letter,
    topMargin=0.32 * inch, bottomMargin=0.28 * inch,
    leftMargin=0.5 * inch, rightMargin=0.5 * inch,
)

story = []

# ---------------------------------------------------------------------
# Brand header: logo + title + tagline, centered
# ---------------------------------------------------------------------
text_col_w = max(
    stringWidth(BRAND_TITLE, "Helvetica-Bold", 17),
    stringWidth(BRAND_TAGLINE, "Helvetica-Oblique", 9.5),
) + 14

logo_img = Image(LOGO_PATH, width=0.5 * inch, height=0.5 * inch * (926 / 824))
brand_text = [
    Paragraph(BRAND_TITLE, styles["BrandTitle"]),
    Paragraph(BRAND_TAGLINE, styles["BrandTagline"]),
]
brand_table = Table([[logo_img, brand_text]], colWidths=[0.55 * inch, text_col_w])
brand_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (1, 0), (1, 0), 8),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]))
brand_table.hAlign = "CENTER"
story.append(brand_table)
story.append(Spacer(1, 2))
story.append(HRFlowable(width="88%", thickness=0.8, hAlign="CENTER",
                         color=colors.HexColor("#d0d4da"), spaceAfter=10))

# ---------------------------------------------------------------------
# Project title
# ---------------------------------------------------------------------
story.append(Paragraph("Care-Gap Prediction for Chronic Disease Management", styles["H1Custom"]))
story.append(Paragraph(
    "Identifying patients likely to miss recommended screenings or follow-ups, to close gaps "
    "before they become costly complications &nbsp;|&nbsp; Sohail &mdash; Strategic HealthCare BI Analyst",
    styles["SubTitle"]))
story.append(HRFlowable(width="100%", thickness=1.1, color=NAVY, spaceAfter=8))

# ---------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------
kpis = [
    ("15,000", "Chronic Disease\nPatients Analyzed"),
    (f"{best_model_metrics['roc_auc']:.3f}", "Best ROC-AUC\n(Logistic Regression)"),
    (f"{best_model_metrics['precision_at_10pct']*100:.0f}%", "Precision @ Top 10%\n(vs. 34.6% base rate)"),
    (f"{float(best_roi_row['roi']):.2f}x", f"ROI at {best_roi_row['capacity_tier_pct']}% "
                                             f"Capacity Tier"),
    (f"${float(best_roi_row['annualized_net_savings'])/1000:,.0f}K", "Est. Annual Net Savings\n(50K-patient panel)"),
]
kpi_cells = []
for num, label in kpis:
    cell = [Paragraph(num, styles["KpiNum"]), Paragraph(label.replace("\n", "<br/>"), styles["KpiLabel"])]
    kpi_cells.append(cell)

kpi_table = Table([kpi_cells], colWidths=[1.42 * inch] * 5)
kpi_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LINEAFTER", (0, 0), (-2, 0), 0.6, colors.white),
]))
story.append(kpi_table)
story.append(Spacer(1, 2))

# ---------------------------------------------------------------------
# Headline finding callout
# ---------------------------------------------------------------------
finding_style = ParagraphStyle("Finding", parent=styles["BodySmall"], fontSize=9.2,
                                textColor=colors.white, leading=12.5)
finding_table = Table([[Paragraph(
    "<b>Headline finding:</b> An interpretable logistic regression model &mdash; trained on "
    "utilization, adherence, and access features rather than clinical severity alone &mdash; "
    "outperformed both tree ensembles at identifying which chronic disease patients will miss "
    "their next guideline-recommended screening or follow-up. Days since last visit, appointment "
    "no-show history, and reminder staleness dominate the risk signal, meaning most of the gap is "
    "closeable through outreach timing and channel &mdash; not a clinical severity problem.",
    finding_style)]],
    colWidths=[7.5 * inch])
finding_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(finding_table)
story.append(Spacer(1, 3))

# ---------------------------------------------------------------------
# Model comparison table + SHAP bar chart (left column) / ROI chart + text (right)
# ---------------------------------------------------------------------
model_rows = [["MODEL", "ROC-AUC", "PR-AUC", "PREC @ TOP 10%"]]
for m in sorted(metrics["models"], key=lambda x: -x["pr_auc"]):
    label = m["model"] + ("  BEST" if m["model"] == metrics["best_model"] else "")
    model_rows.append([label, f"{m['roc_auc']:.3f}", f"{m['pr_auc']:.3f}", f"{m['precision_at_10pct']*100:.1f}%"])

model_table = Table(model_rows, colWidths=[1.6 * inch, 0.65 * inch, 0.6 * inch, 1.1 * inch])
model_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 7.6),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#eef2f5")),
    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d4da")),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))

img_shap_bar = Image("figures/04_shap_bar.png", width=3.55 * inch, height=1.55 * inch)

left_col = [
    Paragraph("Model Comparison (Held-Out Test Set)", styles["SectionHead"]),
    model_table,
    Spacer(1, 2),
    Paragraph(
        "The interpretable baseline edged out both tree ensembles &mdash; consistent with the "
        "readmission project's finding that, at this feature-set size, linear models are "
        "competitive and easier to trust operationally.",
        styles["BodySmall"]),
    Spacer(1, 2),
    Paragraph("Top Risk Drivers (SHAP)", styles["SectionHead"]),
    img_shap_bar,
]

img_roi = Image("figures/05_roi_by_capacity.png", width=3.55 * inch, height=1.55 * inch)

right_col_flow = [
    Paragraph("Cost / Impact Simulation", styles["SectionHead"]),
    img_roi,
    Spacer(1, 2),
]
bullets = [
    "<b>Days since last visit</b> and <b>reminder staleness</b> are the two strongest drivers "
    "&mdash; both are operational levers, not clinical ones.",
    "<b>Prior no-show history</b> and <b>medication adherence (PDC)</b> confirm the model is "
    "picking up genuine behavioral risk, not just demographics.",
    "<b>Telehealth enrollment</b> and having a <b>reminder contact on file</b> both push risk "
    "down &mdash; concrete, actionable enrollment targets for the outreach team.",
    "ROI peaks at the narrowest 5% tier (6.40x) but total annual net savings keep climbing "
    "through 30% capacity &mdash; the same staffing tradeoff seen in the readmission project.",
]
for b in bullets:
    right_col_flow.append(Paragraph(f"&bull;&nbsp; {b}", styles["BulletSmall"]))
    right_col_flow.append(Spacer(1, 3))

two_col = Table([[left_col, right_col_flow]], colWidths=[3.75 * inch, 3.75 * inch])
two_col.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("LEFTPADDING", (1, 0), (1, 0), 12),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
]))
story.append(two_col)
story.append(Spacer(1, 2))

# ---------------------------------------------------------------------
# Key modeling decisions
# ---------------------------------------------------------------------
story.append(Paragraph("Key Modeling Decisions", styles["SectionHead"]))
decisions = [
    ["Why precision@K over ROC-AUC alone",
     "An outreach team can only call a fixed share of the panel each cycle. Precision at the "
     "10&ndash;20% capacity threshold reflects what matters operationally: how often the flagged "
     "list is actually right, not how the model ranks the full population."],
    ["Why the target label matches the guideline window exactly",
     "\"Missed next service\" is defined against each condition's specific guideline window "
     "(e.g., annual eye exam, semi-annual HbA1c), not a generic 30/60/90-day cutoff &mdash; so "
     "the label means the same thing a care-gap registry would flag."],
    ["Why class weighting over resampling",
     "Imbalance (34.6% positive rate) was handled via class_weight=\"balanced\" rather than "
     "synthetic oversampling, to keep predicted probabilities calibrated for risk-tiering."],
]
dec_cells = [[Paragraph(f"<b>{t}</b>", styles["BodySmall"]), ] for t, _ in decisions]
dec_table_data = [[Paragraph(f"<b>{t}</b>", ParagraphStyle("dt", parent=styles["BodySmall"], fontSize=8.3)),]
                   for t, d in decisions]
# Build as a 1-row-per-item table with title+body stacked
dec_rows = []
for t, d in decisions:
    dec_rows.append([Paragraph(f"<b>{t}</b><br/>{d}", ParagraphStyle("decbody", parent=styles["BodySmall"], fontSize=8.1, leading=10.6))])
dec_table = Table([[r[0] for r in dec_rows]], colWidths=[2.5 * inch] * 3)
dec_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(dec_table)
story.append(Spacer(1, 3))

# ---------------------------------------------------------------------
# Honest limitations
# ---------------------------------------------------------------------
story.append(Paragraph("Honest Limitations &amp; Next Steps", styles["SectionHead"]))
story.append(Paragraph(
    "<b>Synthetic data, real-shaped signal.</b> Risk-factor directions (no-show history, adherence, "
    "reminder timing) reflect published care-gap literature, but coefficients are illustrative, "
    "not fit to a real population.<br/>"
    "<b>Before production:</b> validate against a real care-gap registry with a temporal holdout, "
    "confirm the 35% relative-risk-reduction assumption against pilot data, and audit for disparate "
    "impact across insurance type and language access before setting enrollment thresholds.",
    styles["BodySmall"]))
story.append(Spacer(1, 2))

story.append(Paragraph(
    "<b>Stack:</b> Python &middot; pandas &middot; scikit-learn &middot; XGBoost &middot; SHAP &nbsp;|&nbsp; "
    "<b>Data:</b> Synthetic chronic-disease population (diabetes, hypertension, CHF, CKD, COPD) &nbsp;|&nbsp; "
    "<b>Eval:</b> ROC-AUC, PR-AUC, precision@K, cost/ROI simulation",
    styles["BodySmall"]))

# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------
story.append(Spacer(1, 2))
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d0d4da"), spaceAfter=5))
story.append(Paragraph(
    "All patient data is synthetically generated for portfolio demonstration and contains no real patient records.<br/>"
    "strategichealthcarebianalyst@gmail.com &nbsp;|&nbsp; linkedin.com/in/aimms-consulting-35895439 &nbsp;|&nbsp; "
    "sohail5993.github.io/Strategic-HealthCare-BI-Analyst/",
    styles["FooterStyle"]))

doc.build(story)
print("PDF built: Care_Gap_Prediction_One_Pager.pdf")
