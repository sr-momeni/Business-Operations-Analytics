from __future__ import annotations

import sqlite3

from database.create_database import create_database


def test_database_creation(sample_project):
    database_path = sample_project["root"] / "test_retail.db"
    counts = create_database(sample_project["cleaned"], database_path)
    assert database_path.exists()
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"customers", "products", "stores", "sales", "inventory", "returns"}.issubset(tables)
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == counts["sales"]

