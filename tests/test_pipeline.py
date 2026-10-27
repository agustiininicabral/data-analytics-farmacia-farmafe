from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from pharmacy_analytics import (  # noqa: E402
    analyze_dataset,
    generate_dataset,
    read_dataset,
    validate_dataset,
    write_analysis,
    write_dataset,
)
from run_sql import run_queries  # noqa: E402


class PharmacyAnalyticsTests(unittest.TestCase):
    def test_generator_is_deterministic(self) -> None:
        self.assertEqual(
            generate_dataset(seed=11, sales_count=25, product_count=8),
            generate_dataset(seed=11, sales_count=25, product_count=8),
        )

    def test_generator_rejects_non_positive_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            generate_dataset(sales_count=0)
        with self.assertRaises(ValueError):
            generate_dataset(product_count=0)

    def test_validation_and_kpi_totals_reconcile(self) -> None:
        dataset = generate_dataset(seed=7, sales_count=100, product_count=12)
        self.assertEqual(validate_dataset(dataset), [])
        report = analyze_dataset(dataset)
        totals = report["totals"]
        self.assertEqual(totals["transactions"], 100)
        self.assertEqual(totals["transactions"], sum(row["transactions"] for row in report["monthly_sales"]))
        self.assertAlmostEqual(
            totals["gross_sales"] - totals["discount_amount"],
            totals["net_sales"],
            places=2,
        )
        self.assertAlmostEqual(
            totals["net_sales"] - totals["cogs"],
            totals["gross_profit"],
            places=2,
        )
        self.assertEqual(len(report["category_sales"]), len({p["category"] for p in dataset["products"]}))

    def test_validation_rejects_unknown_products_and_invalid_discounts(self) -> None:
        dataset = generate_dataset(seed=5, sales_count=4, product_count=3)
        dataset["sales"][0]["product_id"] = "P9999"
        dataset["sales"][1]["discount_pct"] = 1.0
        errors = validate_dataset(dataset)
        self.assertTrue(any("unknown product_id" in error for error in errors))
        self.assertTrue(any("discount_pct" in error for error in errors))
        with self.assertRaises(ValueError):
            analyze_dataset(dataset)

    def test_csv_round_trip_and_analysis_outputs(self) -> None:
        dataset = generate_dataset(seed=21, sales_count=40, product_count=10)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            out_dir = root / "outputs"
            write_dataset(dataset, data_dir)
            loaded = read_dataset(data_dir)
            report = analyze_dataset(loaded)
            write_analysis(report, out_dir)

            self.assertTrue((out_dir / "kpi_report.json").is_file())
            self.assertTrue((out_dir / "REPORT.md").is_file())
            self.assertTrue((out_dir / "monthly_sales.csv").is_file())
            self.assertTrue((out_dir / "stock_alerts.csv").is_file())
            self.assertEqual(report["totals"]["transactions"], 40)

    def test_named_sql_queries_execute_and_export_results(self) -> None:
        dataset = generate_dataset(seed=22, sales_count=75, product_count=15)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            out_dir = root / "sql"
            write_dataset(dataset, data_dir)
            counts = run_queries(data_dir, ROOT / "sql" / "analysis.sql", out_dir)

            self.assertEqual(
                set(counts),
                {"monthly_sales", "category_sales", "channel_sales", "stock_alerts"},
            )
            self.assertGreater(counts["monthly_sales"], 0)
            self.assertEqual(counts["category_sales"], len({p["category"] for p in dataset["products"]}))
            for name in counts:
                self.assertTrue((out_dir / f"{name}.csv").is_file())


if __name__ == "__main__":
    unittest.main()
