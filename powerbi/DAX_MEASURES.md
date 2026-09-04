# Beginner-Friendly DAX Measures

These measures assume the cleaned CSV queries were renamed to `FactSales`, `FactInventory`, `FactReturns`, `DimProduct`, `DimStore`, `DimCustomer`, and `DimDate` as described in `POWER_BI_GUIDE.md`.

Create a dedicated empty table called `_Measures` and store the measures there. Format currency as CAD, rates as percentages, and counts as whole numbers.

## Core sales measures

```DAX
Total Revenue =
SUM ( FactSales[net_revenue] )
```

Adds net revenue after discounts.

```DAX
Total Profit =
SUM ( FactSales[profit] )
```

Adds gross product profit. It does not include operating expenses.

```DAX
Profit Margin =
DIVIDE ( [Total Profit], [Total Revenue] )
```

Returns profit per revenue dollar and safely handles a zero denominator.

```DAX
Orders =
DISTINCTCOUNT ( FactSales[order_id] )
```

Counts each order once even when it contains several products.

```DAX
Units Sold =
SUM ( FactSales[quantity] )
```

```DAX
Average Order Value =
DIVIDE ( [Total Revenue], [Orders] )
```

```DAX
Customers =
CALCULATE (
    DISTINCTCOUNT ( FactSales[customer_id] ),
    FactSales[customer_id] <> "CUST_UNKNOWN"
)
```

Excludes sales whose raw customer ID was missing or invalid.

```DAX
Average Discount =
AVERAGE ( FactSales[discount_pct] )
```

This is a sales-line average, not weighted by units or revenue.

## Returns

```DAX
Returned Units =
SUM ( FactReturns[quantity_returned] )
```

```DAX
Return Rate =
DIVIDE ( [Returned Units], [Units Sold] )
```

The numerator and denominator come from separate fact tables, avoiding duplicated sales values. Under a date filter, this is an operational period rate: returns are filtered by return date and sales by order date.

## Time intelligence

The `DimDate[Date]` column must be marked as the date table.

```DAX
Previous Month Revenue =
CALCULATE (
    [Total Revenue],
    DATEADD ( DimDate[Date], -1, MONTH )
)
```

```DAX
Month-over-Month Growth =
DIVIDE (
    [Total Revenue] - [Previous Month Revenue],
    [Previous Month Revenue]
)
```

The first month returns blank because there is no earlier month.

```DAX
Year-to-Date Revenue =
TOTALYTD ( [Total Revenue], DimDate[Date] )
```

## Inventory measures used on Page 3

```DAX
Inventory Observations =
COUNTROWS ( FactInventory )
```

```DAX
Stockout Observations =
CALCULATE (
    COUNTROWS ( FactInventory ),
    FactInventory[closing_stock] = 0
)
```

```DAX
Stockout Rate =
DIVIDE ( [Stockout Observations], [Inventory Observations] )
```

```DAX
Closing Inventory Value =
SUMX (
    FactInventory,
    FactInventory[closing_stock] * RELATED ( DimProduct[unit_cost] )
)
```

```DAX
Average Monthly Inventory Value =
AVERAGEX (
    VALUES ( DimDate[Year Month] ),
    [Closing Inventory Value]
)
```

```DAX
Inventory Turnover =
DIVIDE ( SUM ( FactSales[cost] ), [Average Monthly Inventory Value] )
```

Always show the selected date range beside Inventory Turnover because the numerator grows with the period length.

## Optional customer measures

```DAX
Repeat Customers =
COUNTROWS (
    FILTER (
        VALUES ( FactSales[customer_id] ),
        FactSales[customer_id] <> "CUST_UNKNOWN"
            && CALCULATE ( DISTINCTCOUNT ( FactSales[order_id] ) ) >= 2
    )
)
```

```DAX
Repeat Customer Rate =
DIVIDE ( [Repeat Customers], [Customers] )
```

