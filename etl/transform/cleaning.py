"""Shared helpers for bronze -> silver transformations."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from etl.logging_setup import get_logger

logger = get_logger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def dedupe_by_id(df: pd.DataFrame, id_column: str) -> pd.DataFrame:
    """Drop duplicate business keys, keeping the last occurrence.

    DummyJSON serves a full snapshot on every call, so duplicates should
    never happen in practice; this guards the load layer's unique
    constraints against a flaky or partially-retried extraction anyway.
    """
    before = len(df)
    df = df.drop_duplicates(subset=[id_column], keep="last").reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d duplicate rows on %s", dropped, id_column)
    return df
