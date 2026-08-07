"""Builds and upserts the star schema's dimension tables from ``raw``.

dim_product is a type-1 (overwrite-in-place) dimension: DummyJSON has no
notion of product history, so only the latest attributes matter.

dim_customer is type-2 (versioned): when a tracked attribute changes, the
current row is closed (``is_current = FALSE``, ``valid_to`` stamped) and a
fresh row is inserted, preserving history of where a customer used to live.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine

from etl.logging_setup import get_logger

logger = get_logger(__name__)

# Buckets customers into a light-weight segment for slicing revenue by
# age group; DummyJSON has no real loyalty/spend tier to draw from.
_SEGMENT_EXPR = """
    CASE
        WHEN u.age IS NULL THEN 'Unknown'
        WHEN u.age < 25 THEN 'Gen Z (<25)'
        WHEN u.age < 40 THEN 'Millennial (25-39)'
        WHEN u.age < 55 THEN 'Gen X (40-54)'
        ELSE 'Boomer+ (55+)'
    END
"""


def date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def upsert_dim_date(engine: Engine, dates: set[date]) -> int:
    if not dates:
        return 0

    rows = [
        {
            "date_key": date_key(d),
            "full_date": d,
            "day_number": d.day,
            "day_name": d.strftime("%A"),
            "week_number": int(d.strftime("%W")),
            "month_number": d.month,
            "month_name": d.strftime("%B"),
            "quarter_number": (d.month - 1) // 3 + 1,
            "year_number": d.year,
            "is_weekend": d.weekday() >= 5,
        }
        for d in sorted(dates)
    ]

    insert_sql = text(
        """
        INSERT INTO analytics.dim_date (
            date_key, full_date, day_number, day_name, week_number,
            month_number, month_name, quarter_number, year_number, is_weekend
        ) VALUES (
            :date_key, :full_date, :day_number, :day_name, :week_number,
            :month_number, :month_name, :quarter_number, :year_number, :is_weekend
        )
        ON CONFLICT (date_key) DO NOTHING
        """
    )
    with engine.begin() as conn:
        conn.execute(insert_sql, rows)

    logger.info("Upserted %d dim_date row(s)", len(rows))
    return len(rows)


def upsert_dim_product(engine: Engine) -> int:
    sql = text(
        """
        INSERT INTO analytics.dim_product (product_id, product_name, category, subcategory, brand)
        SELECT product_id::text, title, category, NULL, brand
        FROM raw.products
        ON CONFLICT (product_id) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category = EXCLUDED.category,
            brand = EXCLUDED.brand
        """
    )
    with engine.begin() as conn:
        result = conn.execute(sql)

    logger.info("Upserted dim_product (%d row(s) affected)", result.rowcount)
    return result.rowcount


_CLOSE_CHANGED_SQL = text(
    f"""
    UPDATE analytics.dim_customer d
    SET valid_to = now(), is_current = FALSE
    FROM raw.users u
    WHERE d.customer_id = u.user_id::text
      AND d.is_current = TRUE
      AND (
           COALESCE(d.customer_name, '') <> COALESCE(u.first_name || ' ' || u.last_name, '')
        OR COALESCE(d.email, '') <> COALESCE(u.email, '')
        OR COALESCE(d.city, '') <> COALESCE(u.city, '')
        OR COALESCE(d.state, '') <> COALESCE(u.state, '')
        OR COALESCE(d.country, '') <> COALESCE(u.country, '')
        OR COALESCE(d.customer_segment, '') <> COALESCE({_SEGMENT_EXPR}, '')
      )
    """
)

_INSERT_NEW_VERSIONS_SQL = text(
    f"""
    INSERT INTO analytics.dim_customer (
        customer_id, customer_name, email, city, state, country, customer_segment
    )
    SELECT
        u.user_id::text,
        u.first_name || ' ' || u.last_name,
        u.email,
        u.city,
        u.state,
        u.country,
        {_SEGMENT_EXPR}
    FROM raw.users u
    WHERE NOT EXISTS (
        SELECT 1 FROM analytics.dim_customer d
        WHERE d.customer_id = u.user_id::text AND d.is_current = TRUE
    )
    """
)


def upsert_dim_customer(engine: Engine) -> tuple[int, int]:
    with engine.begin() as conn:
        closed = conn.execute(_CLOSE_CHANGED_SQL).rowcount
        inserted = conn.execute(_INSERT_NEW_VERSIONS_SQL).rowcount

    logger.info("dim_customer SCD2: closed %d row(s), inserted %d new version(s)", closed, inserted)
    return closed, inserted
