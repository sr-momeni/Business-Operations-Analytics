-- 08_advanced_analysis.sql
-- CTEs, ROW_NUMBER, RANK, LAG, cumulative shares, and year-over-year analysis.

-- Top three products by revenue within each category.
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_id,
        p.product_name,
        SUM(s.net_revenue) AS revenue
    FROM sales AS s
    INNER JOIN products AS p ON s.product_id = p.product_id
    GROUP BY p.category, p.product_id, p.product_name
),
ranked AS (
    SELECT
        category,
        product_id,
        product_name,
        revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC, product_id) AS category_position
    FROM product_revenue
)
SELECT
    category,
    category_position,
    product_id,
    product_name,
    ROUND(revenue, 2) AS revenue
FROM ranked
WHERE category_position <= 3
ORDER BY category, category_position;

-- Monthly store revenue and rank, plus change from the previous month.
WITH monthly_store AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        store_id,
        SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY month, store_id
),
with_change AS (
    SELECT
        month,
        store_id,
        revenue,
        LAG(revenue) OVER (PARTITION BY store_id ORDER BY month) AS previous_month_revenue,
        RANK() OVER (PARTITION BY month ORDER BY revenue DESC) AS store_rank
    FROM monthly_store
)
SELECT
    wc.month,
    st.store_name,
    ROUND(wc.revenue, 2) AS revenue,
    ROUND(wc.previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(100.0 * (wc.revenue - wc.previous_month_revenue) / NULLIF(wc.previous_month_revenue, 0), 2) AS growth_pct,
    wc.store_rank
FROM with_change AS wc
INNER JOIN stores AS st ON wc.store_id = st.store_id
ORDER BY wc.month, wc.store_rank;

-- ABC classification based on cumulative product revenue share.
WITH product_revenue AS (
    SELECT product_id, SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY product_id
),
contribution AS (
    SELECT
        product_id,
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            / SUM(revenue) OVER () AS cumulative_share
    FROM product_revenue
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(c.revenue, 2) AS revenue,
    ROUND(100.0 * c.cumulative_share, 2) AS cumulative_revenue_share_pct,
    CASE
        WHEN c.cumulative_share <= 0.80 THEN 'A'
        WHEN c.cumulative_share <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM contribution AS c
INNER JOIN products AS p ON c.product_id = p.product_id
ORDER BY c.revenue DESC;

-- Year-over-year monthly revenue where a comparable prior-year month exists.
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY month
),
with_prior_year AS (
    SELECT
        month,
        revenue,
        LAG(revenue, 12) OVER (ORDER BY month) AS prior_year_revenue
    FROM monthly
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(prior_year_revenue, 2) AS prior_year_revenue,
    ROUND(100.0 * (revenue - prior_year_revenue) / NULLIF(prior_year_revenue, 0), 2) AS year_over_year_growth_pct
FROM with_prior_year
WHERE prior_year_revenue IS NOT NULL
ORDER BY month;

-- Customer recency/frequency/value snapshot using the last order date as the as-of date.
WITH as_of AS (
    SELECT MAX(order_date) AS max_order_date FROM sales
),
customer_metrics AS (
    SELECT
        customer_id,
        CAST(julianday((SELECT max_order_date FROM as_of)) - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(net_revenue) AS monetary_value
    FROM sales
    WHERE customer_id <> 'CUST_UNKNOWN'
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.customer_name,
    cm.recency_days,
    cm.frequency,
    ROUND(cm.monetary_value, 2) AS monetary_value,
    CASE
        WHEN cm.recency_days <= 60 AND cm.frequency >= 10 THEN 'Champions'
        WHEN cm.recency_days <= 120 AND cm.frequency >= 5 THEN 'Active'
        WHEN cm.recency_days > 180 THEN 'At Risk'
        ELSE 'Developing'
    END AS behavioral_segment
FROM customer_metrics AS cm
INNER JOIN customers AS c ON cm.customer_id = c.customer_id
ORDER BY cm.monetary_value DESC;

