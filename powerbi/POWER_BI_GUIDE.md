# Power BI Guide

This guide creates the model and four dashboard pages. It does not create a fake `.pbix`; the final Power BI file must be built in Power BI Desktop.

## 1. Import the cleaned CSV files

1. Open Power BI Desktop and choose **Get data > Text/CSV**.
2. Import all six files from `data/cleaned/`.
3. Select **Transform Data** and rename the queries:

| CSV | Power BI table |
|---|---|
| `sales.csv` | `FactSales` |
| `inventory.csv` | `FactInventory` |
| `returns.csv` | `FactReturns` |
| `products.csv` | `DimProduct` |
| `stores.csv` | `DimStore` |
| `customers.csv` | `DimCustomer` |

4. Set ID/name/category columns to Text; quantities to Whole Number; money/discount fields to Decimal Number; and date columns to Date.
5. Confirm that `FactSales` has 13 columns, including the calculated revenue, cost, and profit fields.
6. Select **Close & Apply**.

## 2. Create the date table

Choose **Modeling > New table** and enter:

```DAX
DimDate =
VAR AllDates =
    UNION (
        SELECTCOLUMNS ( FactSales, "Date", FactSales[order_date] ),
        SELECTCOLUMNS ( FactInventory, "Date", FactInventory[date] ),
        SELECTCOLUMNS ( FactReturns, "Date", FactReturns[return_date] )
    )
RETURN
ADDCOLUMNS (
    CALENDAR ( MINX ( AllDates, [Date] ), MAXX ( AllDates, [Date] ) ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year Month", FORMAT ( [Date], "YYYY-MM" ),
    "Year Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
    "Quarter", "Q" & FORMAT ( [Date], "Q" )
)
```

Then:

1. Select `DimDate[Year Month]` and use **Sort by column > Year Month Sort**.
2. Select `DimDate` and choose **Table tools > Mark as date table > Date**.
3. Hide `Year Month Sort` from report view.

## 3. Build the star schema

Create one-to-many, single-direction relationships from dimensions to facts:

| One side | Many side | Active relationship |
|---|---|---|
| `DimCustomer[customer_id]` | `FactSales[customer_id]` | Yes |
| `DimStore[store_id]` | `FactSales[store_id]` | Yes |
| `DimStore[store_id]` | `FactInventory[store_id]` | Yes |
| `DimProduct[product_id]` | `FactSales[product_id]` | Yes |
| `DimProduct[product_id]` | `FactInventory[product_id]` | Yes |
| `DimProduct[product_id]` | `FactReturns[product_id]` | Yes |
| `DimDate[Date]` | `FactSales[order_date]` | Yes |
| `DimDate[Date]` | `FactInventory[date]` | Yes |
| `DimDate[Date]` | `FactReturns[return_date]` | Yes |

Do not directly relate the three fact tables. Shared dimensions filter them consistently and reduce ambiguous paths.

### Returns by store or customer

`returns.csv` intentionally contains only return-event fields. For store/customer return analysis, enrich it in Power Query:

1. In both `FactSales` and `FactReturns`, add a custom column: `[order_id] & "|" & [product_id]` and name it `sale_line_key`.
2. Merge `FactReturns` with a reference of `FactSales` on `sale_line_key` using a Left Outer join.
3. Expand only `store_id` and `customer_id` from the match.
4. Add relationships from `DimStore` and `DimCustomer` to those new fields in `FactReturns`.
5. Confirm the merge does not change the number of return rows. The cleaned sales composite key is unique, so every valid return should match once.

## 4. Create measures

Create an empty `_Measures` table and add the measures from `DAX_MEASURES.md`. Place measures in display folders such as Sales, Customers, Inventory, Returns, and Time Intelligence.

## 5. Report-wide design

- Canvas: 16:9.
- Theme: dark navy headings, blue primary series, teal positive emphasis, gold warning emphasis, light neutral background.
- Add slicers for Date, Province, Store, Category, and Customer Segment where relevant.
- Synchronize the Date, Province, Store, and Category slicers across pages.
- Show CAD in titles/tooltips. Use whole dollars for cards and one or two decimals for rates.
- Add a tooltip or information icon stating that data is synthetic.
- Avoid 3D charts, dual axes, and truncated bar-chart axes.

## Page 1: Executive Overview

**Purpose:** company health and trend.

- Cards: Total Revenue, Total Profit, Profit Margin, Orders, Average Order Value.
- Line chart: `DimDate[Year Month]` by Total Revenue.
- Clustered bar chart: `DimProduct[category]` by Total Revenue, sorted descending.
- Bar chart: `DimStore[store_name]` by Total Revenue, sorted descending.
- Table or bar chart: top 10 `DimProduct[product_name]` by Total Revenue.
- Column chart: `DimDate[Year Month]` by Month-over-Month Growth with a zero reference line.

## Page 2: Sales & Product Analysis

**Purpose:** identify products/categories that drive sales and margin.

- Product ranking table: product, category, revenue, profit, margin, units, revenue rank.
- Bar chart: category by Total Revenue.
- Bar chart: category by Profit Margin; use a zero-based scale when practical.
- Line chart: Year Month by Total Revenue and Total Profit as separate small multiples or two adjacent charts; avoid a dual axis.
- Scatter chart: Average Discount on X, Profit Margin on Y, bubble size = Total Revenue, detail = product. Title it as an association, not a causal relationship.
- Slicers: category, subcategory, supplier, store, date.

## Page 3: Inventory Analysis

**Purpose:** find availability risk and slow-moving stock.

- Cards: Stockout Rate, Closing Inventory Value, Inventory Turnover.
- Table: latest-date store/product rows where closing stock is below reorder level.
- Bar chart: bottom 20 products by inventory `units_sold`, with average closing stock in the tooltip.
- Bar chart: category by Closing Inventory Value.
- Matrix: store by category with Stockout Rate and conditional formatting.
- Add a visible note: inventory is monthly store-product data, so stockout rate is a snapshot rate.

## Page 4: Customer & Returns

**Purpose:** monitor repeat behavior and product-return risk.

- Cards: Customers, Repeat Customer Rate, Return Rate, Returned Units.
- Stacked columns: Year Month by new-customer orders versus repeat orders. This requires the order-sequence logic from `05_customer_analysis.sql` or a prepared Power Query table.
- Bar chart: source `customer_segment` by Customers or Total Revenue.
- Table: top customers by Total Revenue, Orders, and AOV.
- Bar chart: `FactReturns[return_reason]` by Returned Units.
- Bar chart: `DimProduct[category]` by Return Rate.

## 6. Model QA checklist

- [ ] Every dimension key is on the one side of its relationship.
- [ ] Cross-filter direction is Single from dimension to fact.
- [ ] `DimDate` is marked as the date table.
- [ ] `Year Month` sorts chronologically.
- [ ] Total Revenue matches `SUM(sales.net_revenue)` from SQL/Excel.
- [ ] Orders uses distinct `order_id`, not row count.
- [ ] Return Rate divides separately aggregated returned units by sold units.
- [ ] The returns enrichment merge, if used, preserves the return row count.
- [ ] All pages state the date range and synthetic-data caveat.

## 7. Publish-ready checks

1. Reset filters and verify the company-level totals against the Excel Executive Summary.
2. Filter one store and one category; confirm all visuals respond as expected.
3. Check the first month’s MoM value is blank.
4. Check no visual silently excludes `CUST_UNKNOWN` except customer-count/behavior metrics.
5. Review titles so they describe the metric rather than claim an untested cause.
6. Save the final file as `powerbi/Retail_Operations_Analytics.pbix`.

