"""Execute every SQL analysis statement as a lightweight syntax/runtime check."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer = ""
    for line in sql_text.splitlines():
        buffer += line + "\n"
        if sqlite3.complete_statement(buffer):
            if buffer.strip():
                statements.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        raise ValueError("SQL file ends with an incomplete statement")
    return statements


def run_sql_files(database_path: Path | str, sql_dir: Path | str) -> dict[str, int]:
    db_path = Path(database_path)
    sql_path = Path(sql_dir)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    sql_files = sorted(sql_path.glob("[0-9][0-9]_*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"No numbered SQL files found in {sql_path}")

    results: dict[str, int] = {}
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for sql_file in sql_files:
            statements = split_sql_statements(sql_file.read_text(encoding="utf-8"))
            executed = 0
            for statement_number, statement in enumerate(statements, start=1):
                try:
                    cursor = connection.execute(statement)
                    if cursor.description:
                        cursor.fetchmany(3)
                    executed += 1
                except sqlite3.Error as exc:
                    raise RuntimeError(
                        f"{sql_file.name}, statement {statement_number} failed: {exc}"
                    ) from exc
            results[sql_file.name] = executed
            print(f"  {sql_file.name}: {executed} statements passed")
    print(f"Executed {sum(results.values())} SQL statements across {len(results)} files.")
    return results


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=project_root / "database" / "retail_analytics.db")
    parser.add_argument("--sql-dir", type=Path, default=project_root / "sql")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_sql_files(args.database, args.sql_dir)

