-- 02_sales_analysis.sql
-- Revenue trends, order behavior, discount bands, LAG, and running totals.

-- Monthly revenue, profit, orders, and units sold.
SELECT
    strftime('%Y-%m', order_date) AS month,
    ROUND(SUM(net_revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    COUNT(DISTINCT order_id) AS orders,
    SUM(quantity) AS units_sold
FROM sales
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month;

-- Month-over-month revenue growth using LAG.
WITH monthly_sales AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY strftime('%Y-%m', order_date)
),
with_previous AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue
    FROM monthly_sales
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(100.0 * (revenue - previous_month_revenue) / NULLIF(previous_month_revenue, 0), 2) AS growth_pct
FROM with_previous
ORDER BY month;

-- Strongest calendar months across all available years.
SELECT
    CAST(strftime('%m', order_date) AS INTEGER) AS month_number,
    CASE strftime('%m', order_date)
        WHEN '01' THEN 'January' WHEN '02' THEN 'February' WHEN '03' THEN 'March'
        WHEN '04' THEN 'April' WHEN '05' THEN 'May' WHEN '06' THEN 'June'
        WHEN '07' THEN 'July' WHEN '08' THEN 'August' WHEN '09' THEN 'September'
        WHEN '10' THEN 'October' WHEN '11' THEN 'November' WHEN '12' THEN 'December'
    END AS month_name,
    ROUND(SUM(net_revenue), 2) AS revenue,
    COUNT(DISTINCT order_id) AS orders
FROM sales
GROUP BY month_number, month_name
ORDER BY revenue DESC;

-- Discount bands help assess association with margin; this is not a causal test.
SELECT
    CASE
        WHEN discount_pct = 0 THEN 'No discount'
        WHEN discount_pct <= 0.10 THEN '1-10%'
        WHEN discount_pct <= 0.20 THEN '11-20%'
        ELSE 'Over 20%'
    END AS discount_band,
    COUNT(*) AS sales_lines,
    ROUND(AVG(discount_pct) * 100, 2) AS average_discount_pct,
    ROUND(SUM(net_revenue), 2) AS revenue,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 2) AS profit_margin_pct
FROM sales
GROUP BY discount_band
ORDER BY average_discount_pct;

-- Monthly revenue with a running total (SUM OVER).
WITH monthly_sales AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        SUM(net_revenue) AS revenue
    FROM sales
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(SUM(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue
FROM monthly_sales
ORDER BY month;

-- Order-level basket size and order value distribution.
WITH order_totals AS (
    SELECT
        order_id,
        order_date,
        SUM(quantity) AS units_in_order,
        COUNT(*) AS product_lines,
        SUM(net_revenue) AS order_value
    FROM sales
    GROUP BY order_id, order_date
)
SELECT
    product_lines,
    COUNT(*) AS orders,
    ROUND(AVG(units_in_order), 2) AS average_units,
    ROUND(AVG(order_value), 2) AS average_order_value
FROM order_totals
GROUP BY product_lines
ORDER BY product_lines;

