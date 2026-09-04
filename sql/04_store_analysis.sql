-- 04_store_analysis.sql
-- Store performance, ranking, regional comparison, and monthly trend.

-- Complete store performance scorecard ranked by revenue.
WITH store_metrics AS (
    SELECT
        st.store_id,
        st.store_name,
        st.city,
        st.province,
        st.store_type,
        SUM(s.net_revenue) AS revenue,
        SUM(s.profit) AS profit,
        COUNT(DISTINCT s.order_id) AS orders,
        SUM(s.quantity) AS units_sold
    FROM stores AS st
    INNER JOIN sales AS s ON st.store_id = s.store_id
    GROUP BY st.store_id, st.store_name, st.city, st.province, st.store_type
)
SELECT
    store_id,
    store_name,
    city,
    province,
    store_type,
    ROUND(revenue, 2) AS revenue,
    ROUND(profit, 2) AS profit,
    ROUND(100.0 * profit / NULLIF(revenue, 0), 2) AS profit_margin_pct,
    orders,
    ROUND(revenue / NULLIF(orders, 0), 2) AS average_order_value,
    units_sold,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM store_metrics
ORDER BY revenue_rank, store_id;

-- Province-level performance.
SELECT
    st.province,
    COUNT(DISTINCT st.store_id) AS stores,
    ROUND(SUM(s.net_revenue), 2) AS revenue,
    ROUND(SUM(s.profit), 2) AS profit,
    COUNT(DISTINCT s.order_id) AS orders
FROM sales AS s
INNER JOIN stores AS st ON s.store_id = st.store_id
GROUP BY st.province
ORDER BY revenue DESC;

-- Store revenue rank within each month.
WITH monthly_store AS (
    SELECT
        strftime('%Y-%m', s.order_date) AS month,
        st.store_id,
        st.store_name,
        SUM(s.net_revenue) AS revenue
    FROM sales AS s
    INNER JOIN stores AS st ON s.store_id = st.store_id
    GROUP BY month, st.store_id, st.store_name
)
SELECT
    month,
    store_id,
    store_name,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (PARTITION BY month ORDER BY revenue DESC) AS monthly_revenue_rank
FROM monthly_store
ORDER BY month, monthly_revenue_rank;

-- Stores with margins below the company margin.
WITH company AS (
    SELECT SUM(profit) / NULLIF(SUM(net_revenue), 0) AS margin FROM sales
),
store_margin AS (
    SELECT
        store_id,
        SUM(profit) / NULLIF(SUM(net_revenue), 0) AS margin,
        SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY store_id
)
SELECT
    st.store_name,
    ROUND(sm.revenue, 2) AS revenue,
    ROUND(100.0 * sm.margin, 2) AS store_margin_pct,
    ROUND(100.0 * c.margin, 2) AS company_margin_pct
FROM store_margin AS sm
INNER JOIN stores AS st ON sm.store_id = st.store_id
CROSS JOIN company AS c
WHERE sm.margin < c.margin
ORDER BY sm.margin;

