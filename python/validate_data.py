"""Validate cleaned retail datasets and fail clearly on any broken rule."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


TABLE_NAMES = ["customers", "products", "stores", "sales", "inventory", "returns"]
PRIMARY_KEYS = {
    "customers": ["customer_id"],
    "products": ["product_id"],
    "stores": ["store_id"],
    "sales": ["order_id", "product_id"],
    "inventory": ["date", "store_id", "product_id"],
    "returns": ["return_id"],
}
REQUIRED_COLUMNS = {
    "customers": ["customer_id", "customer_name", "city", "province", "signup_date", "customer_segment"],
    "products": ["product_id", "product_name", "category", "subcategory", "unit_cost", "unit_price", "supplier"],
    "stores": ["store_id", "store_name", "city", "province", "store_type", "opening_date"],
    "sales": ["order_id", "order_date", "customer_id", "store_id", "product_id", "quantity", "unit_price", "discount_pct", "unit_cost", "gross_revenue", "net_revenue", "cost", "profit"],
    "inventory": ["date", "store_id", "product_id", "opening_stock", "units_received", "units_sold", "closing_stock", "reorder_level"],
    "returns": ["return_id", "order_id", "product_id", "return_date", "quantity_returned", "return_reason"],
}


class DataValidationError(AssertionError):
    """Raised when one or more data validation rules fail."""


def _add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def validate_data(cleaned_dir: Path | str) -> dict[str, int]:
    """Run schema, key, relationship, and calculation checks."""
    cleaned_path = Path(cleaned_dir)
    missing_files = [name for name in TABLE_NAMES if not (cleaned_path / f"{name}.csv").exists()]
    if missing_files:
        raise FileNotFoundError(f"Missing cleaned CSV files: {', '.join(missing_files)}")

    tables = {name: pd.read_csv(cleaned_path / f"{name}.csv") for name in TABLE_NAMES}
    failures: list[str] = []

    for name, frame in tables.items():
        missing_columns = sorted(set(REQUIRED_COLUMNS[name]) - set(frame.columns))
        _add_failure(failures, not missing_columns, f"{name}: missing columns {missing_columns}")
        if missing_columns:
            continue
        null_counts = frame[REQUIRED_COLUMNS[name]].isna().sum()
        _add_failure(
            failures,
            int(null_counts.sum()) == 0,
            f"{name}: required fields contain nulls {null_counts[null_counts > 0].to_dict()}",
        )
        duplicated = frame.duplicated(subset=PRIMARY_KEYS[name]).sum()
        _add_failure(
            failures,
            int(duplicated) == 0,
            f"{name}: primary key {PRIMARY_KEYS[name]} has {int(duplicated)} duplicates",
        )

    customers = tables["customers"]
    products = tables["products"]
    stores = tables["stores"]
    sales = tables["sales"]
    inventory = tables["inventory"]
    returns = tables["returns"]

    _add_failure(failures, sales["quantity"].gt(0).all(), "sales: quantity must be greater than zero")
    _add_failure(failures, sales[["unit_price", "unit_cost"]].ge(0).all().all(), "sales: prices and costs must be non-negative")
    _add_failure(failures, products[["unit_price", "unit_cost"]].ge(0).all().all(), "products: prices and costs must be non-negative")
    _add_failure(failures, sales["discount_pct"].between(0, 1).all(), "sales: discount_pct must be between 0 and 1")
    _add_failure(failures, inventory["closing_stock"].ge(0).all(), "inventory: closing_stock must be non-negative")
    _add_failure(failures, inventory[["opening_stock", "units_received", "units_sold", "reorder_level"]].ge(0).all().all(), "inventory: stock fields must be non-negative")

    _add_failure(failures, sales["customer_id"].isin(customers["customer_id"]).all(), "sales: invalid customer foreign keys")
    _add_failure(failures, sales["product_id"].isin(products["product_id"]).all(), "sales: invalid product foreign keys")
    _add_failure(failures, sales["store_id"].isin(stores["store_id"]).all(), "sales: invalid store foreign keys")
    _add_failure(failures, inventory["product_id"].isin(products["product_id"]).all(), "inventory: invalid product foreign keys")
    _add_failure(failures, inventory["store_id"].isin(stores["store_id"]).all(), "inventory: invalid store foreign keys")

    sale_keys = pd.MultiIndex.from_frame(sales[["order_id", "product_id"]])
    return_keys = pd.MultiIndex.from_frame(returns[["order_id", "product_id"]])
    _add_failure(failures, return_keys.isin(sale_keys).all(), "returns: invalid order/product foreign keys")

    expected_gross = (sales["quantity"] * sales["unit_price"]).round(2)
    expected_net = (expected_gross * (1 - sales["discount_pct"])).round(2)
    expected_cost = (sales["quantity"] * sales["unit_cost"]).round(2)
    expected_profit = (expected_net - expected_cost).round(2)
    _add_failure(failures, np.allclose(sales["gross_revenue"], expected_gross, atol=0.01), "sales: gross_revenue calculation is incorrect")
    _add_failure(failures, np.allclose(sales["net_revenue"], expected_net, atol=0.01), "sales: net_revenue calculation is incorrect")
    _add_failure(failures, np.allclose(sales["cost"], expected_cost, atol=0.01), "sales: cost calculation is incorrect")
    _add_failure(failures, np.allclose(sales["profit"], expected_profit, atol=0.01), "sales: profit calculation is incorrect")

    inventory_balance = inventory["opening_stock"] + inventory["units_received"] - inventory["units_sold"]
    _add_failure(failures, inventory_balance.eq(inventory["closing_stock"]).all(), "inventory: opening + received - sold must equal closing stock")

    if not returns.empty:
        sales_lookup = sales.set_index(["order_id", "product_id"])[["order_date", "quantity"]]
        matched_sales = sales_lookup.reindex(return_keys)
        return_dates = pd.to_datetime(returns["return_date"], errors="coerce")
        order_dates = pd.to_datetime(matched_sales["order_date"].to_numpy(), errors="coerce")
        sold_quantities = matched_sales["quantity"].to_numpy()
        _add_failure(failures, return_dates.notna().all(), "returns: invalid return dates")
        _add_failure(failures, (return_dates.to_numpy() >= order_dates).all(), "returns: return_date occurs before order_date")
        _add_failure(failures, (returns["quantity_returned"].to_numpy() <= sold_quantities).all(), "returns: quantity_returned exceeds quantity sold")

    for table_name, date_column in [
        ("customers", "signup_date"),
        ("stores", "opening_date"),
        ("sales", "order_date"),
        ("inventory", "date"),
        ("returns", "return_date"),
    ]:
        valid_dates = pd.to_datetime(tables[table_name][date_column], errors="coerce").notna().all()
        _add_failure(failures, bool(valid_dates), f"{table_name}: {date_column} contains invalid dates")

    if failures:
        details = "\n".join(f"  - {failure}" for failure in failures)
        raise DataValidationError(f"Data validation failed with {len(failures)} problem(s):\n{details}")

    row_counts = {name: len(frame) for name, frame in tables.items()}
    print("All validation checks passed.")
    for name, count in row_counts.items():
        print(f"  {name:10s}: {count:,} rows")
    print("  Checks     : primary keys, required fields, ranges, calculations, dates, and foreign keys")
    return row_counts


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleaned-dir", type=Path, default=project_root / "data" / "cleaned")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    validate_data(args.cleaned_dir)

