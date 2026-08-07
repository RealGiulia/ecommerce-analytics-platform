"""Loads silver-layer DataFrames into the ``raw`` Postgres schema.

DummyJSON exposes full snapshots with no incremental/updated-since
capability, so every run truncates and reloads: the raw layer always
mirrors the latest pull rather than accumulating history (history lives in
MinIO's date-partitioned bronze/silver objects, and in dim_customer's SCD2
versions downstream).
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from etl.logging_setup import get_logger

logger = get_logger(__name__)


def load_raw_table(engine: Engine, df: pd.DataFrame, table: str, schema: str = "raw") -> int:
    if df.empty:
        logger.warning("Skipping load of %s.%s: empty dataframe", schema, table)
        return 0

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {schema}.{table}"))
        df.to_sql(
            table,
            con=conn,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )

    logger.info("Loaded %d rows into %s.%s", len(df), schema, table)
    return len(df)
