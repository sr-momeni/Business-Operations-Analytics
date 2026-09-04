"""Clean the raw retail CSV files and create analysis-ready datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


TABLE_NAMES = ["customers", "products", "stores", "sales", "inventory", "returns"]
PROVINCE_MAP = {
    "ab": "Alberta",
    "alberta": "Alberta",
    "bc": "British Columbia",
    "b.c.": "British Columbia",
    "british columbia": "British Columbia",
    "mb": "Manitoba",
    "manitoba": "Manitoba",
    "ns": "Nova Scotia",
    "nova scotia": "Nova Scotia",
    "on": "Ontario",
    "ont": "Ontario",
    "ont.": "Ontario",
    "ontario": "Ontario",
    "qc": "Quebec",
    "quebec": "Quebec",
    "québec": "Quebec",
    "sk": "Saskatchewan",
    "saskatchewan": "Saskatchewan",
}
ALLOWED_CATEGORIES = {"Electronics", "Grocery", "Home", "Personal Care", "Clothing", "Office"}


def _normalize_text(series: pd.Series, *, title: bool = False, upper: bool = False) -> pd.Series:
    result = series.astype("string").str.strip()
    if title:
        result = result.str.title()
    if upper:
        result = result.str.upper()
    return result.replace({"": pd.NA, "Nan": pd.NA, "NAN": pd.NA})


def _normalize_province(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip().str.lower()
    return normalized.map(PROVINCE_MAP).astype("string")


def _remove_duplicates(
    frame: pd.DataFrame,
    key: list[str],
    stats: dict[str, object],
) -> pd.DataFrame:
    before = len(frame)
    frame = frame.drop_duplicates().copy()
    stats["exact_duplicates_removed"] = before - len(frame)
    before_key = len(frame)
    frame = frame.drop_duplicates(subset=key, keep="first").copy()
    stats["primary_key_duplicates_removed"] = before_key - len(frame)
    return frame


def _count_missing(frame: pd.DataFrame) -> dict[str, int]:
    return {column: int(count) for column, count in frame.isna().sum().items() if count}


def _require_columns(frame: pd.DataFrame, table: str, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{table}.csv is missing required columns: {', '.join(missing)}")


def _clean_customers(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["customer_id", "customer_name", "city", "province", "signup_date", "customer_segment"]
    _require_columns(raw, "customers", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["customer_id"], stats)
    frame["customer_id"] = _normalize_text(frame["customer_id"], upper=True)
    frame["customer_name"] = _normalize_text(frame["customer_name"], title=True)
    frame["city"] = _normalize_text(frame["city"], title=True)
    frame["province"] = _normalize_province(frame["province"])
    frame["customer_segment"] = _normalize_text(frame["customer_segment"], title=True)
    frame["signup_date"] = pd.to_datetime(frame["signup_date"], errors="coerce")

    frame["customer_name"] = frame["customer_name"].fillna(
        "Unknown Customer " + frame["customer_id"].fillna("Record")
    )
    frame["customer_segment"] = frame["customer_segment"].where(
        frame["customer_segment"].isin(["New", "Regular", "Loyal"]), "Regular"
    )
    frame["signup_date"] = frame["signup_date"].fillna(pd.Timestamp("2023-01-01"))

    valid = (
        frame["customer_id"].str.fullmatch(r"CUST\d{4}", na=False)
        & frame["city"].notna()
        & frame["province"].notna()
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame["signup_date"] = frame["signup_date"].dt.strftime("%Y-%m-%d")
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def _clean_products(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["product_id", "product_name", "category", "subcategory", "unit_cost", "unit_price", "supplier"]
    _require_columns(raw, "products", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["product_id"], stats)
    frame["product_id"] = _normalize_text(frame["product_id"], upper=True)
    for column in ["product_name", "category", "subcategory", "supplier"]:
        frame[column] = _normalize_text(frame[column], title=True)
    frame["supplier"] = frame["supplier"].fillna("Unknown Supplier")
    frame["unit_cost"] = pd.to_numeric(frame["unit_cost"], errors="coerce")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
    valid = (
        frame["product_id"].str.fullmatch(r"PROD\d{3}", na=False)
        & frame["product_name"].notna()
        & frame["category"].isin(ALLOWED_CATEGORIES)
        & frame["subcategory"].notna()
        & frame["unit_cost"].ge(0)
        & frame["unit_price"].ge(0)
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame[["unit_cost", "unit_price"]] = frame[["unit_cost", "unit_price"]].round(2)
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def _clean_stores(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["store_id", "store_name", "city", "province", "store_type", "opening_date"]
    _require_columns(raw, "stores", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["store_id"], stats)
    frame["store_id"] = _normalize_text(frame["store_id"], upper=True)
    for column in ["store_name", "city", "store_type"]:
        frame[column] = _normalize_text(frame[column], title=True)
    frame["province"] = _normalize_province(frame["province"])
    frame["opening_date"] = pd.to_datetime(frame["opening_date"], errors="coerce")
    frame["opening_date"] = frame["opening_date"].fillna(pd.Timestamp("2018-01-01"))
    valid = (
        frame["store_id"].str.fullmatch(r"STORE\d{2}", na=False)
        & frame["store_name"].notna()
        & frame["city"].notna()
        & frame["province"].notna()
        & frame["store_type"].isin(["Urban", "Suburban"])
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame["opening_date"] = frame["opening_date"].dt.strftime("%Y-%m-%d")
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def _clean_sales(
    raw: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["order_id", "order_date", "customer_id", "store_id", "product_id", "quantity", "unit_price", "discount_pct"]
    _require_columns(raw, "sales", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["order_id", "product_id"], stats)
    for column in ["order_id", "customer_id", "store_id", "product_id"]:
        frame[column] = _normalize_text(frame[column], upper=True)
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    for column in ["quantity", "unit_price", "discount_pct"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    product_price = products.set_index("product_id")["unit_price"]
    missing_price = frame["unit_price"].isna() & frame["product_id"].isin(product_price.index)
    frame.loc[missing_price, "unit_price"] = frame.loc[missing_price, "product_id"].map(product_price)

    valid_customer_ids = set(customers["customer_id"])
    unknown_customer_mask = frame["customer_id"].isna() | ~frame["customer_id"].isin(valid_customer_ids)
    frame.loc[unknown_customer_mask, "customer_id"] = "CUST_UNKNOWN"
    stats["customer_ids_assigned_to_unknown"] = int(unknown_customer_mask.sum())

    valid = (
        frame["order_id"].str.fullmatch(r"ORD\d{6}", na=False)
        & frame["order_date"].notna()
        & frame["store_id"].isin(set(stores["store_id"]))
        & frame["product_id"].isin(set(products["product_id"]))
        & frame["quantity"].gt(0)
        & np.isclose(frame["quantity"], frame["quantity"].round(), equal_nan=False)
        & frame["unit_price"].ge(0)
        & frame["discount_pct"].between(0, 1, inclusive="both")
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame["quantity"] = frame["quantity"].astype(int)
    frame["unit_cost"] = frame["product_id"].map(products.set_index("product_id")["unit_cost"])
    frame["gross_revenue"] = (frame["quantity"] * frame["unit_price"]).round(2)
    frame["net_revenue"] = (frame["gross_revenue"] * (1 - frame["discount_pct"])).round(2)
    frame["cost"] = (frame["quantity"] * frame["unit_cost"]).round(2)
    frame["profit"] = (frame["net_revenue"] - frame["cost"]).round(2)
    frame["order_date"] = frame["order_date"].dt.strftime("%Y-%m-%d")
    money_columns = ["unit_price", "unit_cost", "gross_revenue", "net_revenue", "cost", "profit"]
    frame[money_columns] = frame[money_columns].round(2)
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def _clean_inventory(
    raw: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["date", "store_id", "product_id", "opening_stock", "units_received", "units_sold", "closing_stock", "reorder_level"]
    _require_columns(raw, "inventory", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["date", "store_id", "product_id"], stats)
    frame["store_id"] = _normalize_text(frame["store_id"], upper=True)
    frame["product_id"] = _normalize_text(frame["product_id"], upper=True)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    numeric_columns = ["opening_stock", "units_received", "units_sold", "closing_stock", "reorder_level"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    expected_closing = frame["opening_stock"] + frame["units_received"] - frame["units_sold"]
    can_repair = expected_closing.ge(0) & expected_closing.notna()
    needs_repair = can_repair & (
        frame["closing_stock"].lt(0)
        | ~np.isclose(frame["closing_stock"], expected_closing, equal_nan=False)
    )
    frame.loc[needs_repair, "closing_stock"] = expected_closing.loc[needs_repair]
    stats["closing_balances_corrected"] = int(needs_repair.sum())

    valid = (
        frame["date"].notna()
        & frame["store_id"].isin(set(stores["store_id"]))
        & frame["product_id"].isin(set(products["product_id"]))
        & frame[numeric_columns].notna().all(axis=1)
        & frame[numeric_columns].ge(0).all(axis=1)
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame[numeric_columns] = frame[numeric_columns].astype(int)
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def _clean_returns(
    raw: pd.DataFrame,
    sales: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    required = ["return_id", "order_id", "product_id", "return_date", "quantity_returned", "return_reason"]
    _require_columns(raw, "returns", required)
    stats: dict[str, object] = {"rows_before": len(raw), "missing_values_before": _count_missing(raw)}
    frame = _remove_duplicates(raw, ["return_id"], stats)
    for column in ["return_id", "order_id", "product_id"]:
        frame[column] = _normalize_text(frame[column], upper=True)
    frame["return_reason"] = _normalize_text(frame["return_reason"], title=True).fillna("Unknown")
    frame["return_date"] = pd.to_datetime(frame["return_date"], errors="coerce")
    frame["quantity_returned"] = pd.to_numeric(frame["quantity_returned"], errors="coerce")

    sale_lookup = sales.set_index(["order_id", "product_id"])[["order_date", "quantity"]]
    keys = pd.MultiIndex.from_frame(frame[["order_id", "product_id"]])
    matching = keys.isin(sale_lookup.index)
    order_dates = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    sold_quantities = pd.Series(np.nan, index=frame.index, dtype=float)
    if matching.any():
        matched_values = sale_lookup.reindex(keys[matching])
        order_dates.loc[matching] = pd.to_datetime(matched_values["order_date"].to_numpy())
        sold_quantities.loc[matching] = matched_values["quantity"].to_numpy(dtype=float)

    valid = (
        frame["return_id"].str.fullmatch(r"RET\d{6}", na=False)
        & matching
        & frame["return_date"].notna()
        & frame["quantity_returned"].gt(0)
        & np.isclose(frame["quantity_returned"], frame["quantity_returned"].round(), equal_nan=False)
        & frame["quantity_returned"].le(sold_quantities)
        & frame["return_date"].ge(order_dates)
    )
    stats["invalid_rows_removed"] = int((~valid).sum())
    frame = frame.loc[valid, required].copy()
    frame["quantity_returned"] = frame["quantity_returned"].astype(int)
    frame["return_date"] = frame["return_date"].dt.strftime("%Y-%m-%d")
    stats["missing_values_handled"] = int(sum(stats["missing_values_before"].values()))
    stats["rows_after"] = len(frame)
    return frame, stats


def clean_data(
    raw_dir: Path | str,
    cleaned_dir: Path | str,
) -> dict[str, pd.DataFrame]:
    """Clean raw files, validate relationships, and export cleaned CSVs."""
    raw_path = Path(raw_dir)
    cleaned_path = Path(cleaned_dir)
    cleaned_path.mkdir(parents=True, exist_ok=True)
    missing_files = [name for name in TABLE_NAMES if not (raw_path / f"{name}.csv").exists()]
    if missing_files:
        raise FileNotFoundError(f"Missing raw CSV files: {', '.join(missing_files)}")

    raw = {name: pd.read_csv(raw_path / f"{name}.csv") for name in TABLE_NAMES}
    summary: dict[str, dict[str, object]] = {}
    customers, summary["customers"] = _clean_customers(raw["customers"])
    products, summary["products"] = _clean_products(raw["products"])
    stores, summary["stores"] = _clean_stores(raw["stores"])

    unknown_customer = pd.DataFrame(
        [{
            "customer_id": "CUST_UNKNOWN",
            "customer_name": "Unknown Customer",
            "city": "Unknown",
            "province": "Ontario",
            "signup_date": "2023-01-01",
            "customer_segment": "New",
        }]
    )
    customers = pd.concat([customers, unknown_customer], ignore_index=True)
    summary["customers"]["rows_after"] = len(customers)
    summary["customers"]["note"] = "Added CUST_UNKNOWN to preserve sales with missing or invalid customer IDs."

    sales, summary["sales"] = _clean_sales(raw["sales"], customers, products, stores)
    inventory, summary["inventory"] = _clean_inventory(raw["inventory"], products, stores)
    returns, summary["returns"] = _clean_returns(raw["returns"], sales)

    cleaned = {
        "customers": customers,
        "products": products,
        "stores": stores,
        "sales": sales,
        "inventory": inventory,
        "returns": returns,
    }
    for name, frame in cleaned.items():
        frame.to_csv(cleaned_path / f"{name}.csv", index=False)

    (cleaned_path / "cleaning_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("Cleaning completed successfully.")
    for name in TABLE_NAMES:
        table_stats = summary[name]
        print(
            f"  {name:10s}: {table_stats['rows_before']:,} -> {table_stats['rows_after']:,} rows | "
            f"exact duplicates {table_stats['exact_duplicates_removed']:,} | "
            f"key duplicates {table_stats['primary_key_duplicates_removed']:,} | "
            f"invalid removed {table_stats['invalid_rows_removed']:,} | "
            f"missing handled {table_stats['missing_values_handled']:,}"
        )
    print(f"  output     : {cleaned_path.resolve()}")
    return cleaned


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=project_root / "data" / "raw")
    parser.add_argument("--cleaned-dir", type=Path, default=project_root / "data" / "cleaned")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_data(args.raw_dir, args.cleaned_dir)

