-- 07_returns_analysis.sql
-- Return rates, products, categories, reasons, and stores.

-- Overall unit return rate.
WITH sold AS (
    SELECT SUM(quantity) AS units_sold FROM sales
),
returned AS (
    SELECT SUM(quantity_returned) AS units_returned FROM returns
)
SELECT
    sold.units_sold,
    returned.units_returned,
    ROUND(100.0 * returned.units_returned / NULLIF(sold.units_sold, 0), 2) AS return_rate_pct
FROM sold CROSS JOIN returned;

-- Products with the most returned units and their unit return rates.
WITH product_sales AS (
    SELECT product_id, SUM(quantity) AS units_sold
    FROM sales
    GROUP BY product_id
),
product_returns AS (
    SELECT product_id, SUM(quantity_returned) AS units_returned
    FROM returns
    GROUP BY product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ps.units_sold,
    COALESCE(pr.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(pr.units_returned, 0) / NULLIF(ps.units_sold, 0), 2) AS return_rate_pct
FROM products AS p
INNER JOIN product_sales AS ps ON p.product_id = ps.product_id
LEFT JOIN product_returns AS pr ON p.product_id = pr.product_id
ORDER BY units_returned DESC, return_rate_pct DESC
LIMIT 25;

-- Returns by category, with separately aggregated denominators.
WITH category_sales AS (
    SELECT p.category, SUM(s.quantity) AS units_sold
    FROM sales AS s
    INNER JOIN products AS p ON s.product_id = p.product_id
    GROUP BY p.category
),
category_returns AS (
    SELECT p.category, SUM(r.quantity_returned) AS units_returned
    FROM returns AS r
    INNER JOIN products AS p ON r.product_id = p.product_id
    GROUP BY p.category
)
SELECT
    cs.category,
    cs.units_sold,
    COALESCE(cr.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(cr.units_returned, 0) / NULLIF(cs.units_sold, 0), 2) AS return_rate_pct
FROM category_sales AS cs
LEFT JOIN category_returns AS cr ON cs.category = cr.category
ORDER BY return_rate_pct DESC;

-- Most common return reasons.
SELECT
    return_reason,
    COUNT(*) AS return_records,
    SUM(quantity_returned) AS units_returned,
    ROUND(100.0 * SUM(quantity_returned) / SUM(SUM(quantity_returned)) OVER (), 2) AS share_of_returned_units_pct
FROM returns
GROUP BY return_reason
ORDER BY units_returned DESC;

-- Store return rate. Return rows are linked to sales before aggregation.
WITH store_sales AS (
    SELECT store_id, SUM(quantity) AS units_sold
    FROM sales
    GROUP BY store_id
),
store_returns AS (
    SELECT s.store_id, SUM(r.quantity_returned) AS units_returned
    FROM returns AS r
    INNER JOIN sales AS s
        ON r.order_id = s.order_id
       AND r.product_id = s.product_id
    GROUP BY s.store_id
)
SELECT
    st.store_name,
    ss.units_sold,
    COALESCE(sr.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(sr.units_returned, 0) / NULLIF(ss.units_sold, 0), 2) AS return_rate_pct
FROM stores AS st
INNER JOIN store_sales AS ss ON st.store_id = ss.store_id
LEFT JOIN store_returns AS sr ON st.store_id = sr.store_id
ORDER BY return_rate_pct DESC;

