# Business Questions

This project is designed to answer the following practical retail questions. Each question has a primary SQL home, although related queries may appear elsewhere.

| # | Business question | Primary data | SQL file |
|---:|---|---|---|
| 1 | Which stores generate the most revenue and profit? | Sales, Stores | `04_store_analysis.sql` |
| 2 | Which product categories are most profitable? | Sales, Products | `03_product_analysis.sql` |
| 3 | Which products have high sales but below-company margins? | Sales, Products | `03_product_analysis.sql` |
| 4 | Which products are slow-moving? | Inventory, Products | `06_inventory_analysis.sql` |
| 5 | Which stores experience stockouts most often? | Inventory, Stores | `06_inventory_analysis.sql` |
| 6 | What is the unit return rate by category? | Returns, Sales, Products | `07_returns_analysis.sql` |
| 7 | How is revenue changing month over month? | Sales | `02_sales_analysis.sql` |
| 8 | What is average order value? | Sales | `04_store_analysis.sql` |
| 9 | Which customers are repeat customers? | Sales, Customers | `05_customer_analysis.sql` |
| 10 | Which products contribute most to revenue? | Sales, Products | `03_product_analysis.sql` |
| 11 | Which calendar months have the strongest sales? | Sales | `02_sales_analysis.sql` |
| 12 | Are higher discounts associated with lower profit margins? | Sales | `02_sales_analysis.sql` |
| 13 | Which products are currently below their reorder level? | Inventory, Products, Stores | `06_inventory_analysis.sql` |
| 14 | What are the most common reasons for returns? | Returns | `07_returns_analysis.sql` |
| 15 | Which products make up the first 80% of revenue? | Sales, Products | `08_advanced_analysis.sql` |

## Important interpretation notes

- Revenue is net of line-item discounts but does not subtract returned revenue.
- Profit is gross product profit; operating costs are not available.
- “Repeat customer” means at least two distinct orders during the available period.
- Stockout rate is based on monthly closing-stock observations.
- Discount analysis is descriptive. It does not prove that discounts caused margin changes.

