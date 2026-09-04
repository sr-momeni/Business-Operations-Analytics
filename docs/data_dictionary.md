# Data Dictionary

The cleaned model contains six relational tables. Dates use ISO `YYYY-MM-DD` text in CSV/SQLite and should be imported as Date in Power BI or Excel. Currency values are CAD.

## Grain and keys

| Table | Grain | Primary key | Important foreign keys |
|---|---|---|---|
| `customers` | One row per customer | `customer_id` | None |
| `products` | One row per product | `product_id` | None |
| `stores` | One row per store | `store_id` | None |
| `sales` | One product line within an order | (`order_id`, `product_id`) | `customer_id`, `store_id`, `product_id` |
| `inventory` | One monthly store-product observation | (`date`, `store_id`, `product_id`) | `store_id`, `product_id` |
| `returns` | One return event for an order-product line | `return_id` | (`order_id`, `product_id`) |

## customers

| Column | Type | Description | Example |
|---|---|---|---|
| `customer_id` | TEXT | Unique customer identifier. `CUST_UNKNOWN` preserves sales with missing/invalid raw customer IDs. | `CUST0042` |
| `customer_name` | TEXT | Synthetic customer display name. | `Maya Singh` |
| `city` | TEXT | Canadian city. | `Toronto` |
| `province` | TEXT | Standardized full province name. | `Ontario` |
| `signup_date` | DATE | Date the customer joined. | `2022-09-14` |
| `customer_segment` | TEXT | Source segment: New, Regular, or Loyal. | `Regular` |

## products

| Column | Type | Description | Example |
|---|---|---|---|
| `product_id` | TEXT | Unique product identifier. | `PROD042` |
| `product_name` | TEXT | Synthetic product name. | `Audio Item 07` |
| `category` | TEXT | Top-level product group. | `Electronics` |
| `subcategory` | TEXT | Product group below category. | `Audio` |
| `unit_cost` | REAL | Company cost for one unit in CAD. | `42.50` |
| `unit_price` | REAL | Standard selling price for one unit in CAD. | `69.99` |
| `supplier` | TEXT | Synthetic supplier name. Missing raw suppliers become `Unknown Supplier`. | `Supplier C` |

## stores

| Column | Type | Description | Example |
|---|---|---|---|
| `store_id` | TEXT | Unique store identifier. | `STORE03` |
| `store_name` | TEXT | Store display name. | `Montreal Centre` |
| `city` | TEXT | Store city. | `Montreal` |
| `province` | TEXT | Standardized full province name. | `Quebec` |
| `store_type` | TEXT | Urban or Suburban. | `Urban` |
| `opening_date` | DATE | Date the store opened. | `2015-11-12` |

## sales

One order may contain multiple products. The generator ensures a product appears at most once per order, making (`order_id`, `product_id`) the line-level key.

| Column | Type | Description | Example |
|---|---|---|---|
| `order_id` | TEXT | Identifier shared by all lines in one order. | `ORD000123` |
| `order_date` | DATE | Date of purchase. | `2024-06-18` |
| `customer_id` | TEXT | Customer key; references `customers`. | `CUST0042` |
| `store_id` | TEXT | Store key; references `stores`. | `STORE03` |
| `product_id` | TEXT | Product key; references `products`. | `PROD042` |
| `quantity` | INTEGER | Units sold on the line; greater than zero. | `2` |
| `unit_price` | REAL | Transaction unit price before discount, CAD. | `69.99` |
| `discount_pct` | REAL | Discount as a decimal from 0 to 1. | `0.10` |
| `unit_cost` | REAL | Product cost copied at cleaning time, CAD. | `42.50` |
| `gross_revenue` | REAL | `quantity * unit_price`, CAD. | `139.98` |
| `net_revenue` | REAL | `gross_revenue * (1 - discount_pct)`, CAD. | `125.98` |
| `cost` | REAL | `quantity * unit_cost`, CAD. | `85.00` |
| `profit` | REAL | `net_revenue - cost`, CAD. | `40.98` |

## inventory

Inventory is a monthly snapshot/flow table. `units_sold` covers the month ending on `date`.

| Column | Type | Description | Example |
|---|---|---|---|
| `date` | DATE | Month-end observation date. | `2024-06-30` |
| `store_id` | TEXT | Store key; references `stores`. | `STORE03` |
| `product_id` | TEXT | Product key; references `products`. | `PROD042` |
| `opening_stock` | INTEGER | Units available at the start of the period. | `12` |
| `units_received` | INTEGER | Units added during the period. | `8` |
| `units_sold` | INTEGER | Units sold during the period. | `6` |
| `closing_stock` | INTEGER | `opening_stock + units_received - units_sold`. | `14` |
| `reorder_level` | INTEGER | Closing-stock threshold used to flag replenishment need. | `10` |

## returns

| Column | Type | Description | Example |
|---|---|---|---|
| `return_id` | TEXT | Unique return record identifier. | `RET000123` |
| `order_id` | TEXT | Original order identifier. | `ORD000123` |
| `product_id` | TEXT | Returned product. Together with `order_id`, references a sales line. | `PROD042` |
| `return_date` | DATE | Date of return; never before the order date in cleaned data. | `2024-06-25` |
| `quantity_returned` | INTEGER | Units returned; positive and no greater than units sold. | `1` |
| `return_reason` | TEXT | Reported reason or `Unknown`. | `Defective` |

## Controlled values

- Product categories: Electronics, Grocery, Home, Personal Care, Clothing, Office.
- Customer segments: New, Regular, Loyal.
- Store types: Urban, Suburban.
- Return reasons: Defective, Wrong Item, Customer Changed Mind, Damaged, Size Issue, Unknown.

