-- 01_basic_analysis.sql
-- Introductory SELECT, WHERE, ORDER BY, GROUP BY, HAVING, and JOIN examples.

-- Row count for each table.
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'stores', COUNT(*) FROM stores
UNION ALL
SELECT 'sales', COUNT(*) FROM sales
UNION ALL
SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL
SELECT 'returns', COUNT(*) FROM returns
ORDER BY table_name;

-- Discounted sales lines over $200, newest first.
SELECT
    order_id,
    order_date,
    product_id,
    net_revenue,
    discount_pct
FROM sales
WHERE discount_pct > 0
  AND net_revenue >= 200
ORDER BY order_date DESC, net_revenue DESC
LIMIT 25;

-- Category-level catalog summary.
SELECT
    category,
    COUNT(*) AS product_count,
    ROUND(AVG(unit_price), 2) AS average_list_price,
    ROUND(AVG(unit_price - unit_cost), 2) AS average_unit_margin
FROM products
GROUP BY category
ORDER BY average_list_price DESC;

-- Suppliers with at least 10 products.
SELECT
    supplier,
    COUNT(*) AS product_count,
    ROUND(AVG(unit_price), 2) AS average_price
FROM products
GROUP BY supplier
HAVING COUNT(*) >= 10
ORDER BY product_count DESC, supplier;

-- LEFT JOIN keeps products even if they have no sales.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COALESCE(SUM(s.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(s.net_revenue), 0), 2) AS revenue
FROM products AS p
LEFT JOIN sales AS s
    ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue ASC, p.product_id
LIMIT 20;

