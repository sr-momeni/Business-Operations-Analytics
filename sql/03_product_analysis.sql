-- 03_product_analysis.sql
-- Product/category performance, return rates, rankings, and contribution.

-- Top 10 products by revenue.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(SUM(s.net_revenue), 2) AS revenue,
    SUM(s.quantity) AS units_sold
FROM sales AS s
INNER JOIN products AS p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- Top 10 products by gross profit.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(SUM(s.profit), 2) AS profit,
    ROUND(100.0 * SUM(s.profit) / NULLIF(SUM(s.net_revenue), 0), 2) AS profit_margin_pct
FROM sales AS s
INNER JOIN products AS p ON s.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY profit DESC
LIMIT 10;

-- Bottom-performing / slow-selling catalog products.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COALESCE(SUM(s.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(s.net_revenue), 0), 2) AS revenue,
    ROUND(COALESCE(SUM(s.profit), 0), 2) AS profit
FROM products AS p
LEFT JOIN sales AS s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold ASC, revenue ASC
LIMIT 20;

-- High-revenue products with below-company margin.
WITH product_metrics AS (
    SELECT
        product_id,
        SUM(net_revenue) AS revenue,
        SUM(profit) AS profit
    FROM sales
    GROUP BY product_id
),
benchmarks AS (
    SELECT
        AVG(revenue) AS average_product_revenue,
        SUM(profit) / NULLIF(SUM(revenue), 0) AS company_margin
    FROM product_metrics
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    ROUND(pm.revenue, 2) AS revenue,
    ROUND(100.0 * pm.profit / NULLIF(pm.revenue, 0), 2) AS profit_margin_pct
FROM product_metrics AS pm
INNER JOIN products AS p ON pm.product_id = p.product_id
CROSS JOIN benchmarks AS b
WHERE pm.revenue >= b.average_product_revenue
  AND pm.profit / NULLIF(pm.revenue, 0) < b.company_margin
ORDER BY pm.revenue DESC;

-- Category performance. Sales and returns are aggregated separately to avoid join inflation.
WITH category_sales AS (
    SELECT
        p.category,
        SUM(s.net_revenue) AS revenue,
        SUM(s.profit) AS profit,
        SUM(s.quantity) AS units_sold
    FROM sales AS s
    INNER JOIN products AS p ON s.product_id = p.product_id
    GROUP BY p.category
),
category_returns AS (
    SELECT
        p.category,
        SUM(r.quantity_returned) AS units_returned
    FROM returns AS r
    INNER JOIN products AS p ON r.product_id = p.product_id
    GROUP BY p.category
)
SELECT
    cs.category,
    ROUND(cs.revenue, 2) AS revenue,
    ROUND(cs.profit, 2) AS profit,
    ROUND(100.0 * cs.profit / NULLIF(cs.revenue, 0), 2) AS profit_margin_pct,
    cs.units_sold,
    COALESCE(cr.units_returned, 0) AS units_returned,
    ROUND(100.0 * COALESCE(cr.units_returned, 0) / NULLIF(cs.units_sold, 0), 2) AS return_rate_pct
FROM category_sales AS cs
LEFT JOIN category_returns AS cr ON cs.category = cr.category
ORDER BY revenue DESC;

-- Product revenue contribution, rank, and cumulative share.
WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(s.net_revenue) AS revenue
    FROM products AS p
    INNER JOIN sales AS s ON p.product_id = s.product_id
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT
    product_id,
    product_name,
    category,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(revenue) OVER (), 2) AS cumulative_revenue_share_pct
FROM product_revenue
ORDER BY revenue DESC;

