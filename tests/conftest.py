"""Shared small-data fixture for fast, readable tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from python.clean_data import clean_data
from python.generate_data import generate_datasets


@pytest.fixture(scope="session")
def sample_project(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("retail_sample")
    raw_dir = root / "raw"
    cleaned_dir = root / "cleaned"
    generate_datasets(
        raw_dir,
        seed=123,
        n_customers=120,
        n_products=36,
        n_stores=3,
        n_sales=1_200,
        start_date="2024-01-01",
        end_date="2024-03-31",
        inject_issues=True,
    )
    clean_data(raw_dir, cleaned_dir)
    return {"root": root, "raw": raw_dir, "cleaned": cleaned_dir}

