from __future__ import annotations

import json

import pandas as pd


def test_dataset_generation_creates_all_expected_files(sample_project):
    expected = {"customers", "products", "stores", "sales", "inventory", "returns"}
    actual = {path.stem for path in sample_project["raw"].glob("*.csv")}
    assert actual == expected
    assert len(pd.read_csv(sample_project["raw"] / "sales.csv")) >= 1_200
    manifest = json.loads((sample_project["raw"] / "quality_issues_manifest.json").read_text())
    assert manifest["seed"] == 123
    assert manifest["issues"]["sales"]["duplicate_rows"] > 0

