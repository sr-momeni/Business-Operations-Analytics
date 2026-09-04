-- 05_customer_analysis.sql
-- Customer value, repeat behavior, frequency, and spend-based segmentation.

-- Company-level customer summary.
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS orders,
        SUM(net_revenue) AS spend
    FROM sales
    WHERE customer_id <> 'CUST_UNKNOWN'
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS unique_customers,
    ROUND(AVG(spend), 2) AS average_spend_per_customer,
    ROUND(AVG(orders), 2) AS average_orders_per_customer,
    ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS repeat_customer_rate_pct
FROM customer_orders;

-- Customer purchase frequency and value.
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(DISTINCT s.order_id) AS purchase_frequency,
    ROUND(SUM(s.net_revenue), 2) AS total_spend,
    ROUND(SUM(s.net_revenue) / NULLIF(COUNT(DISTINCT s.order_id), 0), 2) AS average_order_value,
    MIN(s.order_date) AS first_order_date,
    MAX(s.order_date) AS latest_order_date
FROM customers AS c
INNER JOIN sales AS s ON c.customer_id = s.customer_id
WHERE c.customer_id <> 'CUST_UNKNOWN'
GROUP BY c.customer_id, c.customer_name, c.customer_segment
ORDER BY total_spend DESC;

-- Top 20 customers by spend.
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.province,
    COUNT(DISTINCT s.order_id) AS orders,
    ROUND(SUM(s.net_revenue), 2) AS total_spend,
    ROUND(SUM(s.profit), 2) AS gross_profit
FROM sales AS s
INNER JOIN customers AS c ON s.customer_id = c.customer_id
WHERE c.customer_id <> 'CUST_UNKNOWN'
GROUP BY c.customer_id, c.customer_name, c.city, c.province
ORDER BY total_spend DESC
LIMIT 20;

-- Data-driven spend segments using CASE WHEN.
WITH customer_value AS (
    SELECT
        c.customer_id,
        c.customer_name,
        COUNT(DISTINCT s.order_id) AS orders,
        SUM(s.net_revenue) AS total_spend
    FROM customers AS c
    INNER JOIN sales AS s ON c.customer_id = s.customer_id
    WHERE c.customer_id <> 'CUST_UNKNOWN'
    GROUP BY c.customer_id, c.customer_name
),
thresholds AS (
    SELECT AVG(total_spend) AS average_spend FROM customer_value
)
SELECT
    cv.customer_id,
    cv.customer_name,
    cv.orders,
    ROUND(cv.total_spend, 2) AS total_spend,
    CASE
        WHEN cv.total_spend >= t.average_spend * 2 THEN 'High Value'
        WHEN cv.total_spend >= t.average_spend THEN 'Core'
        ELSE 'Occasional'
    END AS value_segment
FROM customer_value AS cv
CROSS JOIN thresholds AS t
ORDER BY cv.total_spend DESC;

-- New versus repeat orders, based on each customer's order sequence.
WITH order_customers AS (
    SELECT customer_id, order_id, MIN(order_date) AS order_date
    FROM sales
    WHERE customer_id <> 'CUST_UNKNOWN'
    GROUP BY customer_id, order_id
),
sequenced AS (
    SELECT
        customer_id,
        order_id,
        order_date,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS order_number
    FROM order_customers
)
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(CASE WHEN order_number = 1 THEN 1 ELSE 0 END) AS new_customer_orders,
    SUM(CASE WHEN order_number > 1 THEN 1 ELSE 0 END) AS repeat_customer_orders,
    ROUND(100.0 * SUM(CASE WHEN order_number > 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS repeat_order_share_pct
FROM sequenced
GROUP BY month
ORDER BY month;

