"""
Generates the multi-page static site from shared header/nav/footer + per-page
content. Output is plain .html files with no JS/build dependency at runtime —
this script is just an authoring convenience, not part of the shipped site.
"""
import os

OUT_DIR = "/home/claude/portfolio_site"

NAV_ITEMS = [
    ("index.html", "Home"),
    ("about.html", "About"),
    ("approach.html", "Approach"),
    ("certifications.html", "Certifications"),
    ("projects.html", "Projects"),
    ("case-studies.html", "Case Studies"),
    ("blog.html", "Blog"),
    ("contact.html", "Contact"),
]

def render_nav(active_page):
    links = []
    for href, label in NAV_ITEMS:
        cls = "nav-link active" if href == active_page else "nav-link"
        links.append(f'<a href="{href}" class="{cls}">{label}</a>')
    return "\n        ".join(links)

PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Strategic HealthCare BI Analyst</title>
<meta name="description" content="{description}">
<link rel="icon" type="image/png" href="assets/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

  <header class="site-header">
    <div class="wrap header-inner">
      <a href="index.html" class="brand-link">
        <img src="assets/logo.png" alt="Strategic HealthCare BI Analyst logo" class="brand-mark">
        <div class="brand-block">
          <span class="brand-name">Strategic HealthCare BI Analyst</span>
          <span class="brand-tagline">Transforming HealthCare Complexities into Growth Blueprints</span>
        </div>
      </a>
    </div>
    <nav class="site-nav">
      <div class="wrap nav-inner">
        {nav}
      </div>
    </nav>
  </header>

  <main>
"""

PAGE_FOOT = """
  </main>

  <footer class="site-footer wrap">
    <div class="footer-row">
      <span>Strategic HealthCare BI Analyst</span>
      <div class="footer-links">
        <a href="mailto:strategichealthcarebianalyst@gmail.com">Email</a>
        <a href="tel:+923004984892">Phone</a>
        <a href="https://www.linkedin.com/in/aimms-consulting-35895439">LinkedIn</a>
        <a href="https://github.com/sohail5993">GitHub</a>
      </div>
    </div>
  </footer>

</body>
</html>
"""

def write_page(filename, title, description, body_html):
    html = PAGE_HEAD.format(title=title, description=description, nav=render_nav(filename)) \
           + body_html + PAGE_FOOT
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w") as f:
        f.write(html)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
write_page(
    "index.html",
    "Home",
    "Healthcare data science portfolio — turning clinical, operational, and claims data into decisions hospitals can act on.",
    """
    <section class="hero wrap">
      <h1>I turn messy hospital data into decisions someone can act on Monday morning.</h1>
      <p class="lede">
        Every project here starts with a question a hospital actually pays to answer —
        readmissions, cost overruns, care-quality gaps — and works it through end to end:
        the data, the model, why it can be trusted, and what it's worth in dollars.
      </p>
    </section>

    <section class="pillars wrap">
      <div class="pillar">
        <div class="pillar-rule" style="background:#0F5C5C;"></div>
        <div class="pillar-body">
          <h3>Analytics &amp; Modeling</h3>
          <p>Predictive risk models built on real clinical and claims features, validated the way a hospital's own quality team would validate them.</p>
        </div>
      </div>
      <div class="pillar">
        <div class="pillar-rule" style="background:#C96F14;"></div>
        <div class="pillar-body">
          <h3>Strategic Translation</h3>
          <p>Every model ends in a dollar figure and an operational recommendation — not just an AUC score nobody outside the data team can use.</p>
        </div>
      </div>
      <div class="pillar">
        <div class="pillar-rule" style="background:#6C3483;"></div>
        <div class="pillar-body">
          <h3>Healthcare Domain Depth</h3>
          <p>Built around the real constraints hospitals operate under — HRRP penalties, care-management capacity, and what clinicians will actually trust.</p>
        </div>
      </div>
    </section>

    <section class="featured wrap">
      <h2>Featured work</h2>
      <article class="project">
        <div class="project-rule" style="background:#0F5C5C;"></div>
        <div class="project-body">
          <div class="project-head">
            <span class="tag" style="color:#0F5C5C; border-color:#0F5C5C;">Cost &amp; Quality</span>
            <h3>Hospital 30-Day Readmission Prediction</h3>
          </div>
          <p>Flagging the patients most likely to be readmitted within 30 days, so a limited-capacity care-management program targets the people who need it most.</p>
          <div class="stat-row">
            <div class="stat"><span class="stat-num">0.67</span><span class="stat-label">ROC-AUC</span></div>
            <div class="stat"><span class="stat-num">2x</span><span class="stat-label">precision lift, top 10% risk</span></div>
            <div class="stat"><span class="stat-num">$918K</span><span class="stat-label">est. annual net savings</span></div>
          </div>
          <div class="project-links">
            <a href="case-studies.html">Read the case study</a>
            <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction">View repository</a>
          </div>
        </div>
      </article>
      <p class="see-all"><a href="projects.html">See all projects →</a></p>
    </section>
    """
)

# ---------------------------------------------------------------------------
# ABOUT
# ---------------------------------------------------------------------------
write_page(
    "about.html",
    "About",
    "About Strategic HealthCare BI Analyst — background, focus, and how I work.",
    """
    <section class="page-header wrap">
      <h1>About</h1>
    </section>

    <section class="prose wrap">
      <p>
        I'm <strong>Sohail Bashir Butt</strong>, a Strategic HealthCare BI Analyst with
        <strong>10+ years of professional experience</strong> and a credentialed background
        spanning business intelligence platforms, data science, enterprise systems, and
        corporate strategy. My focus is healthcare: turning clinical, operational, and
        claims data into the kind of decisions a hospital finance or care-management leader
        can actually act on.
      </p>
      <p>
        That focus isn't just a specialization — it's backed by dedicated study across
        medical billing and coding, genomic data analysis, and pharmaceutical and medical
        device commercialization, layered on top of enterprise-grade credentials in BI
        platforms (Power BI, Tableau, Google Business Intelligence), data science (Google
        Data Analytics, Executive Data Science, Johns Hopkins' data science series), and
        systems delivery (SAP, Google Project Management, Google Cybersecurity). The
        combination is deliberate: healthcare analytics fails when it's only technical or
        only strategic — it has to be both.
      </p>
      <p>
        What I care about isn't the model — it's whether a hospital can act on it.
        A 0.90 AUC that nobody trusts is worth less than a 0.68 AUC that a care-management
        team actually uses. That's the standard every project on this site is held to.
      </p>

      <h2>How I work</h2>
      <ul class="prose-list">
        <li>Start from the business question, not the dataset — the model serves the decision, not the other way around.</li>
        <li>Report honest performance ceilings, not inflated metrics — healthcare stakeholders can tell the difference, and trust is the whole point.</li>
        <li>Every deliverable ends with a number a finance or operations leader can act on.</li>
      </ul>

      <h2>Background</h2>
      <p>
        Over 10+ years, I've built a deliberately cross-functional foundation —
        strategic management and decision science from Wharton and Copenhagen Business
        School, applied data science from Johns Hopkins, enterprise BI and cybersecurity
        from Google, SAP, and Microsoft, and healthcare-specific grounding in billing,
        genomics, and med-device commercialization. The full list, with verification links,
        is on the <a href="certifications.html">Certifications</a> page.
      </p>
    </section>
    """
)

# ---------------------------------------------------------------------------
# APPROACH
# ---------------------------------------------------------------------------
write_page(
    "approach.html",
    "Approach",
    "The analytical approach behind every project — from business question to measurable impact.",
    """
    <section class="page-header wrap">
      <h1>Approach</h1>
      <p class="lede">The same four-step process runs through every project on this site.</p>
    </section>

    <section class="steps wrap">
      <div class="step">
        <div class="step-rule" style="background:#0F5C5C;"></div>
        <div class="step-body">
          <span class="step-num">01</span>
          <h3>Define the business question</h3>
          <p>Before any data is touched: what decision is this for, who makes it, and what does it cost to get it wrong? A readmission model is worthless without knowing what a hospital would actually do with a risk score.</p>
        </div>
      </div>
      <div class="step">
        <div class="step-rule" style="background:#C96F14;"></div>
        <div class="step-body">
          <span class="step-num">02</span>
          <h3>Engineer clinically-grounded features</h3>
          <p>Features come from how clinicians and care managers actually think about risk — prior utilization, discharge disposition, comorbidity burden — not just whatever columns happen to be in the file.</p>
        </div>
      </div>
      <div class="step">
        <div class="step-rule" style="background:#1E8A8A;"></div>
        <div class="step-body">
          <span class="step-num">03</span>
          <h3>Model, validate, and explain honestly</h3>
          <p>Multiple models compared on metrics that match the real operating constraint (precision at a realistic capacity, not just AUC), with SHAP explanations so a care team can see why a patient was flagged.</p>
        </div>
      </div>
      <div class="step">
        <div class="step-rule" style="background:#6FA82F;"></div>
        <div class="step-body">
          <span class="step-num">04</span>
          <h3>Translate to a business case</h3>
          <p>Every project ends the same way: a dollar figure, an ROI estimate, and an honest account of what would need to happen operationally to realize it.</p>
        </div>
      </div>
    </section>
    """
)

# ---------------------------------------------------------------------------
# CERTIFICATIONS
# ---------------------------------------------------------------------------
CERTIFICATIONS = [
    {
        "category": "Healthcare & Life Sciences",
        "color": "#0F5C5C",
        "items": [
            {
                "name": "Medical Billing and Coding Fundamentals",
                "issuer": "Coursera — MedCerts",
                "year": "2024",
                "link": "https://coursera.org/verify/specialization/LRSZ1A3W8B1O",
                "blurb": "ICD-10, CPT, and HCPCS classification systems alongside revenue cycle management — standardizing clinical diagnoses and procedure data for claims analysis, reimbursement modeling, and fraud detection.",
            },
            {
                "name": "Introduction to Genomic Technologies",
                "issuer": "Coursera — Johns Hopkins University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/JK2DLNKD37YK",
                "blurb": "Computational molecular biology, high-throughput sequencing analysis, and genomic algorithms — enabling extraction and processing of genetic data to advance precision medicine and personalized care strategies.",
            },
            {
                "name": "Pharmaceutical and Medical Device Innovations",
                "issuer": "Coursera — University of Minnesota",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/F22U6KDZWSQV",
                "blurb": "The end-to-end commercialization lifecycle, FDA regulatory pathways, IP protection, and market access strategy — domain context for modeling drug performance and clinical technology adoption.",
            },
        ],
    },
    {
        "category": "Data, Analytics &amp; BI Platforms",
        "color": "#C96F14",
        "items": [
            {
                "name": "Google Data Analytics",
                "issuer": "Coursera — Google Career Certificate",
                "year": "2025",
                "link": "https://coursera.org/verify/professional-cert/Y5UV9UGQ26V9",
                "blurb": "The end-to-end analytical workflow from data cleaning and SQL querying to R programming and visualization — transforming complex electronic health records into clean, compliant, actionable insight.",
            },
            {
                "name": "Google Business Intelligence",
                "issuer": "Coursera — Google Career Certificate",
                "year": "2024",
                "link": "https://coursera.org/verify/professional-cert/B8F3U6D20QBW",
                "blurb": "Data modeling, ETL pipeline architecture, and dashboard development — unifying disparate hospital records and automating clinical KPI reporting for real-time decision-making.",
            },
            {
                "name": "Data Analytics For Lean Six Sigma",
                "issuer": "Coursera — University of Amsterdam",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/YYBCWL5HTJCM",
                "blurb": "Statistical hypothesis testing, regression analysis, and Minitab-driven process improvement under the Lean Six Sigma framework — root-causing inefficiencies in hospital workflows and clinical operations.",
            },
            {
                "name": "Microsoft Power BI Data Analyst",
                "issuer": "Coursera — Microsoft",
                "year": "2024",
                "link": "https://coursera.org/verify/professional-cert/8SAFXVFKMO5N",
                "blurb": "Advanced DAX metric engineering, semantic data modeling, and row-level security — secure executive dashboards tracking hospital operations and patient outcomes while safeguarding sensitive data.",
            },
            {
                "name": "Tableau BI Analyst",
                "issuer": "Coursera — Tableau",
                "year": "2024",
                "link": "https://coursera.org/verify/professional-cert/GN4PZ7VUSP3J",
                "blurb": "Advanced visual analytics, dynamic parameterization, and spatial plotting — turning epidemiological data and patient-flow patterns into intuitive visual stories for clinical leadership.",
            },
            {
                "name": "Executive Data Science Capstone",
                "issuer": "Coursera — Johns Hopkins University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/specialization/MALCTXT4K628",
                "blurb": "Leading end-to-end data science projects, pipeline governance, and executive storytelling — translating clinical models and statistical findings into strategic decisions for health system leaders.",
            },
            {
                "name": "A Crash Course in Data Science",
                "issuer": "Coursera — Johns Hopkins University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/2ERV3HM5RYFU",
                "blurb": "Core principles of machine learning, statistical inference, and data science workflows — a practical foundation for evaluating clinical data methodologies against strategic goals.",
            },
            {
                "name": "Managing Data Analysis",
                "issuer": "Coursera — Johns Hopkins University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/6HKZWGMXW8PE",
                "blurb": "Oversight of analytical workflows, statistical model iteration, and pipeline governance — quality-control frameworks that keep clinical analyses reproducible and compliant before they reach decision-makers.",
            },
            {
                "name": "Data Science in Real Life",
                "issuer": "Coursera — Johns Hopkins University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/YZACWBZLEEYL",
                "blurb": "Managing messy datasets, unexpected pipeline disruptions, and applied statistical modeling — cleaning incomplete electronic health records and producing reliable insight under real-world conditions.",
            },
        ],
    },
    {
        "category": "Strategy &amp; Business Analytics",
        "color": "#6C3483",
        "items": [
            {
                "name": "Strategic Management",
                "issuer": "Coursera — Copenhagen Business School",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/BZV246U5373G",
                "blurb": "A framework for formulating and executing strategy under market volatility and digital disruption — the same lens applied to navigating shifting healthcare policy and payer dynamics.",
            },
            {
                "name": "Strategy Formulation",
                "issuer": "Coursera — Copenhagen Business School",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/7GEGT99XPYR5",
                "blurb": "Tools for identifying growth vectors and designing corporate strategy from market analysis through execution — applied to positioning analytics initiatives around real organizational value.",
            },
            {
                "name": "Decision-Making &amp; Scenarios",
                "issuer": "Coursera — University of Pennsylvania",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/YXH42AHE58CN",
                "blurb": "Financial modeling, scenario planning, and capital-budgeting methods for stress-testing decisions under uncertainty — the discipline behind turning a readmission model into a defensible ROI case.",
            },
            {
                "name": "Operations Analytics",
                "issuer": "Coursera — Wharton, University of Pennsylvania",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/FBACTTKB6BGN",
                "blurb": "Capacity planning, supply chain optimization, and demand forecasting — streamlining hospital bed management, clinical staffing schedules, and pharmaceutical inventory.",
            },
            {
                "name": "People Analytics",
                "issuer": "Coursera — Wharton, University of Pennsylvania",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/PES32EM9CADV",
                "blurb": "Workforce planning, performance modeling, and retention analytics — optimizing nurse-to-patient staffing ratios and reducing clinical burnout and turnover.",
            },
            {
                "name": "Customer Analytics",
                "issuer": "Coursera — Wharton, University of Pennsylvania",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/99F5R86ZCE6W",
                "blurb": "Patient segmentation, behavioral modeling, and satisfaction tracking — personalizing patient engagement and optimizing telehealth adoption strategies.",
            },
            {
                "name": "Accounting Analytics",
                "issuer": "Coursera — Wharton, University of Pennsylvania",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/CHMQ4EGHHZKU",
                "blurb": "Financial statement modeling, cost accounting, and revenue cycle analysis — optimizing hospital billing workflows and tracking cost-per-patient metrics.",
            },
            {
                "name": "Business Metrics for Data-Driven Companies",
                "issuer": "Coursera — Duke University",
                "year": "2017",
                "link": "https://www.coursera.org/account/accomplishments/verify/KVB8BPFJN6D9",
                "blurb": "Key performance indicators, metric alignment, and data-driven decision frameworks — translating clinical and financial data into metrics that optimize hospital performance and patient satisfaction.",
            },
        ],
    },
    {
        "category": "Delivery, Governance &amp; Professional Development",
        "color": "#1E8A8A",
        "items": [
            {
                "name": "Google Project Management",
                "issuer": "Coursera — Google",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/professional-cert/6FME71P1HTZE",
                "blurb": "End-to-end project delivery across Waterfall and Agile methodologies — scope, stakeholder management, and quality control for shipping analytics work on time and on budget.",
            },
            {
                "name": "Google Agile Project Management",
                "issuer": "Coursera — Google",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/8VZCL5XBADVV",
                "blurb": "Scrum and Kanban frameworks, backlog management, and sprint retrospectives — running analytics work in short, stakeholder-responsive cycles rather than big-bang releases.",
            },
            {
                "name": "SAP Business Analyst",
                "issuer": "Coursera — SAP",
                "year": "2025",
                "link": "https://coursera.org/verify/professional-cert/VRQ38MNEYNB2",
                "blurb": "Enterprise business process modeling, requirements engineering, and SAP S/4HANA module integration — streamlining hospital supply chains and clinical procurement workflows.",
            },
            {
                "name": "SAP Technology Consultant",
                "issuer": "Coursera — SAP",
                "year": "2025",
                "link": "https://coursera.org/verify/professional-cert/8B6W3FME5IH6",
                "blurb": "Technical system architecture, SAP S/4HANA infrastructure implementation, and data integration protocols — securing cross-system pipelines and EHR interoperability while maintaining high availability for critical hospital IT operations.",
            },
            {
                "name": "Google Cybersecurity (incl. SQL &amp; Python)",
                "issuer": "Coursera — Google Career Certificate",
                "year": "2025",
                "link": "https://coursera.org/verify/professional-cert/LXXDXPKA66CQ",
                "blurb": "Threat modeling, network hardening, and incident response, plus hands-on Python and SQL — grounding for protecting sensitive patient data across healthcare data pipelines.",
            },
            {
                "name": "Strategic Career Self-Management",
                "issuer": "Coursera — The State University of New York",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/D4VNCVHCVZJX",
                "blurb": "Treating a career as a strategic portfolio — market positioning, gap analysis, and personal branding — the same analytical rigor turned inward.",
            },
            {
                "name": "What is Social?",
                "issuer": "Coursera — Northwestern University",
                "year": None,
                "link": "https://www.coursera.org/account/accomplishments/verify/4MNL3E3P2KQR",
                "blurb": "Social media strategy and audience analytics fundamentals — rounding out the toolkit for communicating healthcare analytics work to a wider professional audience.",
            },
        ],
    },
]

def render_certifications_body():
    parts = ['<section class="page-header wrap">',
             '<h1>Certifications</h1>',
             '<p class="lede">27 verified credentials spanning healthcare domain knowledge, '
             'data science, BI platforms, and strategic delivery — each links to its official '
             'verification page.</p>',
             '</section>']
    for group in CERTIFICATIONS:
        parts.append(f'<section class="cert-group wrap"><h2 class="cert-category">{group["category"]}</h2><div class="cert-list">')
        for item in group["items"]:
            meta = f'{item["issuer"]} · {item["year"]}' if item["year"] else item["issuer"]
            parts.append(f'''
      <div class="cert">
        <div class="cert-rule" style="background:{group["color"]};"></div>
        <div class="cert-body">
          <h3>{item["name"]}</h3>
          <p class="cert-meta">{meta}</p>
          <p>{item["blurb"]}</p>
          <div class="cert-links"><a href="{item["link"]}">Verify credential</a></div>
        </div>
      </div>''')
        parts.append('</div></section>')
    return "\n".join(parts)

write_page(
    "certifications.html",
    "Certifications",
    "27 verified professional certifications spanning healthcare, data science, BI platforms, and strategic delivery.",
    render_certifications_body()
)

# ---------------------------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------------------------
write_page(
    "projects.html",
    "Projects",
    "Healthcare data science and analytics projects.",
    """
    <section class="page-header wrap">
      <h1>Projects</h1>
    </section>

    <section class="projects wrap">
      <article class="project">
        <div class="project-rule" style="background:#0F5C5C;"></div>
        <div class="project-body">
          <div class="project-head">
            <span class="tag" style="color:#0F5C5C; border-color:#0F5C5C;">Cost &amp; Quality</span>
            <h3>Hospital 30-Day Readmission Prediction</h3>
          </div>
          <p>
            Predicts which patients are likely to be readmitted within 30 days of discharge,
            so a care-management team can target a limited-capacity intervention program at
            the patients who need it most — rather than spreading it thin across everyone.
          </p>
          <div class="stat-row">
            <div class="stat"><span class="stat-num">0.67</span><span class="stat-label">ROC-AUC, in line with published readmission models</span></div>
            <div class="stat"><span class="stat-num">2x</span><span class="stat-label">precision lift in the top 10% risk tier</span></div>
            <div class="stat"><span class="stat-num">$918K</span><span class="stat-label">est. annual net savings at a 20K-discharge hospital</span></div>
          </div>
          <div class="project-links">
            <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction">View repository</a>
            <a href="case-studies.html">Read the case study</a>
          </div>
        </div>
      </article>

      <article class="project">
        <div class="project-rule" style="background:#C96F14;"></div>
        <div class="project-body">
          <div class="project-head">
            <span class="tag" style="color:#C96F14; border-color:#C96F14;">Access &amp; Network</span>
            <h3>Provider Network Adequacy Analysis</h3>
          </div>
          <p>
            Evaluates whether a payer's provider network meets access standards across
            specialty, distance, and wait-time thresholds — and finds a network that looks
            adequate on paper but isn't adequate in practice.
          </p>
          <div class="stat-row">
            <div class="stat"><span class="stat-num">78.3%</span><span class="stat-label">members fully compliant, all 3 standards</span></div>
            <div class="stat"><span class="stat-num">99.7%</span><span class="stat-label">distance compliance</span></div>
            <div class="stat"><span class="stat-num">78.6%</span><span class="stat-label">wait-time compliance — the binding constraint</span></div>
          </div>
          <div class="project-links">
            <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst">View repository</a>
            <a href="case-studies.html#provider-network-adequacy">Read the case study</a>
          </div>
        </div>
      </article>

      <article class="project">
        <div class="project-rule" style="background:#6C3483;"></div>
        <div class="project-body">
          <div class="project-head">
            <span class="tag" style="color:#6C3483; border-color:#6C3483;">Chronic Disease</span>
            <h3>Care-Gap Prediction for Chronic Disease Management</h3>
          </div>
          <p>
            Identifies which chronic disease patients are likely to miss their next
            guideline-recommended screening or follow-up, so a limited-capacity outreach
            team knows who to call first — before a missed gap becomes a costly complication.
          </p>
          <div class="stat-row">
            <div class="stat"><span class="stat-num">0.716</span><span class="stat-label">ROC-AUC, in line with published care-gap models</span></div>
            <div class="stat"><span class="stat-num">2x</span><span class="stat-label">precision lift in the top 10% risk tier</span></div>
            <div class="stat"><span class="stat-num">$878K</span><span class="stat-label">est. annual net savings at a 50K-patient panel</span></div>
          </div>
          <div class="project-links">
            <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/chronic-disease-care-gap-prediction">View repository</a>
            <a href="case-studies.html#care-gap-prediction">Read the case study</a>
          </div>
        </div>
      </article>
    </section>
    """
)

# ---------------------------------------------------------------------------
# CASE STUDIES
# ---------------------------------------------------------------------------
write_page(
    "case-studies.html",
    "Case Studies",
    "In-depth case studies: the business problem, the approach, and the measurable outcome.",
    """
    <section class="page-header wrap">
      <h1>Case Studies</h1>
      <p class="lede">Case studies go deeper than the project list — walking through the business problem, the approach, and the measurable outcome.</p>
    </section>

    <section class="case-study wrap">
      <div class="cs-tag" style="color:#0F5C5C; border-color:#0F5C5C;">Cost &amp; Quality</div>
      <h2>Hospital 30-Day Readmission Prediction</h2>

      <h3>The problem</h3>
      <p>
        Under CMS's Hospital Readmissions Reduction Program, hospitals with excess 30-day
        readmissions face payment penalties of up to 3% of total Medicare inpatient
        reimbursement — on top of the roughly $15,000 each avoidable readmission costs
        outright. Care-management teams have enough capacity to actively manage a fraction
        of discharged patients, so the real question isn't "who might be readmitted" —
        it's "who should we call first."
      </p>

      <h3>The approach</h3>
      <p>
        Three models — logistic regression, random forest, and XGBoost — were trained on
        encounter-level clinical and demographic features, with class imbalance handled via
        weighting rather than resampling to keep predicted probabilities trustworthy for
        risk-stratification. Models were compared on precision at realistic staffing
        thresholds (top 10–20% of discharges), not just ROC-AUC, since that's what
        determines whether a limited-capacity program actually catches the right patients.
        SHAP explanations were layered on top so a care coordinator can see <em>why</em> a
        specific patient was flagged, not just their score.
      </p>

      <h3>The result</h3>
      <p>
        The best model reached 0.67 ROC-AUC — in line with published readmission models,
        including CMS's own — and delivered 2x the baseline precision in the top 10% risk
        tier. Simulating a transitional-care program targeted at just the top 5% highest-risk
        discharges produced the best return of any capacity tier tested: 1.84x ROI, an
        estimated $918K in annual net savings for a 20,000-discharge hospital.
      </p>

      <div class="cs-links">
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction">View repository</a>
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/blob/main/hospital-readmission-prediction/reports/readmission_one_pager.pdf">View one-pager</a>
      </div>
    </section>

    <section class="case-study wrap" id="provider-network-adequacy">
      <div class="cs-tag" style="color:#C96F14; border-color:#C96F14;">Access &amp; Network</div>
      <h2>Provider Network Adequacy Analysis</h2>

      <h3>The problem</h3>
      <p>
        Health plans are required — by CMS Medicare Advantage rules, state Medicaid
        contracts, and NCQA accreditation — to prove their provider networks give members
        reasonable access to care, typically measured across three dimensions: distance to
        the nearest provider, appointment wait time, and provider-to-member ratio. Failing
        any of these risks regulatory penalties and corrective action plans — but the
        deeper risk is members who technically have a network but can't actually get seen.
      </p>

      <h3>The approach</h3>
      <p>
        A synthetic regional network of 672 providers across 10 specialties and 48,000
        members across 8 counties (urban, suburban, and rural) was tested against a
        benchmark table modeled on CMS Medicare Advantage Time &amp; Distance criteria and
        state Medicaid MCO wait-time standards. For a stratified member sample, haversine
        distance to the nearest accepting in-network provider, next-available-appointment
        wait time, and provider-to-member ratio were each checked against their standard,
        then rolled up into a gap score ranking every county-by-specialty combination by
        severity.
      </p>

      <h3>The result</h3>
      <p>
        The network passes distance (99.7%) and provider-ratio (100%) standards almost
        everywhere — but appointment wait-time compliance falls to 78.6%, driven by
        Neurology and Behavioral Health backlogs of 22–46 days. Headcount on the roster
        isn't the same as capacity a member can actually access. A second, counterintuitive
        finding: suburban compliance (70.5%) is worse than rural (85.7%), because dense
        suburban demand overwhelms a thin specialist panel more than sparse rural demand
        does — a pattern that urban/suburban/rural bucketing alone would miss.
      </p>

      <div class="cs-links">
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst">View repository</a>
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/blob/main/outputs/Provider_Network_Adequacy_One_Pager.pdf">View one-pager</a>
      </div>
    </section>

    <section class="case-study wrap" id="care-gap-prediction">
      <div class="cs-tag" style="color:#6C3483; border-color:#6C3483;">Chronic Disease</div>
      <h2>Care-Gap Prediction for Chronic Disease Management</h2>

      <h3>The problem</h3>
      <p>
        Chronic disease management runs on guideline-recommended screenings and follow-ups —
        HbA1c tests, diabetic eye and foot exams, nephropathy screening, cardiology and
        pulmonary follow-ups. When a patient misses one, the miss is usually silent until it
        turns into a complication: retinopathy that could have been caught early, a CKD
        patient who progresses further before the next visit, a heart failure readmission
        after a missed weight check. A care-management team can only proactively call a
        fraction of an open care-gap registry each cycle, so the real question isn't who has
        an open gap — it's who will actually miss it if nobody calls first.
      </p>

      <h3>The approach</h3>
      <p>
        A synthetic population of 15,000 chronic disease patients (diabetes, hypertension,
        CHF, CKD, COPD) was built with realistic utilization, adherence, and access features —
        appointment no-show history, medication adherence, transportation barriers, telehealth
        enrollment, and reminder timing. Three models (logistic regression, random forest,
        XGBoost) were trained to predict whether a patient will miss their next guideline-due
        service, compared on precision at realistic outreach-capacity thresholds rather than
        ROC-AUC alone, with SHAP layered on top so a care coordinator can see why a specific
        patient was flagged.
      </p>

      <h3>The result</h3>
      <p>
        The best model reached 0.716 ROC-AUC and delivered 70% precision in the top 10% risk
        tier against a 34.6% base rate — a 2x lift. The top SHAP drivers &mdash; days since
        last visit, prior no-show history, reminder staleness, and medication adherence &mdash;
        are almost entirely operational levers, not clinical severity markers, meaning most of
        this gap is closeable through outreach timing rather than a different care plan.
        Targeting just the top 5% highest-risk patients produced the best return of any
        capacity tier tested: 6.40x ROI, an estimated $878K in annual net savings for a
        50,000-patient chronic disease panel.
      </p>

      <div class="cs-links">
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/chronic-disease-care-gap-prediction">View repository</a>
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/blob/main/chronic-disease-care-gap-prediction/reports/Care_Gap_Prediction_One_Pager.pdf">View one-pager</a>
      </div>
    </section>

    <section class="cs-placeholder wrap">
      <p class="coming-soon">More case studies coming soon.</p>
    </section>
    """
)

# ---------------------------------------------------------------------------
# BLOG
# ---------------------------------------------------------------------------
write_page(
    "blog.html",
    "Blog",
    "Notes on healthcare analytics, model explainability, and translating data into strategy.",
    """
    <section class="page-header wrap">
      <h1>Blog</h1>
      <p class="lede">Notes on healthcare analytics, model explainability, and translating data into strategy.</p>
    </section>

    <section class="case-study wrap">
      <div class="cs-tag" style="color:#2C5F8A; border-color:#2C5F8A;">Model Evaluation</div>
      <h2>Why ROC-AUC Is the Wrong Headline Metric for Readmission Models</h2>
      <p style="color:var(--muted); font-size:13.5px; margin-top:-16px; margin-bottom:24px;">September 2026 &middot; 6 min read</p>

      <p>
        Open almost any readmission-model writeup and the first number you'll see is ROC-AUC.
        0.68. 0.71. 0.65. It's treated like a report card grade — higher is better, and a
        model in the 0.70s must be doing something right. For a care-management team deciding
        whether to trust a model with real staffing decisions, that number is close to useless
        on its own, and sometimes actively misleading.
      </p>

      <h3>What ROC-AUC actually measures</h3>
      <p>
        ROC-AUC asks: if I pick one patient who was readmitted and one who wasn't, how often
        does the model rank the readmitted patient as higher risk? It's a measure of overall
        ranking quality across every possible threshold, from "flag almost everyone" to "flag
        almost no one." That breadth is exactly the problem. A care-management team doesn't
        operate across every threshold — they operate at one, maybe two, defined by how many
        nurses they can staff. A metric that averages performance across thresholds the team
        will never use is answering a question nobody asked.
      </p>

      <h3>The problem: base rates lie</h3>
      <p>
        Readmission datasets are imbalanced by nature — roughly 15&ndash;20% of discharges get
        readmitted within 30 days, so on a typical cohort like the one used in our own
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction">readmission project</a>,
        about 19.2% of patients are positive cases. ROC-AUC is fairly insensitive to this
        imbalance, which is exactly why it can look respectable while precision at any
        realistic staffing threshold stays weak. A model can rank the full population
        reasonably well overall and still hand a care coordinator a top-10% list that's wrong
        three times out of five.
      </p>

      <h3>A concrete illustration</h3>
      <p>
        Take two models trained on the same cohort, both reporting ROC-AUC around 0.67 &mdash;
        indistinguishable on the headline number:
      </p>
      <table style="width:100%; max-width:64ch; border-collapse:collapse; margin:20px 0 24px; font-size:14.5px;">
        <thead>
          <tr style="border-bottom:2px solid var(--ink);">
            <th style="text-align:left; padding:8px 12px 8px 0;">Model</th>
            <th style="text-align:left; padding:8px 12px;">ROC-AUC</th>
            <th style="text-align:left; padding:8px 12px;">Precision @ top 10%</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid var(--rule);">
            <td style="padding:8px 12px 8px 0;">A</td>
            <td style="padding:8px 12px;">0.670</td>
            <td style="padding:8px 12px;">38.7%</td>
          </tr>
          <tr style="border-bottom:1px solid var(--rule);">
            <td style="padding:8px 12px 8px 0;">B</td>
            <td style="padding:8px 12px;">0.668</td>
            <td style="padding:8px 12px;">24.1%</td>
          </tr>
        </tbody>
      </table>
      <p>
        Deploy Model A and a nurse calling the top 10% highest-risk discharges reaches a truly
        high-risk patient roughly 2 out of every 5 calls &mdash; a 2x lift over the 19.2% base
        rate. Deploy Model B off the strength of an "equivalent" ROC-AUC, and that same nurse
        is barely better than calling names at random. Nothing about the headline metric would
        have warned you.
      </p>

      <h3>What to report instead</h3>
      <p>
        None of this means ROC-AUC is useless &mdash; it's a fine sanity check for overall
        discrimination and worth reporting alongside better metrics, just not as the number
        that decides whether a model ships. Three additions matter more for an operational
        readmission model:
      </p>
      <ul class="prose-list">
        <li><strong>PR-AUC</strong> &mdash; unlike ROC-AUC, precision-recall AUC is sensitive
            to class imbalance, so it doesn't flatter a model just because negatives are
            easy to rule out.</li>
        <li><strong>Precision @ K</strong> &mdash; precision at the top 5&ndash;20% of
            discharges, matched to the care-management team's actual enrollment capacity.
            This is the number that answers "if I call this list, how often am I right?"</li>
        <li><strong>Calibration</strong> &mdash; if the predicted probabilities themselves
            will inform triage tiers or be shown to clinicians, they need to mean what they
            say. A model with class weighting instead of synthetic resampling tends to keep
            probabilities more trustworthy for this reason.</li>
      </ul>

      <h3>The honest ceiling</h3>
      <p>
        It's worth saying plainly: published readmission models &mdash; including CMS's own
        &mdash; typically top out around 0.65&ndash;0.70 ROC-AUC, and no amount of metric
        selection changes that ceiling. A large share of readmission risk lives outside the
        EHR entirely &mdash; housing stability, caregiver support, medication adherence &mdash;
        not in a modeling gap waiting to be closed with a better algorithm. Choosing the right
        metric doesn't make a mediocre model look artificially strong; it makes sure a
        genuinely useful model doesn't get judged by a number that can't tell it apart from a
        mediocre one.
      </p>

      <h3>The takeaway</h3>
      <p>
        Next time someone hands you a readmission model with a single ROC-AUC number, ask
        the follow-up question: what's precision at the tier you can actually staff? If they
        don't have that number ready, the model hasn't been evaluated against the decision
        it's meant to support &mdash; it's been evaluated against a benchmark that flatters
        the median use case nobody is actually deploying.
      </p>

      <div class="cs-links">
        <a href="case-studies.html#readmission">Read the full case study</a>
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/blob/main/hospital-readmission-prediction/reports/readmission_one_pager.pdf">View the one-pager</a>
      </div>
    </section>

    <section class="case-study wrap">
      <div class="cs-tag" style="color:#2C5F8A; border-color:#2C5F8A;">Model Evaluation</div>
      <h2>Reading a SHAP Plot as a Non-Technical Stakeholder</h2>
      <p style="color:var(--muted); font-size:13.5px; margin-top:-16px; margin-bottom:24px;">September 2026 &middot; 7 min read</p>

      <p>
        A data scientist hands you a chart full of colored dots, a vertical line at zero, and
        axis labels like <code>cat__had_inpatient_days_False</code>, and says "this is why the
        model flagged these patients." It's meant to build trust, but if you don't already
        know how to read it, it does the opposite. SHAP plots are actually one of the more
        stakeholder-friendly things a model can produce &mdash; you just need the same three
        minutes of orientation the analyst had.
      </p>

      <h3>What problem SHAP is solving</h3>
      <p>
        Most models that predict readmission risk are, at heart, unreadable &mdash; a forest
        of hundreds of decision trees, or a wall of coefficients you can't intuit. SHAP
        (SHapley Additive exPlanations) doesn't try to make the model itself simpler. Instead,
        for every prediction, it answers one specific question: <em>starting from the average
        patient, which factors pushed this person's risk score up, which pushed it down, and
        by how much?</em> That's it. Every SHAP plot you'll see is just a different way of
        displaying those pushes.
      </p>

      <h3>Start with the bar chart &mdash; it's the easy one</h3>
      <img src="https://raw.githubusercontent.com/sohail5993/Strategic-HealthCare-BI-Analyst/main/hospital-readmission-prediction/reports/figures/04_shap_bar.png"
           alt="SHAP mean absolute feature importance bar chart for the readmission model"
           style="width:100%; max-width:560px; display:block; margin:20px auto;">
      <p style="text-align:center; color:var(--muted); font-size:13px; margin-top:-8px;">
        Mean |SHAP| feature importance &mdash; from the readmission project's evaluation report.
      </p>
      <p>
        This one has no hidden layers. Longer bar means that feature moves the prediction
        further, on average, across all patients &mdash; nothing more. It won't tell you
        which direction a feature pushes, only how much it matters overall. Here, whether a
        patient had recent inpatient stays and where they were discharged to dominate
        everything else, which is a reasonable place for a readmission model's attention to
        concentrate.
      </p>

      <h3>Then the beeswarm plot &mdash; more information, same idea</h3>
      <img src="https://raw.githubusercontent.com/sohail5993/Strategic-HealthCare-BI-Analyst/main/hospital-readmission-prediction/reports/figures/03_shap_beeswarm.png"
           alt="SHAP summary beeswarm plot showing global feature impact on 30-day readmission"
           style="width:100%; max-width:640px; display:block; margin:20px auto;">
      <p style="text-align:center; color:var(--muted); font-size:13px; margin-top:-8px;">
        SHAP summary plot &mdash; one dot per patient, per feature.
      </p>
      <p>
        This looks busier, but it's the same bar chart with two things added. Every row is
        still a feature, ranked the same way as before. But now every dot is one actual
        patient, and two new things are encoded:
      </p>
      <ul class="prose-list">
        <li><strong>Horizontal position</strong> &mdash; how far that patient's risk score
            was pushed left (lower risk) or right (higher risk) by this specific feature.</li>
        <li><strong>Color</strong> &mdash; whether that patient had a high (red) or low (blue)
            value for the feature itself, not for the risk score.</li>
      </ul>
      <p>
        Read the top row with that in mind: patients where "no recent inpatient days" is true
        (red) cluster on the left &mdash; that fact lowers their risk. Patients where it's
        false (blue, meaning they <em>did</em> have recent inpatient stays) cluster on the
        right &mdash; it raises their risk. Same logic on the second row: being discharged
        home (red) pushes risk down; being discharged somewhere else &mdash; a skilled
        nursing facility, rehab &mdash; pushes it up. Once you see the color-and-side pattern
        once, every other row reads the same way.
      </p>

      <h3>What individual-patient explanations add</h3>
      <p>
        The two plots above describe the model's behavior across the whole population &mdash;
        useful for auditing the model itself, but not the question a care coordinator actually
        has: <em>why did this one patient get flagged?</em> For that, the same SHAP values get
        shown per-patient, usually as a waterfall running from the population's average risk
        to that patient's specific score, with each bar labeled by the feature that moved it.
        The math is identical to the summary plot; it's just filtered down to a single dot
        from every row. If a coordinator asks "why is Mrs. Alvarez on this list," that
        per-patient waterfall is the artifact that answers it in plain terms &mdash; not
        the model's overall behavior, but hers specifically.
      </p>

      <h3>Four questions worth asking when someone shows you one of these</h3>
      <ul class="prose-list">
        <li><strong>"Does the direction match clinical intuition?"</strong> If a feature pushes
            risk the opposite way a clinician would expect, that's worth investigating before
            trusting anything else in the plot.</li>
        <li><strong>"Is this the population view or one patient?"</strong> A summary plot tells
            you the model is reasonable in aggregate; it says nothing about whether any
            specific flagged patient makes sense.</li>
        <li><strong>"What's driving the top 2&ndash;3 features, operationally?"</strong> If the
            top driver is something a care team can't act on, the explanation is honest but
            not useful for intervention design.</li>
        <li><strong>"Would a different model show a similar picture?"</strong> If the top
            drivers are clinically obvious things like recent inpatient utilization and
            discharge disposition, that's a good sign &mdash; it means the model isn't
            leaning on something spurious to hit its numbers.</li>
      </ul>

      <p>
        None of this requires knowing how Shapley values are computed. The plot is doing the
        math; your job is just reading which way the dots lean.
      </p>

      <div class="cs-links">
        <a href="case-studies.html#readmission">Read the full case study</a>
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction/reports/figures">View the full figure set</a>
      </div>
    </section>

    <section class="case-study wrap">
      <div class="cs-tag" style="color:#0F5C5C; border-color:#0F5C5C;">Policy &amp; Incentives</div>
      <h2>What CMS's HRRP Penalty Formula Actually Rewards</h2>
      <p style="color:var(--muted); font-size:13.5px; margin-top:-16px; margin-bottom:24px;">September 2026 &middot; 8 min read</p>

      <p>
        "Reduce readmissions" is the goal everyone states out loud. It's not, strictly, the
        thing Medicare's Hospital Readmissions Reduction Program actually pays hospitals to
        do. The formula rewards something narrower and more specific &mdash; and the gap
        between the two has shaped a decade of hospital behavior, some of it exactly what
        regulators intended, some of it not.
      </p>

      <h3>The mechanics, briefly</h3>
      <p>
        HRRP tracks 30-day unplanned readmissions for six conditions and procedures: acute
        myocardial infarction, heart failure, pneumonia, COPD, coronary artery bypass graft
        surgery, and elective hip or knee replacement. For each condition where a hospital had
        at least 25 eligible cases, CMS calculates an excess readmission ratio &mdash; predicted
        readmissions for that hospital's actual patient mix, divided by what a statistically
        average hospital would be expected to produce for the same mix. A ratio above 1.0 means
        worse than expected; below 1.0 means better. Since fiscal year 2019, hospitals are
        compared only against peers with a similar share of dual-eligible (Medicare and
        Medicaid) patients, a fix added after years of evidence that safety-net hospitals were
        being penalized for their patients' circumstances more than their own care quality.
        The resulting penalty, capped at 3%, doesn't just hit the six tracked conditions &mdash;
        it's deducted from the hospital's <em>entire</em> base Medicare inpatient payment for
        the full fiscal year.
      </p>

      <h3>What it rewards: relative standing, not absolute improvement</h3>
      <p>
        The ERR is a ratio against a peer benchmark, not a fixed bar. A hospital that cuts its
        readmission rate by 15% can still get penalized if similar hospitals cut theirs by 25%.
        A hospital that makes no changes at all can see its penalty shrink if its peer group's
        performance worsens. The formula rewards outperforming statistically similar hospitals
        in a given period &mdash; not any particular level of absolute quality, and not
        improvement relative to your own past. It's also asymmetric: a hospital with far
        fewer readmissions than expected gets no bonus payment, only the absence of a penalty.
        There's no credit side to this ledger, only a debit side with a floor at zero.
      </p>

      <h3>What counts as a readmission &mdash; and what quietly doesn't</h3>
      <p>
        This is the part worth sitting with. HRRP counts an unplanned return to <em>any</em>
        acute care hospital within 30 days as a readmission &mdash; even if the return is for a
        completely unrelated condition. But it only counts <em>inpatient</em> readmissions.
        A patient who returns and is placed under observation status, or is treated and
        released from the emergency department, doesn't register as a readmission at all,
        regardless of how clinically similar that encounter was to a full inpatient stay.
      </p>
      <p>
        That distinction turned out to matter enormously. Peer-reviewed research tracking
        claims data found that when observation stays were counted alongside inpatient
        readmissions &mdash; on the reasoning that the two are often clinically
        indistinguishable &mdash; more than half of the readmission-rate improvement widely
        credited to HRRP disappeared, and for inpatient-only readmissions the national
        downward trend essentially vanished once observation stays were properly accounted for.
        A separate hospitalist-authored analysis estimated that roughly one in five genuine
        rehospitalizations goes uncounted by HRRP for exactly this reason. None of this
        requires assuming bad faith &mdash; a hospital under pressure to avoid a penalty has a
        completely legal, completely rational reason to lean on observation status for a
        borderline case, and the formula can't tell the difference between that and a
        genuinely borderline clinical judgment.
      </p>

      <h3>Why this matters for a model built to reduce readmissions</h3>
      <p>
        If you're building a predictive model &mdash; like the one behind our own
        <a href="https://github.com/sohail5993/Strategic-HealthCare-BI-Analyst/tree/main/hospital-readmission-prediction">readmission project</a>
        &mdash; the target label has to match CMS's definition exactly, or the model's risk
        scores won't map onto the dollars actually at stake. A model trained on "any return
        visit within 30 days" will flag a different population than one trained on "unplanned
        inpatient readmission within 30 days, excluding observation stays" &mdash; and only
        the second one predicts what shows up in the hospital's HRRP penalty calculation.
        Get the label definition slightly wrong, and a genuinely accurate model ends up
        optimizing for a number the finance team doesn't actually care about.
      </p>

      <h3>The honest critique</h3>
      <p>
        The observation-status shift isn't the only documented side effect. Multiple
        independent studies found increased 30-day mortality following heart failure
        hospitalizations after HRRP took effect, concentrated specifically among patients who
        were <em>not</em> readmitted &mdash; consistent with, though not proof of, sicker
        patients being managed in the ED or under observation rather than admitted, when
        admission might have served them better. CMS's 2019 shift to peer-grouping by
        dual-eligible share addressed one real flaw &mdash; safety-net hospitals were absorbing
        penalties driven by their patients' housing, transportation, and medication-access
        circumstances rather than care quality &mdash; but it didn't touch the
        observation-status blind spot, which by design would need Congress to change the
        underlying statute, not just a CMS rule update.
      </p>

      <h3>The takeaway</h3>
      <p>
        None of this means the formula is badly designed for its stated purpose &mdash; it's
        precisely designed, and precisely narrow. It rewards a hospital for keeping its
        <em>measured, inpatient-coded, 30-day, condition-specific</em> readmission rate below
        its risk-adjusted peer benchmark. Whether that measured number and genuine patient
        outcomes move together is an empirical question, not a guarantee built into the
        formula &mdash; and a decade of claims data suggests the two have drifted apart more
        than the program's early success statistics implied.
      </p>

      <div class="cs-links">
        <a href="case-studies.html#readmission">Read the full case study</a>
        <a href="https://www.cms.gov/medicare/quality/value-based-programs/hospital-readmissions">CMS HRRP program page</a>
      </div>
    </section>

    <section class="prose wrap">
      <h2>More topics in progress</h2>
      <p class="coming-soon">Next post coming soon.</p>
    </section>
    """
)

# ---------------------------------------------------------------------------
# CONTACT
# ---------------------------------------------------------------------------
write_page(
    "contact.html",
    "Contact",
    "Get in touch — email, LinkedIn, or GitHub.",
    """
    <section class="page-header wrap">
      <h1>Contact</h1>
      <p class="lede">Have a healthcare data problem worth solving? Let's talk.</p>
    </section>

    <section class="contact-list wrap">
      <a class="contact-item" href="mailto:strategichealthcarebianalyst@gmail.com">
        <span class="contact-label">Email</span>
        <span class="contact-value">strategichealthcarebianalyst@gmail.com</span>
      </a>
      <a class="contact-item" href="tel:+923004984892">
        <span class="contact-label">Phone</span>
        <span class="contact-value">+92-300-498-4892</span>
      </a>
      <a class="contact-item" href="https://www.linkedin.com/in/aimms-consulting-35895439">
        <span class="contact-label">LinkedIn</span>
        <span class="contact-value">linkedin.com/in/aimms-consulting-35895439</span>
      </a>
      <a class="contact-item" href="https://github.com/sohail5993">
        <span class="contact-label">GitHub</span>
        <span class="contact-value">github.com/sohail5993</span>
      </a>
    </section>
    """
)

print("\nAll pages generated.")
