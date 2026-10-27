"""Validate pharmacy CSV data and generate KPI outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmacy_analytics import (  # noqa: E402
    analyze_dataset,
    read_dataset,
    validate_dataset,
    write_analysis,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(ROOT / "data" / "raw"))
    parser.add_argument("--out-dir", default=str(ROOT / "outputs"))
    args = parser.parse_args()

    try:
        dataset = read_dataset(args.input_dir)
        errors = validate_dataset(dataset)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

        report = analyze_dataset(dataset)
        write_analysis(report, args.out_dir)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    totals = report["totals"]
    print(
        f"PASS: {totals['transactions']} transactions; "
        f"net sales {totals['net_sales']:.2f}; "
        f"gross profit {totals['gross_profit']:.2f}"
    )
    print(f"Reports written to {Path(args.out_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
