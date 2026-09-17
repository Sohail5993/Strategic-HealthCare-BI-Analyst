"""
build_one_pager.py
-------------------
Builds a polished single-page PDF executive summary of the Provider
Network Adequacy Analysis, matching the portfolio's one-pager style.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

BRAND_TITLE = "Strategic HealthCare BI Analyst"
BRAND_TAGLINE = "Transforming HealthCare Complexities into Growth Blueprints"
LOGO_PATH = "../assets/logo.png"

NAVY = colors.HexColor("#1b2a4a")
TEAL = colors.HexColor("#1a7a5e")
RED = colors.HexColor("#c0392b")
GRAY = colors.HexColor("#5b6472")
LIGHT_BG = colors.HexColor("#f4f6f8")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1Custom", parent=styles["Heading1"], fontSize=17,
                           textColor=NAVY, spaceAfter=2, leading=20))
styles.add(ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=9.5,
                           textColor=GRAY, spaceAfter=10, leading=12))
styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], fontSize=11,
                           textColor=NAVY, spaceBefore=8, spaceAfter=4, leading=13))
styles.add(ParagraphStyle("BodySmall", parent=styles["Normal"], fontSize=8.7,
                           textColor=colors.HexColor("#2b2f36"), leading=11.5))
styles.add(ParagraphStyle("BulletSmall", parent=styles["Normal"], fontSize=8.5,
                           textColor=colors.HexColor("#2b2f36"), leading=11.2,
                           leftIndent=10, bulletIndent=0))
styles.add(ParagraphStyle("KpiNum", parent=styles["Normal"], fontSize=19,
                           textColor=NAVY, alignment=TA_CENTER, leading=21, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("KpiLabel", parent=styles["Normal"], fontSize=7.3,
                           textColor=GRAY, alignment=TA_CENTER, leading=9))
styles.add(ParagraphStyle("FooterStyle", parent=styles["Normal"], fontSize=7.3,
                           textColor=GRAY, alignment=TA_CENTER, leading=9))
styles.add(ParagraphStyle("BrandTitle", parent=styles["Normal"], fontSize=17,
                           textColor=NAVY, fontName="Helvetica-Bold", leading=19))
styles.add(ParagraphStyle("BrandTagline", parent=styles["Normal"], fontSize=9.5,
                           textColor=GRAY, fontName="Helvetica-Oblique", leading=11))

doc = SimpleDocTemplate(
    "../outputs/Provider_Network_Adequacy_One_Pager.pdf",
    pagesize=letter,
    topMargin=0.45 * inch, bottomMargin=0.4 * inch,
    leftMargin=0.5 * inch, rightMargin=0.5 * inch,
)

story = []

# ---------------------------------------------------------------------
# Brand header: logo + title + tagline, centered
# ---------------------------------------------------------------------
from reportlab.pdfbase.pdfmetrics import stringWidth
text_col_w = max(
    stringWidth(BRAND_TITLE, "Helvetica-Bold", 17),
    stringWidth(BRAND_TAGLINE, "Helvetica-Oblique", 9.5),
) + 14  # points, small buffer

logo_img = Image(LOGO_PATH, width=0.5 * inch, height=0.5 * inch * (267 / 237))
brand_text = [
    Paragraph(BRAND_TITLE, styles["BrandTitle"]),
    Paragraph(BRAND_TAGLINE, styles["BrandTagline"]),
]
brand_table = Table([[logo_img, brand_text]], colWidths=[0.55 * inch, text_col_w])
brand_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (0, 0), "CENTER"),
    ("LEFTPADDING", (1, 0), (1, 0), 8),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]))
# Center the brand block as a whole on the page.
brand_table.hAlign = "CENTER"
story.append(brand_table)
story.append(Spacer(1, 10))
story.append(HRFlowable(width="88%", thickness=0.8, hAlign="CENTER",
                         color=colors.HexColor("#d0d4da"), spaceAfter=10))

# ---------------------------------------------------------------------
# Project title
# ---------------------------------------------------------------------
story.append(Paragraph("Provider Network Adequacy Analysis", styles["H1Custom"]))
story.append(Paragraph(
    "Evaluating whether a payer's provider network meets access standards across specialty, "
    "distance, and wait-time thresholds &nbsp;|&nbsp; Sohail — Strategic HealthCare BI Analyst",
    styles["SubTitle"]))
story.append(HRFlowable(width="100%", thickness=1.1, color=NAVY, spaceAfter=8))

# ---------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------
kpis = [
    ("672", "Network Providers\nAcross 10 Specialties"),
    ("48,000", "Synthetic Members\nAnalyzed"),
    ("78.3%", "Fully Compliant\n(All 3 Standards)"),
    ("99.7%", "Distance\nCompliance"),
    ("78.6%", "Wait-Time\nCompliance"),
]
kpi_cells = []
for num, label in kpis:
    cell = [Paragraph(num, styles["KpiNum"]), Paragraph(label.replace("\n", "<br/>"), styles["KpiLabel"])]
    kpi_cells.append(cell)

kpi_table = Table([kpi_cells], colWidths=[1.42 * inch] * 5)
kpi_table.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("BOX", (0, 0), (0, 0), 0, colors.white),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("LINEAFTER", (0, 0), (-2, 0), 0.6, colors.white),
]))
story.append(kpi_table)
story.append(Spacer(1, 10))

# ---------------------------------------------------------------------
# Headline finding callout
# ---------------------------------------------------------------------
finding_style = ParagraphStyle("Finding", parent=styles["BodySmall"], fontSize=9.2,
                                textColor=colors.white, leading=12.5)
finding_table = Table([[Paragraph(
    "<b>Headline finding:</b> The network looks adequate on paper but isn't adequate in practice. "
    "It meets provider-to-member ratio standards almost universally (100%) and distance standards "
    "nearly everywhere (99.7%) — yet appointment wait-time compliance falls to 78.6%, driven by "
    "Neurology and Behavioral Health backlogs of 22&ndash;46 days. Headcount on the roster isn't the "
    "same as capacity a member can actually access.", finding_style)]],
    colWidths=[7.5 * inch])
finding_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
]))
story.append(finding_table)
story.append(Spacer(1, 9))

# ---------------------------------------------------------------------
# Two-column: charts left, findings/methodology right
# ---------------------------------------------------------------------
img1 = Image("../outputs/charts/02_specialty_geography_heatmap.png", width=3.55 * inch, height=2.17 * inch)
img2 = Image("../outputs/charts/01_compliance_by_geography.png", width=3.55 * inch, height=2.13 * inch)

left_col = [
    Paragraph("Compliance by Specialty x Geography", styles["SectionHead"]),
    img1,
    Spacer(1, 4),
    Paragraph("Overall Compliance by Geography", styles["SectionHead"]),
    img2,
]

right_col_flow = []
right_col_flow.append(Paragraph("Where the Network Breaks Down", styles["SectionHead"]))
bullets = [
    "<b>Neurology &amp; Behavioral Health</b> fail across nearly every county (19&ndash;43% compliant), driven by wait times of 22&ndash;46 days &mdash; not distance.",
    "<b>Suburban compliance (70.5%) is worse than rural (85.7%)</b> &mdash; a counterintuitive result. Dense suburban demand overwhelms a thin specialist panel more than sparse rural demand does.",
    "<b>OB/GYN access lags in rural counties</b> (Millbrook, Cedar Ridge) &mdash; a concern given the acuity of delayed prenatal care.",
    "Every specialty passes the <b>provider-to-member ratio</b> standard, confirming the gap is an appointment-availability problem, not a network-size problem.",
]
for b in bullets:
    right_col_flow.append(Paragraph(f"&bull;&nbsp; {b}", styles["BulletSmall"]))
    right_col_flow.append(Spacer(1, 3))

right_col_flow.append(Spacer(1, 4))
right_col_flow.append(Paragraph("Methodology", styles["SectionHead"]))
method_text = (
    "Synthetic network of 672 providers and 48,000 members across 8 counties (urban/suburban/rural). "
    "Haversine distance to nearest accepting in-network provider, simulated next-available-appointment "
    "wait time, and provider-to-member ratio were each compared to a benchmark table modeled on CMS "
    "Medicare Advantage Time &amp; Distance criteria and state Medicaid MCO wait-time standards."
)
right_col_flow.append(Paragraph(method_text, styles["BodySmall"]))

right_col_flow.append(Spacer(1, 6))
right_col_flow.append(Paragraph("Recommended Actions", styles["SectionHead"]))
actions = [
    "Prioritize Behavioral Health / Neurology telehealth expansion in the worst-performing counties &mdash; closes the wait-time gap without new physical sites.",
    "Pair ratio compliance with an appointment-availability audit before every regulatory filing.",
    "Model specialist demand at the county level; the suburban/rural pattern shows urban-suburban-rural buckets can mask real gaps.",
]
for a in actions:
    right_col_flow.append(Paragraph(f"&bull;&nbsp; {a}", styles["BulletSmall"]))
    right_col_flow.append(Spacer(1, 3))

two_col = Table([[left_col, right_col_flow]], colWidths=[3.75 * inch, 3.75 * inch])
two_col.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("LEFTPADDING", (1, 0), (1, 0), 12),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
]))
story.append(two_col)
story.append(Spacer(1, 8))

# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d0d4da"), spaceAfter=5))
story.append(Paragraph(
    "All provider, member, and location data is synthetically generated for portfolio demonstration. "
    "Standards are modeled loosely on public CMS/NCQA/Medicaid frameworks (simplified; not an authoritative regulatory reference).<br/>"
    "strategichealthcarebianalyst@gmail.com &nbsp;|&nbsp; linkedin.com/in/aimms-consulting-35895439 &nbsp;|&nbsp; "
    "sohail5993.github.io/Strategic-HealthCare-BI-Analyst/ &nbsp;|&nbsp; github.com/sohail5993",
    styles["FooterStyle"]))

doc.build(story)
print("PDF built: ../outputs/Provider_Network_Adequacy_One_Pager.pdf")
