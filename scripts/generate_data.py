"""Generate reproducible synthetic pharmacy CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmacy_analytics import generate_dataset, write_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--sales", type=int, default=1200)
    parser.add_argument("--products", type=int, default=60)
    parser.add_argument("--out-dir", default=str(ROOT / "data" / "raw"))
    args = parser.parse_args()
    if args.sales < 1 or args.products < 1:
        parser.error("--sales and --products must be positive integers")

    dataset = generate_dataset(args.seed, args.sales, args.products)
    write_dataset(dataset, args.out_dir)
    for name, rows in dataset.items():
        print(f"{name}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
