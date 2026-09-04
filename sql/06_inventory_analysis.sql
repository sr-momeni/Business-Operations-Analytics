-- 06_inventory_analysis.sql
-- Stockouts, reorder risk, demand, slow movers, and inventory turnover.

-- Stockout rate by store (closing_stock = 0).
SELECT
    st.store_id,
    st.store_name,
    COUNT(*) AS inventory_observations,
    SUM(CASE WHEN i.closing_stock = 0 THEN 1 ELSE 0 END) AS stockout_observations,
    ROUND(100.0 * SUM(CASE WHEN i.closing_stock = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS stockout_rate_pct
FROM inventory AS i
INNER JOIN stores AS st ON i.store_id = st.store_id
GROUP BY st.store_id, st.store_name
ORDER BY stockout_rate_pct DESC;

-- Average closing stock by category.
SELECT
    p.category,
    ROUND(AVG(i.closing_stock), 2) AS average_closing_units,
    ROUND(AVG(i.reorder_level), 2) AS average_reorder_level,
    SUM(i.units_sold) AS recorded_units_sold
FROM inventory AS i
INNER JOIN products AS p ON i.product_id = p.product_id
GROUP BY p.category
ORDER BY average_closing_units DESC;

-- Slow-moving products based on recorded inventory-period units sold.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(i.units_sold) AS units_sold,
    ROUND(AVG(i.closing_stock), 2) AS average_closing_stock,
    SUM(CASE WHEN i.units_sold = 0 THEN 1 ELSE 0 END) AS zero_sales_periods
FROM inventory AS i
INNER JOIN products AS p ON i.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_sold ASC, average_closing_stock DESC
LIMIT 20;

-- High-demand products.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(i.units_sold) AS units_sold,
    RANK() OVER (ORDER BY SUM(i.units_sold) DESC) AS demand_rank
FROM inventory AS i
INNER JOIN products AS p ON i.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY demand_rank
LIMIT 20;

-- Products below reorder level in the latest inventory snapshot.
WITH latest_date AS (
    SELECT MAX(date) AS inventory_date FROM inventory
)
SELECT
    i.date,
    st.store_name,
    p.product_id,
    p.product_name,
    p.category,
    i.closing_stock,
    i.reorder_level,
    i.reorder_level - i.closing_stock AS units_below_reorder
FROM inventory AS i
INNER JOIN latest_date AS ld ON i.date = ld.inventory_date
INNER JOIN stores AS st ON i.store_id = st.store_id
INNER JOIN products AS p ON i.product_id = p.product_id
WHERE i.closing_stock < i.reorder_level
ORDER BY units_below_reorder DESC, st.store_name, p.product_id;

-- Inventory turnover by category: COGS divided by average monthly inventory value.
WITH category_cogs AS (
    SELECT p.category, SUM(s.cost) AS cogs
    FROM sales AS s
    INNER JOIN products AS p ON s.product_id = p.product_id
    GROUP BY p.category
),
monthly_inventory_value AS (
    SELECT
        i.date,
        p.category,
        SUM(i.closing_stock * p.unit_cost) AS inventory_value
    FROM inventory AS i
    INNER JOIN products AS p ON i.product_id = p.product_id
    GROUP BY i.date, p.category
),
average_inventory AS (
    SELECT category, AVG(inventory_value) AS average_inventory_value
    FROM monthly_inventory_value
    GROUP BY category
)
SELECT
    c.category,
    ROUND(c.cogs, 2) AS cost_of_goods_sold,
    ROUND(a.average_inventory_value, 2) AS average_inventory_value,
    ROUND(c.cogs / NULLIF(a.average_inventory_value, 0), 2) AS inventory_turnover
FROM category_cogs AS c
INNER JOIN average_inventory AS a ON c.category = a.category
ORDER BY inventory_turnover DESC;

