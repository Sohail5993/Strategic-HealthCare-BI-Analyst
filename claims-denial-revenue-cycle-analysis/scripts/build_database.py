"""
build_database.py
------------------
Loads data/claims.csv into a SQLite database (data/claims.db) using a
lightweight star schema (fact_claims + dimension tables), so the SQL
scripts in /sql can be run and verified end-to-end with zero setup.

SQLite is used purely as a portable, zero-install engine for the
portfolio repo. The SQL in /sql is written in standard ANSI SQL and is
directly portable to PostgreSQL / SQL Server / Snowflake with minimal
(or no) changes -- see sql/README.md for dialect notes.
"""

import sqlite3
import pandas as pd

CSV_PATH = "/home/claude/healthcare-bi/data/claims.csv"
DB_PATH = "/home/claude/healthcare-bi/data/claims.db"

df = pd.read_csv(CSV_PATH, parse_dates=["date_of_service", "claim_submission_date"])

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------------------------------------------------------------
# Dimension tables
# ---------------------------------------------------------------------
dim_payer = (
    df[["payer_name", "payer_type"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
dim_payer.insert(0, "payer_id", range(1, len(dim_payer) + 1))

dim_service_line = (
    df[["service_line"]].drop_duplicates().reset_index(drop=True)
)
dim_service_line.insert(0, "service_line_id", range(1, len(dim_service_line) + 1))

dim_facility = df[["facility"]].drop_duplicates().reset_index(drop=True)
dim_facility.insert(0, "facility_id", range(1, len(dim_facility) + 1))

dim_denial_reason = (
    df[["denial_reason_code", "denial_reason_description", "denial_category"]]
    .dropna(subset=["denial_reason_code"])
    .drop_duplicates()
    .reset_index(drop=True)
)

# ---------------------------------------------------------------------
# Fact table (denormalized-friendly: keep natural keys + names for easy
# querying in a portfolio context, plus surrogate FKs for a "proper"
# star-schema demonstration)
# ---------------------------------------------------------------------
fact = df.merge(dim_payer, on=["payer_name", "payer_type"], how="left")
fact = fact.merge(dim_service_line, on="service_line", how="left")
fact = fact.merge(dim_facility, on="facility", how="left")

fact_cols = [
    "claim_id", "patient_id", "provider_id",
    "facility_id", "facility",
    "payer_id", "payer_name", "payer_type",
    "service_line_id", "service_line",
    "cpt_code", "icd10_code",
    "date_of_service", "claim_submission_date",
    "billed_amount", "paid_amount",
    "is_clean_claim", "first_pass_status",
    "denial_reason_code", "denial_reason_description", "denial_category",
    "is_resubmitted", "resubmission_count",
    "final_status", "turnaround_days",
]
fact_claims = fact[fact_cols].copy()
fact_claims["date_of_service"] = fact_claims["date_of_service"].dt.strftime("%Y-%m-%d")
fact_claims["claim_submission_date"] = fact_claims["claim_submission_date"].dt.strftime("%Y-%m-%d")
fact_claims["is_clean_claim"] = fact_claims["is_clean_claim"].astype(int)
fact_claims["is_resubmitted"] = fact_claims["is_resubmitted"].astype(int)

fact_claims.to_sql("fact_claims", conn, if_exists="replace", index=False)
dim_payer.to_sql("dim_payer", conn, if_exists="replace", index=False)
dim_service_line.to_sql("dim_service_line", conn, if_exists="replace", index=False)
dim_facility.to_sql("dim_facility", conn, if_exists="replace", index=False)
dim_denial_reason.to_sql("dim_denial_reason", conn, if_exists="replace", index=False)

cur.execute("CREATE INDEX idx_fact_payer ON fact_claims(payer_name)")
cur.execute("CREATE INDEX idx_fact_service_line ON fact_claims(service_line)")
cur.execute("CREATE INDEX idx_fact_submission_date ON fact_claims(claim_submission_date)")
cur.execute("CREATE INDEX idx_fact_status ON fact_claims(first_pass_status)")
conn.commit()

print("Tables created:", [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()])
print("fact_claims row count:", cur.execute("SELECT COUNT(*) FROM fact_claims").fetchone()[0])

conn.close()
print(f"\nDatabase written to {DB_PATH}")
