"""Integration test: backfilling a new date must accumulate history, not
collide with whatever date an order was first loaded under.

Regression test for the bug reported via the dashboard: "only today's items
show up" even after `uv run python main.py --date <past-date>`. Root cause
was analytics.fact_orders' natural key being (order_id, order_item_id) only
-- since DummyJSON always returns the same cart/product IDs, every backfill
for a different date collided with the existing row and silently kept its
original order_date_key. The fix adds order_date_key to the unique
constraint / ON CONFLICT target, so different dates create separate rows
while re-running the *same* date stays idempotent.

Needs a reachable Postgres warehouse with the pipeline already run at least
once (``uv run python main.py``); skips itself otherwise so the rest of the
suite stays fast and DB-free.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from etl.load.db import get_engine
from etl.load.dimension_loader import date_key, upsert_dim_date
from etl.load.fact_loader import load_fact_orders


@pytest.fixture(scope="module")
def engine():
    eng = get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Postgres warehouse not reachable — run `docker compose up -d postgres`")
    return eng


def _distinct_order_dates(engine) -> set[date]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT DISTINCT dd.full_date "
                "FROM analytics.fact_orders f "
                "JOIN analytics.dim_date dd ON dd.date_key = f.order_date_key"
            )
        ).scalars().all()
    return set(rows)


def _count_fact_rows(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM analytics.fact_orders")).scalar()


def test_backfilling_a_new_date_accumulates_instead_of_colliding(engine):
    with engine.connect() as conn:
        raw_rows = conn.execute(text("SELECT COUNT(*) FROM raw.cart_items")).scalar()
    if not raw_rows:
        pytest.skip("raw.cart_items is empty — run `uv run python main.py` first")

    date_a, date_b = date(2020, 1, 1), date(2020, 6, 15)
    original_dates = _distinct_order_dates(engine)

    try:
        upsert_dim_date(engine, {date_a, date_b})

        n_before = _count_fact_rows(engine)
        inserted_a = load_fact_orders(engine, date_a)
        assert inserted_a > 0
        assert _count_fact_rows(engine) - n_before == inserted_a, (
            "loading a fresh date should add new rows, not overwrite existing ones"
        )
        assert _distinct_order_dates(engine) == original_dates | {date_a}, (
            "the original date's orders should still be there alongside the new one"
        )

        # Re-running the *same* date must stay idempotent: no row growth.
        n_after_a = _count_fact_rows(engine)
        load_fact_orders(engine, date_a)
        assert _count_fact_rows(engine) == n_after_a, (
            "re-running the same --date duplicated rows instead of updating them in place"
        )

        # A second, different date should accumulate too.
        inserted_b = load_fact_orders(engine, date_b)
        assert inserted_b > 0
        assert _distinct_order_dates(engine) == original_dates | {date_a, date_b}, (
            "backfilling a different date should coexist with prior dates, "
            "not collide with and overwrite them"
        )
    finally:
        with engine.begin() as conn:
            keys = [date_key(date_a), date_key(date_b)]
            conn.execute(
                text("DELETE FROM analytics.fact_orders WHERE order_date_key = ANY(:keys)"),
                {"keys": keys},
            )
            conn.execute(
                text("DELETE FROM analytics.dim_date WHERE date_key = ANY(:keys)"),
                {"keys": keys},
            )
