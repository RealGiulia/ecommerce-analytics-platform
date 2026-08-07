"""Builds and upserts ``analytics.fact_orders`` from the raw cart layer.

Each cart line item (one product within one cart) becomes a fact row.
DummyJSON carts carry no order timestamp, so the pipeline's own ingestion
date stands in for ``order_date`` -- a deliberate, documented stand-in
rather than a fabricated business date. Likewise there is no order status
on the source, so every row is recorded as ``completed``.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine

from etl.load.dimension_loader import date_key
from etl.logging_setup import get_logger

logger = get_logger(__name__)

_UPSERT_FACT_SQL = text(
    """
    INSERT INTO analytics.fact_orders (
        order_id, order_item_id, customer_key, product_key, order_date_key,
        quantity, unit_price, discount_amount, gross_amount, net_amount,
        order_status, source_system
    )
    SELECT
        ci.cart_id::text,
        ci.product_id::text,
        dc.customer_key,
        dp.product_key,
        :order_date_key,
        ci.quantity,
        ci.price,
        (ci.total - ci.discounted_total),
        ci.total,
        ci.discounted_total,
        'completed',
        'dummyjson_api'
    FROM raw.cart_items ci
    JOIN raw.carts c ON c.cart_id = ci.cart_id
    JOIN analytics.dim_customer dc
        ON dc.customer_id = c.user_id::text AND dc.is_current = TRUE
    JOIN analytics.dim_product dp
        ON dp.product_id = ci.product_id::text
    ON CONFLICT (order_id, order_item_id) DO UPDATE SET
        quantity = EXCLUDED.quantity,
        unit_price = EXCLUDED.unit_price,
        discount_amount = EXCLUDED.discount_amount,
        gross_amount = EXCLUDED.gross_amount,
        net_amount = EXCLUDED.net_amount,
        order_status = EXCLUDED.order_status,
        loaded_at = now()
    """
)


def load_fact_orders(engine: Engine, order_date: date) -> int:
    with engine.begin() as conn:
        result = conn.execute(_UPSERT_FACT_SQL, {"order_date_key": date_key(order_date)})

    logger.info("Upserted fact_orders (%d row(s) affected)", result.rowcount)
    return result.rowcount
