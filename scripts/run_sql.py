"""Execute the named SQL analytics queries against a temporary SQLite database."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmacy_analytics import read_dataset, validate_dataset  # noqa: E402

QUERY_PATTERN = re.compile(
    r"^-- QUERY: ([a-zA-Z0-9_]+)\s*\n(.*?)(?=^-- QUERY: |\Z)",
    re.MULTILINE | re.DOTALL,
)


def load_database(input_dir: str | Path) -> sqlite3.Connection:
    dataset = read_dataset(input_dir)
    errors = validate_dataset(dataset)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors[:10]))

    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            reorder_point INTEGER NOT NULL
        );
        CREATE TABLE sales (
            transaction_id TEXT PRIMARY KEY,
            sale_date TEXT NOT NULL,
            product_id TEXT NOT NULL REFERENCES products(product_id),
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            discount_pct REAL NOT NULL,
            channel TEXT NOT NULL,
            region TEXT NOT NULL
        );
        CREATE TABLE inventory (
            snapshot_date TEXT NOT NULL,
            product_id TEXT PRIMARY KEY REFERENCES products(product_id),
            stock_on_hand INTEGER NOT NULL
        );
        """
    )

    for name, rows in dataset.items():
        columns = list(rows[0])
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(f'"{column}"' for column in columns)
        connection.executemany(
            f"INSERT INTO {name} ({column_sql}) VALUES ({placeholders})",
            [[row[column] for column in columns] for row in rows],
        )
    return connection


def parse_queries(path: str | Path) -> list[tuple[str, str]]:
    content = Path(path).read_text(encoding="utf-8")
    queries = [
        (match.group(1), match.group(2).strip().rstrip(";"))
        for match in QUERY_PATTERN.finditer(content)
    ]
    if not queries:
        raise ValueError(f"No named SQL queries found in {path}")
    names = [name for name, _ in queries]
    if len(names) != len(set(names)):
        raise ValueError("SQL query names must be unique.")
    return queries


def run_queries(
    input_dir: str | Path,
    query_file: str | Path,
    out_dir: str | Path,
) -> dict[str, int]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    connection = load_database(input_dir)
    counts: dict[str, int] = {}
    try:
        for name, sql in parse_queries(query_file):
            cursor = connection.execute(sql)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description or []]
            with (output / f"{name}.csv").open(
                "w", newline="", encoding="utf-8"
            ) as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                writer.writerows(rows)
            counts[name] = len(rows)
    finally:
        connection.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(ROOT / "data" / "raw"))
    parser.add_argument("--query-file", default=str(ROOT / "sql" / "analysis.sql"))
    parser.add_argument("--out-dir", default=str(ROOT / "outputs" / "sql"))
    args = parser.parse_args()
    try:
        counts = run_queries(args.input_dir, args.query_file, args.out_dir)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for name, count in counts.items():
        print(f"{name}: {count} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
