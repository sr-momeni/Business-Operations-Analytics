"""Generate a reproducible synthetic Canadian retail dataset.

The clean business records are created first. A small, documented set of data
quality issues is then added to the raw CSV files so the cleaning pipeline has
realistic problems to solve.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_END_DATE = "2025-06-30"

CATEGORY_CONFIG = {
    "Electronics": {
        "subcategories": ["Audio", "Computers", "Mobile Accessories", "Smart Home"],
        "price_range": (25, 650),
        "cost_ratio": (0.58, 0.78),
    },
    "Grocery": {
        "subcategories": ["Beverages", "Pantry", "Snacks", "Breakfast"],
        "price_range": (2.5, 35),
        "cost_ratio": (0.55, 0.76),
    },
    "Home": {
        "subcategories": ["Kitchen", "Decor", "Storage", "Bedding"],
        "price_range": (8, 220),
        "cost_ratio": (0.48, 0.70),
    },
    "Personal Care": {
        "subcategories": ["Hair Care", "Skin Care", "Oral Care", "Wellness"],
        "price_range": (4, 85),
        "cost_ratio": (0.45, 0.68),
    },
    "Clothing": {
        "subcategories": ["Men", "Women", "Children", "Accessories"],
        "price_range": (10, 180),
        "cost_ratio": (0.42, 0.65),
    },
    "Office": {
        "subcategories": ["Paper", "Writing", "Organization", "Desk Accessories"],
        "price_range": (3, 140),
        "cost_ratio": (0.48, 0.69),
    },
}

STORE_TEMPLATES = [
    ("Toronto Central", "Toronto", "Ontario", "Urban", "2016-04-18"),
    ("Vancouver West", "Vancouver", "British Columbia", "Urban", "2017-08-07"),
    ("Montreal Centre", "Montreal", "Quebec", "Urban", "2015-11-12"),
    ("Calgary North", "Calgary", "Alberta", "Suburban", "2018-03-26"),
    ("Ottawa East", "Ottawa", "Ontario", "Suburban", "2019-06-03"),
    ("Edmonton South", "Edmonton", "Alberta", "Suburban", "2018-09-17"),
    ("Winnipeg Market", "Winnipeg", "Manitoba", "Urban", "2020-02-10"),
    ("Halifax Harbour", "Halifax", "Nova Scotia", "Urban", "2020-10-05"),
    ("Quebec City North", "Quebec City", "Quebec", "Suburban", "2021-05-31"),
    ("Saskatoon Centre", "Saskatoon", "Saskatchewan", "Suburban", "2021-11-15"),
]

CITY_PROVINCES = [
    ("Toronto", "Ontario"),
    ("Ottawa", "Ontario"),
    ("Mississauga", "Ontario"),
    ("Vancouver", "British Columbia"),
    ("Victoria", "British Columbia"),
    ("Montreal", "Quebec"),
    ("Quebec City", "Quebec"),
    ("Calgary", "Alberta"),
    ("Edmonton", "Alberta"),
    ("Winnipeg", "Manitoba"),
    ("Halifax", "Nova Scotia"),
    ("Saskatoon", "Saskatchewan"),
]

FIRST_NAMES = [
    "Alex", "Amelia", "Avery", "Benjamin", "Charlotte", "Daniel", "Ella", "Ethan",
    "Fatima", "Gabriel", "Grace", "Harper", "Isla", "Jack", "James", "Layla",
    "Liam", "Lucas", "Maya", "Mia", "Noah", "Olivia", "Owen", "Priya", "Sofia",
]
LAST_NAMES = [
    "Anderson", "Brown", "Campbell", "Chen", "Clarke", "Davis", "Dubois", "Evans",
    "Garcia", "Gauthier", "Johnson", "Khan", "Lee", "Martin", "Miller", "Patel",
    "Roy", "Singh", "Smith", "Taylor", "Thomas", "Tremblay", "Wilson", "Wong",
]


def _random_dates(
    rng: np.random.Generator,
    start: pd.Timestamp,
    end: pd.Timestamp,
    size: int,
) -> pd.DatetimeIndex:
    """Return random dates, with mild growth and realistic holiday seasonality."""
    days = pd.date_range(start, end, freq="D")
    months_from_start = (days.year - start.year) * 12 + days.month - start.month
    seasonal = np.select(
        [days.month == 12, days.month == 11, days.month.isin([6, 7, 8]), days.month == 1],
        [1.32, 1.18, 1.08, 0.86],
        default=1.0,
    )
    weights = seasonal * (1 + 0.008 * months_from_start)
    weights = weights / weights.sum()
    return pd.DatetimeIndex(rng.choice(days.to_numpy(), size=size, p=weights))


def _make_customers(
    rng: np.random.Generator,
    count: int,
    start_date: pd.Timestamp,
) -> pd.DataFrame:
    locations = rng.choice(len(CITY_PROVINCES), size=count)
    signup_start = start_date - pd.DateOffset(years=4)
    signup_dates = _random_dates(rng, signup_start, start_date, count)
    segments = rng.choice(["New", "Regular", "Loyal"], size=count, p=[0.24, 0.53, 0.23])

    rows = []
    for i in range(count):
        city, province = CITY_PROVINCES[int(locations[i])]
        first = FIRST_NAMES[int(rng.integers(0, len(FIRST_NAMES)))]
        last = LAST_NAMES[int(rng.integers(0, len(LAST_NAMES)))]
        rows.append(
            {
                "customer_id": f"CUST{i + 1:04d}",
                "customer_name": f"{first} {last}",
                "city": city,
                "province": province,
                "signup_date": signup_dates[i].strftime("%Y-%m-%d"),
                "customer_segment": segments[i],
            }
        )
    return pd.DataFrame(rows)


def _make_products(rng: np.random.Generator, count: int) -> pd.DataFrame:
    categories = list(CATEGORY_CONFIG)
    category_choices = np.resize(np.array(categories), count)
    rng.shuffle(category_choices)
    suppliers = [f"Supplier {letter}" for letter in "ABCDEFGHIJKL"]
    category_counters = {category: 0 for category in categories}
    rows = []

    for i, category in enumerate(category_choices, start=1):
        config = CATEGORY_CONFIG[str(category)]
        category_counters[str(category)] += 1
        subcategory = str(rng.choice(config["subcategories"]))
        low, high = config["price_range"]
        unit_price = round(float(np.exp(rng.uniform(np.log(low), np.log(high)))), 2)
        cost_low, cost_high = config["cost_ratio"]
        unit_cost = round(unit_price * float(rng.uniform(cost_low, cost_high)), 2)
        rows.append(
            {
                "product_id": f"PROD{i:03d}",
                "product_name": f"{subcategory} Item {category_counters[str(category)]:02d}",
                "category": str(category),
                "subcategory": subcategory,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "supplier": str(rng.choice(suppliers)),
            }
        )
    return pd.DataFrame(rows)


def _make_stores(count: int) -> pd.DataFrame:
    if not 1 <= count <= len(STORE_TEMPLATES):
        raise ValueError(f"store count must be between 1 and {len(STORE_TEMPLATES)}")
    rows = []
    for i, (name, city, province, store_type, opening_date) in enumerate(
        STORE_TEMPLATES[:count], start=1
    ):
        rows.append(
            {
                "store_id": f"STORE{i:02d}",
                "store_name": name,
                "city": city,
                "province": province,
                "store_type": store_type,
                "opening_date": opening_date,
            }
        )
    return pd.DataFrame(rows)


def _line_counts(rng: np.random.Generator, n_sales: int) -> np.ndarray:
    """Create 1-4 line items per order and make the total exactly n_sales."""
    n_orders = max(1, int(round(n_sales / 2.15)))
    n_orders = min(n_orders, n_sales)
    counts = rng.choice([1, 2, 3, 4], size=n_orders, p=[0.28, 0.39, 0.24, 0.09])
    while counts.sum() < n_sales:
        candidates = np.flatnonzero(counts < 4)
        take = min(n_sales - int(counts.sum()), len(candidates))
        counts[rng.choice(candidates, size=take, replace=False)] += 1
    while counts.sum() > n_sales:
        candidates = np.flatnonzero(counts > 1)
        take = min(int(counts.sum()) - n_sales, len(candidates))
        counts[rng.choice(candidates, size=take, replace=False)] -= 1
    return counts


def _make_sales(
    rng: np.random.Generator,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    count: int,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    counts = _line_counts(rng, count)
    order_count = len(counts)
    order_dates = _random_dates(rng, start_date, end_date, order_count)

    customer_multiplier = customers["customer_segment"].map(
        {"New": 0.55, "Regular": 1.0, "Loyal": 1.8}
    ).to_numpy(dtype=float)
    customer_weights = customer_multiplier / customer_multiplier.sum()
    store_multiplier = stores["store_type"].map({"Urban": 1.25, "Suburban": 0.9}).to_numpy()
    store_weights = store_multiplier / store_multiplier.sum()
    product_weights = rng.lognormal(mean=0.0, sigma=0.85, size=len(products))
    product_weights = product_weights / product_weights.sum()

    customer_ids = rng.choice(customers["customer_id"], size=order_count, p=customer_weights)
    store_ids = rng.choice(stores["store_id"], size=order_count, p=store_weights)
    product_ids = products["product_id"].to_numpy()
    product_lookup = products.set_index("product_id")
    rows: list[dict[str, object]] = []

    for order_index, line_count in enumerate(counts, start=1):
        selected_products = rng.choice(
            product_ids, size=int(line_count), replace=False, p=product_weights
        )
        for product_id in selected_products:
            product = product_lookup.loc[str(product_id)]
            category = product["category"]
            max_quantity = 6 if category == "Grocery" else 5 if category == "Office" else 3
            quantity = int(rng.integers(1, max_quantity + 1))
            discount = float(
                rng.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.30], p=[0.48, 0.15, 0.16, 0.10, 0.08, 0.03])
            )
            rows.append(
                {
                    "order_id": f"ORD{order_index:06d}",
                    "order_date": order_dates[order_index - 1].strftime("%Y-%m-%d"),
                    "customer_id": str(customer_ids[order_index - 1]),
                    "store_id": str(store_ids[order_index - 1]),
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "unit_price": float(product["unit_price"]),
                    "discount_pct": discount,
                }
            )
    return pd.DataFrame(rows)


def _make_inventory(
    rng: np.random.Generator,
    sales: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    month_ends = pd.date_range(start_date, end_date, freq="ME")
    store_ids = stores["store_id"].tolist()
    product_ids = products["product_id"].tolist()
    sales_work = sales.copy()
    sales_work["date"] = pd.to_datetime(sales_work["order_date"]).dt.to_period("M").dt.to_timestamp("M")
    demand = sales_work.groupby(["date", "store_id", "product_id"])["quantity"].sum()

    shape = (len(store_ids), len(product_ids))
    reorder = rng.integers(4, 15, size=shape)
    opening = rng.integers(0, 18, size=shape)
    rows: list[dict[str, object]] = []

    for month_end in month_ends:
        month_demand = np.zeros(shape, dtype=int)
        for store_index, store_id in enumerate(store_ids):
            for product_index, product_id in enumerate(product_ids):
                month_demand[store_index, product_index] = int(
                    demand.get((month_end, store_id, product_id), 0)
                )

        # A delayed replenishment when demand reaches available stock creates a
        # plausible zero closing balance without breaking the inventory equation.
        delayed = (
            (month_demand > 0)
            & (month_demand >= opening)
            & (rng.random(shape) < 0.22)
        )
        target_closing = reorder + rng.integers(1, 10, size=shape)
        normal_receipts = np.maximum(0, month_demand + target_closing - opening)
        delayed_receipts = np.maximum(0, month_demand - opening)
        units_received = np.where(delayed, delayed_receipts, normal_receipts)
        closing = opening + units_received - month_demand

        for store_index, store_id in enumerate(store_ids):
            for product_index, product_id in enumerate(product_ids):
                rows.append(
                    {
                        "date": month_end.strftime("%Y-%m-%d"),
                        "store_id": store_id,
                        "product_id": product_id,
                        "opening_stock": int(opening[store_index, product_index]),
                        "units_received": int(units_received[store_index, product_index]),
                        "units_sold": int(month_demand[store_index, product_index]),
                        "closing_stock": int(closing[store_index, product_index]),
                        "reorder_level": int(reorder[store_index, product_index]),
                    }
                )
        opening = closing
    return pd.DataFrame(rows)


def _make_returns(
    rng: np.random.Generator,
    sales: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    category_map = products.set_index("product_id")["category"]
    category_rate = {
        "Electronics": 0.060,
        "Grocery": 0.018,
        "Home": 0.040,
        "Personal Care": 0.030,
        "Clothing": 0.075,
        "Office": 0.025,
    }
    probabilities = sales["product_id"].map(category_map).map(category_rate).to_numpy()
    selected = sales.loc[rng.random(len(sales)) < probabilities].copy().reset_index(drop=True)
    reasons = ["Defective", "Wrong Item", "Customer Changed Mind", "Damaged", "Size Issue"]
    reason_probs = [0.24, 0.17, 0.25, 0.19, 0.15]
    rows = []
    for i, row in selected.iterrows():
        order_date = pd.Timestamp(row["order_date"])
        rows.append(
            {
                "return_id": f"RET{i + 1:06d}",
                "order_id": row["order_id"],
                "product_id": row["product_id"],
                "return_date": (order_date + pd.Timedelta(days=int(rng.integers(1, 31)))).strftime("%Y-%m-%d"),
                "quantity_returned": int(rng.integers(1, int(row["quantity"]) + 1)),
                "return_reason": str(rng.choice(reasons, p=reason_probs)),
            }
        )
    return pd.DataFrame(rows)


def _add_duplicates(
    frame: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if frame.empty or count <= 0:
        return frame
    duplicate_count = min(count, len(frame))
    duplicates = frame.iloc[rng.choice(len(frame), size=duplicate_count, replace=False)]
    return pd.concat([frame, duplicates], ignore_index=True)


def _sample_indices(
    rng: np.random.Generator,
    frame: pd.DataFrame,
    count: int,
) -> np.ndarray:
    return rng.choice(frame.index.to_numpy(), size=min(count, len(frame)), replace=False)


def _inject_quality_issues(
    rng: np.random.Generator,
    tables: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    """Add small, deterministic quality issues to otherwise valid tables."""
    dirty = {name: frame.copy() for name, frame in tables.items()}
    manifest: dict[str, object] = {"seed": SEED, "issues": {}}

    customers = dirty["customers"]
    customers.loc[_sample_indices(rng, customers, 10), "city"] = " toronto "
    province_indices = _sample_indices(rng, customers, 12)
    province_variants = np.resize(np.array(["ON", "ontario", " B.C. ", "QC"]), len(province_indices))
    customers.loc[province_indices, "province"] = province_variants
    customers.loc[_sample_indices(rng, customers, 6), "signup_date"] = "not-a-date"
    customers.loc[_sample_indices(rng, customers, 6), "customer_name"] = np.nan
    dirty["customers"] = _add_duplicates(customers, 8, rng)
    manifest["issues"]["customers"] = {
        "duplicate_rows": 8,
        "text_or_province_inconsistencies": 22,
        "invalid_dates": 6,
        "missing_names": 6,
    }

    products = dirty["products"]
    category_indices = _sample_indices(rng, products, 10)
    products.loc[category_indices, "category"] = products.loc[category_indices, "category"].str.lower() + " "
    products.loc[_sample_indices(rng, products, 6), "supplier"] = np.nan
    dirty["products"] = _add_duplicates(products, 5, rng)
    manifest["issues"]["products"] = {
        "duplicate_rows": 5,
        "category_capitalization_or_whitespace": 10,
        "missing_suppliers": 6,
    }

    stores = dirty["stores"]
    store_province_indices = _sample_indices(rng, stores, 3)
    store_variants = np.resize(np.array(["AB", "ontario", " QC "]), len(store_province_indices))
    stores.loc[store_province_indices, "province"] = store_variants
    stores.loc[_sample_indices(rng, stores, 2), "opening_date"] = "13/40/2020"
    dirty["stores"] = _add_duplicates(stores, 2, rng)
    manifest["issues"]["stores"] = {
        "duplicate_rows": 2,
        "province_inconsistencies": len(store_province_indices),
        "invalid_dates": 2,
    }

    sales = dirty["sales"]
    sales.loc[_sample_indices(rng, sales, 60), "quantity"] *= -1
    sales.loc[_sample_indices(rng, sales, 75), "customer_id"] = np.nan
    sales.loc[_sample_indices(rng, sales, 20), "customer_id"] = "CUST9999"
    sales.loc[_sample_indices(rng, sales, 40), "order_date"] = "invalid-date"
    sales.loc[_sample_indices(rng, sales, 50), "unit_price"] = np.nan
    sales.loc[_sample_indices(rng, sales, 30), "discount_pct"] = 1.5
    id_indices = _sample_indices(rng, sales, 40)
    sales.loc[id_indices, "product_id"] = " " + sales.loc[id_indices, "product_id"].astype(str) + " "
    dirty["sales"] = _add_duplicates(sales, 75, rng)
    manifest["issues"]["sales"] = {
        "duplicate_rows": 75,
        "negative_quantities": 60,
        "missing_customer_ids": 75,
        "invalid_customer_ids": 20,
        "invalid_dates": 40,
        "missing_prices": 50,
        "invalid_discounts": 30,
        "whitespace_in_ids": 40,
    }

    inventory = dirty["inventory"]
    inventory.loc[_sample_indices(rng, inventory, 25), "closing_stock"] = -5
    inventory.loc[_sample_indices(rng, inventory, 20), "date"] = "2025-99-99"
    inventory.loc[_sample_indices(rng, inventory, 20), "store_id"] = np.nan
    inventory_indices = _sample_indices(rng, inventory, 40)
    inventory.loc[inventory_indices, "product_id"] = (
        " " + inventory.loc[inventory_indices, "product_id"].astype(str).str.lower() + " "
    )
    dirty["inventory"] = _add_duplicates(inventory, 60, rng)
    manifest["issues"]["inventory"] = {
        "duplicate_rows": 60,
        "incorrect_negative_closing_stock": 25,
        "invalid_dates": 20,
        "missing_store_ids": 20,
        "inconsistent_product_ids": 40,
    }

    returns = dirty["returns"]
    if not returns.empty:
        sale_dates = tables["sales"].set_index(["order_id", "product_id"])["order_date"]
        early_indices = _sample_indices(rng, returns, 15)
        for idx in early_indices:
            key = (returns.at[idx, "order_id"], returns.at[idx, "product_id"])
            returns.at[idx, "return_date"] = (
                pd.Timestamp(sale_dates.loc[key]) - pd.Timedelta(days=int(rng.integers(1, 8)))
            ).strftime("%Y-%m-%d")
        returns.loc[_sample_indices(rng, returns, 15), "order_id"] = "ORD999999"
        returns.loc[_sample_indices(rng, returns, 10), "product_id"] = "PROD999"
        returns.loc[_sample_indices(rng, returns, 20), "return_reason"] = np.nan
        reason_indices = _sample_indices(rng, returns, 20)
        returns.loc[reason_indices, "return_reason"] = (
            " " + returns.loc[reason_indices, "return_reason"].astype(str).str.lower() + " "
        )
        dirty["returns"] = _add_duplicates(returns, 20, rng)
    manifest["issues"]["returns"] = {
        "duplicate_rows": min(20, len(returns)),
        "returns_before_sale": min(15, len(returns)),
        "invalid_order_ids": min(15, len(returns)),
        "invalid_product_ids": min(10, len(returns)),
        "missing_reasons": min(20, len(returns)),
        "reason_capitalization_or_whitespace": min(20, len(returns)),
    }
    return dirty, manifest


def generate_datasets(
    output_dir: Path | str,
    *,
    seed: int = SEED,
    n_customers: int = 2_000,
    n_products: int = 300,
    n_stores: int = 10,
    n_sales: int = 50_000,
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    inject_issues: bool = True,
) -> dict[str, pd.DataFrame]:
    """Generate all raw tables and write them to output_dir."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start >= end:
        raise ValueError("start_date must be before end_date")

    customers = _make_customers(rng, n_customers, start)
    products = _make_products(rng, n_products)
    stores = _make_stores(n_stores)
    sales = _make_sales(rng, customers, products, stores, n_sales, start, end)
    inventory = _make_inventory(rng, sales, products, stores, start, end)
    returns = _make_returns(rng, sales, products)

    tables = {
        "customers": customers,
        "products": products,
        "stores": stores,
        "sales": sales,
        "inventory": inventory,
        "returns": returns,
    }
    manifest: dict[str, object] = {"seed": seed, "issues": {}}
    if inject_issues:
        issue_rng = np.random.default_rng(seed + 1)
        tables, manifest = _inject_quality_issues(issue_rng, tables)
        manifest["seed"] = seed

    for name, frame in tables.items():
        frame.to_csv(output_path / f"{name}.csv", index=False)

    manifest["generated_rows"] = {name: len(frame) for name, frame in tables.items()}
    manifest["date_range"] = {"start": start_date, "end": end_date}
    (output_path / "quality_issues_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print("Synthetic retail data generated successfully.")
    for name, frame in tables.items():
        print(f"  {name:10s}: {len(frame):,} rows")
    print(f"  output     : {output_path.resolve()}")
    return tables


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "data" / "raw")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--no-issues", action="store_true", help="Generate clean source records.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_datasets(args.output_dir, seed=args.seed, inject_issues=not args.no_issues)

