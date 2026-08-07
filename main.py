"""CLI entrypoint for the e-commerce ETL pipeline.

Usage:
    python main.py                  # run the full pipeline for today
    python main.py --date 2026-08-01  # backfill a specific ingestion date
"""

from __future__ import annotations

import argparse
from datetime import date, datetime

from etl.pipeline import run_full_pipeline


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DummyJSON e-commerce ETL pipeline")
    parser.add_argument(
        "--date",
        type=_parse_date,
        default=None,
        help="Ingestion date to run/backfill, format YYYY-MM-DD (defaults to today, UTC)",
    )
    args = parser.parse_args()

    run_full_pipeline(ingestion_date=args.date)


if __name__ == "__main__":
    main()
