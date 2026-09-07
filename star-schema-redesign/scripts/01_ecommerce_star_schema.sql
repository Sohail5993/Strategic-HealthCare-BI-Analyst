-- =============================================================================
-- Star Schema Redesign — Example 1: E-Commerce Order Data
-- Grain: one row per product line, per order.
-- Target: PostgreSQL (portable to any standard SQL engine with minor tweaks)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- DIM_DATE — conformed dimension, reusable across future fact tables
-- ---------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key        INT PRIMARY KEY,        -- surrogate key, e.g. 20240103
    full_date       DATE NOT NULL,
    day_of_week     VARCHAR(10) NOT NULL,
    day_of_month    SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    month_name      VARCHAR(10) NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    is_holiday      BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
-- DIM_CUSTOMER — SCD Type 2 on segment/city: history matters for
-- point-in-time revenue-by-segment reporting.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key    SERIAL PRIMARY KEY,     -- surrogate key
    customer_id     VARCHAR(20) NOT NULL,   -- natural/business key from source system
    customer_name   VARCHAR(120) NOT NULL,
    segment         VARCHAR(30) NOT NULL,
    city            VARCHAR(80),
    effective_date  DATE NOT NULL,
    expiry_date     DATE,                   -- NULL while row is current
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_dim_customer_natural_key ON dim_customer (customer_id, is_current);

-- ---------------------------------------------------------------------------
-- DIM_PRODUCT — SCD Type 1: cosmetic corrections overwrite in place.
-- A genuine category reclassification would be handled as Type 2 in a
-- mature warehouse; kept Type 1 here as a deliberate, documented simplification.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key     SERIAL PRIMARY KEY,
    product_id      VARCHAR(20) NOT NULL UNIQUE,
    product_name    VARCHAR(150) NOT NULL,
    category        VARCHAR(60) NOT NULL,
    subcategory     VARCHAR(60),
    standard_cost   NUMERIC(10,2)
);

-- ---------------------------------------------------------------------------
-- DIM_EMPLOYEE — SCD Type 1
-- ---------------------------------------------------------------------------
CREATE TABLE dim_employee (
    employee_key    SERIAL PRIMARY KEY,
    employee_id     VARCHAR(20) NOT NULL UNIQUE,
    employee_name   VARCHAR(120) NOT NULL,
    region          VARCHAR(60)
);

-- ---------------------------------------------------------------------------
-- FACT_SALES — grain: one row per product line, per order.
-- OrderID kept as a degenerate dimension (no attributes of its own).
-- ---------------------------------------------------------------------------
CREATE TABLE fact_sales (
    date_key        INT NOT NULL REFERENCES dim_date (date_key),
    customer_key    INT NOT NULL REFERENCES dim_customer (customer_key),
    product_key     INT NOT NULL REFERENCES dim_product (product_key),
    employee_key    INT NOT NULL REFERENCES dim_employee (employee_key),
    order_id        VARCHAR(20) NOT NULL,   -- degenerate dimension

    -- Fully additive measures (safe to SUM across any dimension combination)
    quantity        INT NOT NULL,
    extended_amount NUMERIC(12,2) NOT NULL,
    cogs            NUMERIC(12,2) NOT NULL,
    profit          NUMERIC(12,2) NOT NULL,

    -- Non-additive measures — kept for audit/line-level detail only.
    -- Never SUM these; average or display at the line-item grain.
    unit_price      NUMERIC(10,2) NOT NULL,
    discount        NUMERIC(5,4) NOT NULL DEFAULT 0
);

CREATE INDEX idx_fact_sales_date ON fact_sales (date_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales (customer_key);
CREATE INDEX idx_fact_sales_product ON fact_sales (product_key);
CREATE INDEX idx_fact_sales_order ON fact_sales (order_id);

-- ---------------------------------------------------------------------------
-- Sample data — mirrors the flat extract shown in the README
-- ---------------------------------------------------------------------------
INSERT INTO dim_date (date_key, full_date, day_of_week, day_of_month, month, month_name, quarter, year, is_weekend)
VALUES (20240103, '2024-01-03', 'Wednesday', 3, 1, 'January', 1, 2024, FALSE);

INSERT INTO dim_customer (customer_id, customer_name, segment, city, effective_date, is_current)
VALUES
    ('C204', 'J. Farooq', 'Corporate', 'Lahore', '2024-01-01', TRUE),
    ('C097', 'A. Bhatti', 'Consumer', 'Karachi', '2024-01-01', TRUE);

INSERT INTO dim_product (product_id, product_name, category, subcategory, standard_cost)
VALUES
    ('P0091', 'Wireless Mouse', 'Electronics', 'Accessories', 6.40),
    ('P0113', 'USB-C Hub', 'Electronics', 'Accessories', 11.10);

INSERT INTO dim_employee (employee_id, employee_name, region)
VALUES
    ('E12', 'S. Malik', 'Punjab'),
    ('E08', 'R. Iqbal', 'Sindh');

INSERT INTO fact_sales (date_key, customer_key, product_key, employee_key, order_id, quantity, extended_amount, cogs, profit, unit_price, discount)
VALUES
    (20240103, (SELECT customer_key FROM dim_customer WHERE customer_id = 'C204'),
     (SELECT product_key FROM dim_product WHERE product_id = 'P0091'),
     (SELECT employee_key FROM dim_employee WHERE employee_id = 'E12'),
     '10001', 3, 37.02, 19.20, 17.82, 12.99, 0.05),
    (20240103, (SELECT customer_key FROM dim_customer WHERE customer_id = 'C204'),
     (SELECT product_key FROM dim_product WHERE product_id = 'P0113'),
     (SELECT employee_key FROM dim_employee WHERE employee_id = 'E12'),
     '10001', 1, 24.99, 11.10, 13.89, 24.99, 0.00),
    (20240103, (SELECT customer_key FROM dim_customer WHERE customer_id = 'C097'),
     (SELECT product_key FROM dim_product WHERE product_id = 'P0091'),
     (SELECT employee_key FROM dim_employee WHERE employee_id = 'E08'),
     '10002', 2, 25.98, 12.80, 13.18, 12.99, 0.00);

-- ---------------------------------------------------------------------------
-- Example query: revenue and profit by product category, safe because
-- the grain is fixed and the measures are correctly additive.
-- ---------------------------------------------------------------------------
-- SELECT
--     p.category,
--     SUM(f.extended_amount) AS total_revenue,
--     SUM(f.profit)          AS total_profit
-- FROM fact_sales f
-- JOIN dim_product p ON f.product_key = p.product_key
-- GROUP BY p.category
-- ORDER BY total_revenue DESC;
