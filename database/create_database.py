"""Create the SQLite analytics database from cleaned CSV files."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


TABLE_ORDER = ["customers", "products", "stores", "sales", "inventory", "returns"]

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    province TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    customer_segment TEXT NOT NULL CHECK (customer_segment IN ('New', 'Regular', 'Loyal'))
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    supplier TEXT NOT NULL
);

CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    city TEXT NOT NULL,
    province TEXT NOT NULL,
    store_type TEXT NOT NULL CHECK (store_type IN ('Urban', 'Suburban')),
    opening_date TEXT NOT NULL
);

CREATE TABLE sales (
    order_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount_pct REAL NOT NULL CHECK (discount_pct BETWEEN 0 AND 1),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    gross_revenue REAL NOT NULL,
    net_revenue REAL NOT NULL,
    cost REAL NOT NULL,
    profit REAL NOT NULL,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE inventory (
    date TEXT NOT NULL,
    store_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    opening_stock INTEGER NOT NULL CHECK (opening_stock >= 0),
    units_received INTEGER NOT NULL CHECK (units_received >= 0),
    units_sold INTEGER NOT NULL CHECK (units_sold >= 0),
    closing_stock INTEGER NOT NULL CHECK (closing_stock >= 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
    PRIMARY KEY (date, store_id, product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE returns (
    return_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    return_date TEXT NOT NULL,
    quantity_returned INTEGER NOT NULL CHECK (quantity_returned > 0),
    return_reason TEXT NOT NULL,
    FOREIGN KEY (order_id, product_id) REFERENCES sales(order_id, product_id)
);

CREATE INDEX idx_sales_order_date ON sales(order_date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_store ON sales(store_id);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_inventory_date ON inventory(date);
CREATE INDEX idx_inventory_store_product ON inventory(store_id, product_id);
CREATE INDEX idx_returns_date ON returns(return_date);
CREATE INDEX idx_returns_order_product ON returns(order_id, product_id);
"""


def create_database(
    cleaned_dir: Path | str,
    database_path: Path | str,
) -> dict[str, int]:
    """Build a fresh SQLite database and verify its integrity."""
    cleaned_path = Path(cleaned_dir)
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [name for name in TABLE_ORDER if not (cleaned_path / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"Missing cleaned CSV files: {', '.join(missing)}")
    if db_path.exists():
        db_path.unlink()

    counts: dict[str, int] = {}
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_SQL)
        for table_name in TABLE_ORDER:
            frame = pd.read_csv(cleaned_path / f"{table_name}.csv")
            frame.to_sql(table_name, connection, if_exists="append", index=False, chunksize=1_000)
            counts[table_name] = len(frame)
        connection.commit()

        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if foreign_key_errors:
            raise RuntimeError(f"SQLite foreign key check failed: {foreign_key_errors[:5]}")
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        for table_name, expected_count in counts.items():
            actual_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if actual_count != expected_count:
                raise RuntimeError(
                    f"Row-count mismatch for {table_name}: CSV={expected_count}, database={actual_count}"
                )

    print("SQLite database created successfully.")
    for name, count in counts.items():
        print(f"  {name:10s}: {count:,} rows")
    print(f"  database   : {db_path.resolve()}")
    return counts


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleaned-dir", type=Path, default=project_root / "data" / "cleaned")
    parser.add_argument("--database", type=Path, default=project_root / "database" / "retail_analytics.db")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_database(args.cleaned_dir, args.database)

