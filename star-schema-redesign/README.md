# Star Schema Redesign

**Two flat, denormalized datasets rebuilt as governed star schemas — with every modeling
decision documented, not just the result.**

## The business problem

Flat, denormalized datasets are easy to hand over but hard to build reliable BI on top of — every
report re-derives its own logic, grain is implicit rather than stated, and slowly-changing
attributes (a customer's region, a patient's assigned provider) get overwritten instead of tracked.
Two working datasets — a retail order extract and a healthcare patient-encounters extract — needed
to be rebuilt into a form a BI tool and an analyst could both trust.

## Approach

Both datasets were redesigned as governed star schemas: an explicit grain statement for each fact
table, conformed dimensions shared across the model rather than duplicated per report, and Slowly
Changing Dimension Type 2 applied only where history genuinely mattered — not as a blanket
default. A bridge table was introduced specifically to resolve a many-to-many relationship that a
simple foreign key couldn't represent cleanly. Every modeling decision — why a dimension was
conformed, why SCD2 was or wasn't used, why the bridge table was necessary — was documented
alongside the schema rather than left implicit.

## Result

Two complete worked examples — retail and healthcare — each with a documented, query-ready star
schema: explicit grain, conformed dimensions, SCD2 applied selectively where history mattered, and
one bridge table resolving the many-to-many case. The healthcare model in particular gives the rest
of this portfolio's patient-level projects a schema pattern to build on, rather than starting from
a flat extract each time.

## Dashboard

[`dashboard.html`](./dashboard.html) — the live dashboard for this project.

## A note on what's in this repo

The schemas and documentation described above (grain statements, conformed dimensions, SCD2 logic,
the bridge table) aren't currently uploaded to this repo — only this write-up and the dashboard
are. Flagging this honestly rather than implying there's a reproducible schema/DDL here to inspect;
if the underlying files get uploaded later, this note should be replaced with a real
repo-structure section like the LOS Prediction and Care-Gap Prediction projects have.
