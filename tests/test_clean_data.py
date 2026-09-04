from __future__ import annotations

import numpy as np
import pandas as pd

from python.validate_data import validate_data


def test_data_cleaning_creates_valid_output(sample_project):
    counts = validate_data(sample_project["cleaned"])
    assert counts["sales"] > 0
    assert counts["customers"] > 0


def test_calculated_revenue(sample_project):
    sales = pd.read_csv(sample_project["cleaned"] / "sales.csv")
    expected_gross = (sales["quantity"] * sales["unit_price"]).round(2)
    expected_net = (expected_gross * (1 - sales["discount_pct"])).round(2)
    assert np.allclose(sales["gross_revenue"], expected_gross, atol=0.01)
    assert np.allclose(sales["net_revenue"], expected_net, atol=0.01)


def test_calculated_profit(sample_project):
    sales = pd.read_csv(sample_project["cleaned"] / "sales.csv")
    expected_cost = (sales["quantity"] * sales["unit_cost"]).round(2)
    expected_profit = (sales["net_revenue"] - expected_cost).round(2)
    assert np.allclose(sales["cost"], expected_cost, atol=0.01)
    assert np.allclose(sales["profit"], expected_profit, atol=0.01)


def test_duplicate_removal(sample_project):
    raw_sales = pd.read_csv(sample_project["raw"] / "sales.csv")
    cleaned_sales = pd.read_csv(sample_project["cleaned"] / "sales.csv")
    assert raw_sales.duplicated().any()
    assert not cleaned_sales.duplicated().any()
    assert not cleaned_sales.duplicated(["order_id", "product_id"]).any()


def test_invalid_ids_are_removed_or_mapped(sample_project):
    sales = pd.read_csv(sample_project["cleaned"] / "sales.csv")
    customers = set(pd.read_csv(sample_project["cleaned"] / "customers.csv")["customer_id"])
    products = set(pd.read_csv(sample_project["cleaned"] / "products.csv")["product_id"])
    stores = set(pd.read_csv(sample_project["cleaned"] / "stores.csv")["store_id"])
    assert set(sales["customer_id"]).issubset(customers)
    assert set(sales["product_id"]).issubset(products)
    assert set(sales["store_id"]).issubset(stores)
    assert "CUST9999" not in set(sales["customer_id"])
    assert "CUST_UNKNOWN" in customers

