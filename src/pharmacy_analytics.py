"""Deterministic synthetic pharmacy sales data and KPI analysis."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

CATEGORIES = (
    "Dermocosmética",
    "Cuidado personal",
    "Bebés",
    "Medicamentos OTC",
    "Perfumería",
    "Suplementos",
)
BRANDS = ("NovaCare", "AndesLab", "BioPlus", "DermaVida", "SaludMix")
CHANNELS = ("Store", "Online", "Delivery")
REGIONS = ("Buenos Aires", "Córdoba", "Santa Fe", "Mendoza")


def generate_dataset(
    seed: int = 2026,
    sales_count: int = 1200,
    product_count: int = 60,
) -> dict[str, list[dict[str, Any]]]:
    """Return deterministic products, sales, and inventory records."""
    if sales_count < 1 or product_count < 1:
        raise ValueError("sales_count and product_count must be positive.")

    rng = random.Random(seed)
    products: list[dict[str, Any]] = []
    for index in range(1, product_count + 1):
        unit_price = round(rng.uniform(500, 18000), 2)
        unit_cost = round(unit_price * rng.uniform(0.42, 0.78), 2)
        products.append(
            {
                "product_id": f"P{index:04d}",
                "product_name": f"Producto {index:03d}",
                "category": rng.choice(CATEGORIES),
                "brand": rng.choice(BRANDS),
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "reorder_point": rng.randint(10, 35),
            }
        )

    sales: list[dict[str, Any]] = []
    start_date = date(2025, 1, 1)
    for index in range(1, sales_count + 1):
        product = rng.choice(products)
        sale_date = start_date + timedelta(days=rng.randrange(365))
        quantity = rng.randint(1, 5)
        sales.append(
            {
                "transaction_id": f"TX{index:06d}",
                "sale_date": sale_date.isoformat(),
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": product["unit_price"],
                "unit_cost": product["unit_cost"],
                "discount_pct": rng.choice((0.0, 0.0, 0.05, 0.10, 0.15)),
                "channel": rng.choice(CHANNELS),
                "region": rng.choice(REGIONS),
            }
        )

    inventory = [
        {
            "snapshot_date": "2025-12-31",
            "product_id": product["product_id"],
            "stock_on_hand": rng.randint(0, 120),
        }
        for product in products
    ]
    return {"products": products, "sales": sales, "inventory": inventory}


def write_dataset(dataset: dict[str, list[dict[str, Any]]], out_dir: str | Path) -> None:
    """Write dataset tables as UTF-8 CSV files."""
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in dataset.items():
        if not rows:
            raise ValueError(f"Cannot write an empty table: {name}")
        path = output / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def read_dataset(input_dir: str | Path) -> dict[str, list[dict[str, str]]]:
    """Read the three expected CSV files from a directory."""
    folder = Path(input_dir)
    dataset: dict[str, list[dict[str, str]]] = {}
    for name in ("products", "sales", "inventory"):
        path = folder / f"{name}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Required input file is missing: {path}")
        with path.open(newline="", encoding="utf-8-sig") as stream:
            dataset[name] = list(csv.DictReader(stream))
    return dataset


def validate_dataset(dataset: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Return data-quality findings without mutating source rows."""
    errors: list[str] = []
    products = dataset.get("products", [])
    sales = dataset.get("sales", [])
    inventory = dataset.get("inventory", [])

    product_ids = [str(row.get("product_id", "")).strip() for row in products]
    if not products:
        errors.append("products table is empty")
    if any(not value for value in product_ids):
        errors.append("products contains a blank product_id")
    if len(product_ids) != len(set(product_ids)):
        errors.append("products contains duplicate product_id values")
    known_products = set(product_ids)

    transaction_ids = [str(row.get("transaction_id", "")).strip() for row in sales]
    if not sales:
        errors.append("sales table is empty")
    if any(not value for value in transaction_ids):
        errors.append("sales contains a blank transaction_id")
    if len(transaction_ids) != len(set(transaction_ids)):
        errors.append("sales contains duplicate transaction_id values")

    for row in products:
        product_id = row.get("product_id", "")
        try:
            price = float(row["unit_price"])
            cost = float(row["unit_cost"])
            reorder = int(row["reorder_point"])
            if price <= 0 or cost < 0 or cost > price:
                errors.append(f"products {product_id}: invalid price/cost")
            if reorder < 0:
                errors.append(f"products {product_id}: negative reorder point")
        except (KeyError, TypeError, ValueError):
            errors.append(f"products {product_id}: non-numeric price/cost/reorder point")

    for row in sales:
        transaction_id = row.get("transaction_id", "")
        if str(row.get("product_id", "")) not in known_products:
            errors.append(f"sales {transaction_id}: unknown product_id")
        try:
            quantity = int(row["quantity"])
            price = float(row["unit_price"])
            cost = float(row["unit_cost"])
            discount = float(row["discount_pct"])
            date.fromisoformat(str(row["sale_date"]))
            if quantity <= 0 or price <= 0 or cost < 0 or cost > price:
                errors.append(f"sales {transaction_id}: invalid quantity or price/cost")
            if not 0 <= discount < 1:
                errors.append(f"sales {transaction_id}: discount_pct must be in [0, 1)")
        except (KeyError, TypeError, ValueError):
            errors.append(f"sales {transaction_id}: invalid date or numeric field")

    inventory_ids = [str(row.get("product_id", "")) for row in inventory]
    if len(inventory_ids) != len(set(inventory_ids)):
        errors.append("inventory contains duplicate product_id values")
    for row in inventory:
        product_id = str(row.get("product_id", ""))
        if product_id not in known_products:
            errors.append(f"inventory {product_id}: unknown product_id")
        try:
            stock = int(row["stock_on_hand"])
            date.fromisoformat(str(row["snapshot_date"]))
            if stock < 0:
                errors.append(f"inventory {product_id}: negative stock")
        except (KeyError, TypeError, ValueError):
            errors.append(f"inventory {product_id}: invalid snapshot date or stock")

    return errors


def analyze_dataset(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Calculate sales KPIs, grouped summaries, and stock replenishment alerts."""
    errors = validate_dataset(dataset)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors[:10]))

    products = {str(row["product_id"]): row for row in dataset["products"]}
    monthly: dict[str, dict[str, float]] = defaultdict(
        lambda: {"transactions": 0, "units": 0, "net_sales": 0.0, "gross_profit": 0.0}
    )
    by_category: dict[str, dict[str, float]] = defaultdict(
        lambda: {"transactions": 0, "units": 0, "net_sales": 0.0, "gross_profit": 0.0}
    )
    by_channel: dict[str, dict[str, float]] = defaultdict(
        lambda: {"transactions": 0, "units": 0, "net_sales": 0.0, "gross_profit": 0.0}
    )

    totals = {
        "transactions": 0,
        "units_sold": 0,
        "gross_sales": 0.0,
        "discount_amount": 0.0,
        "net_sales": 0.0,
        "cogs": 0.0,
        "gross_profit": 0.0,
    }

    for sale in dataset["sales"]:
        product = products[str(sale["product_id"])]
        quantity = int(sale["quantity"])
        gross = quantity * float(sale["unit_price"])
        discount = gross * float(sale["discount_pct"])
        net = gross - discount
        cogs = quantity * float(sale["unit_cost"])
        profit = net - cogs
        month = str(sale["sale_date"])[:7]
        category = str(product["category"])
        channel = str(sale["channel"])

        totals["transactions"] += 1
        totals["units_sold"] += quantity
        totals["gross_sales"] += gross
        totals["discount_amount"] += discount
        totals["net_sales"] += net
        totals["cogs"] += cogs
        totals["gross_profit"] += profit

        for group in (monthly[month], by_category[category], by_channel[channel]):
            group["transactions"] += 1
            group["units"] += quantity
            group["net_sales"] += net
            group["gross_profit"] += profit

    totals["gross_margin_pct"] = (
        totals["gross_profit"] / totals["net_sales"] * 100 if totals["net_sales"] else 0.0
    )
    inventory = {str(row["product_id"]): row for row in dataset["inventory"]}
    stock_alerts = []
    for product_id, row in inventory.items():
        product = products[product_id]
        stock = int(row["stock_on_hand"])
        reorder = int(product["reorder_point"])
        if stock <= reorder:
            stock_alerts.append(
                {
                    "product_id": product_id,
                    "product_name": product["product_name"],
                    "category": product["category"],
                    "stock_on_hand": stock,
                    "reorder_point": reorder,
                }
            )

    def normalize(groups: dict[str, dict[str, float]], key_name: str) -> list[dict[str, Any]]:
        rows = []
        for key, values in sorted(groups.items()):
            rows.append(
                {
                    key_name: key,
                    "transactions": int(values["transactions"]),
                    "units": int(values["units"]),
                    "net_sales": round(values["net_sales"], 2),
                    "gross_profit": round(values["gross_profit"], 2),
                }
            )
        return rows

    rounded_totals = {
        key: round(value, 2) if isinstance(value, float) else value
        for key, value in totals.items()
    }
    return {
        "status": "PASS",
        "row_counts": {name: len(rows) for name, rows in dataset.items()},
        "totals": rounded_totals,
        "monthly_sales": normalize(monthly, "month"),
        "category_sales": normalize(by_category, "category"),
        "channel_sales": normalize(by_channel, "channel"),
        "stock_alerts": sorted(
            stock_alerts, key=lambda row: (row["stock_on_hand"], row["product_id"])
        ),
    }


def write_analysis(report: dict[str, Any], out_dir: str | Path) -> None:
    """Write KPI summaries and a readable Markdown report."""
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "kpi_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_csv(output / "monthly_sales.csv", report["monthly_sales"])
    _write_csv(output / "category_sales.csv", report["category_sales"])
    _write_csv(output / "channel_sales.csv", report["channel_sales"])
    _write_csv(output / "stock_alerts.csv", report["stock_alerts"])
    totals = report["totals"]
    lines = [
        "# Pharmacy Sales Analytics Report",
        "",
        "All values are generated from synthetic data and do not describe a real pharmacy.",
        "",
        "## Executive KPIs",
        "",
        f"- Transactions: **{totals['transactions']}**",
        f"- Units sold: **{totals['units_sold']}**",
        f"- Gross sales: **{totals['gross_sales']:.2f}**",
        f"- Discounts: **{totals['discount_amount']:.2f}**",
        f"- Net sales: **{totals['net_sales']:.2f}**",
        f"- Cost of goods sold: **{totals['cogs']:.2f}**",
        f"- Gross profit: **{totals['gross_profit']:.2f}**",
        f"- Gross margin: **{totals['gross_margin_pct']:.2f}%**",
        f"- Products at or below reorder point: **{len(report['stock_alerts'])}**",
        "",
        "## Interpretation",
        "",
        "Use monthly and category summaries to explore synthetic sales patterns. Stock alerts are simple threshold signals, not demand forecasts or purchase recommendations.",
        "",
        "## Generated files",
        "",
        "- kpi_report.json",
        "- monthly_sales.csv",
        "- category_sales.csv",
        "- channel_sales.csv",
        "- stock_alerts.csv",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
