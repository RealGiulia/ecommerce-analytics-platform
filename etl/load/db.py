"""SQLAlchemy engine factory for the analytical warehouse."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from etl.config import DataWarehouseConfig, warehouse_config

_engine: Engine | None = None


def get_engine(config: DataWarehouseConfig = warehouse_config) -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(config.url, pool_pre_ping=True)
    return _engine
