"""Pipeline run tracking against ``audit.pipeline_runs``.

Wrapping a pipeline stage in :func:`track_pipeline_run` guarantees a row is
recorded for every attempt -- success or failure -- so run history and
row-count trends can be queried straight from the warehouse.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine

from etl.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineRunStats:
    extracted_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    rejected_rows: int = 0


_START_SQL = text(
    "INSERT INTO audit.pipeline_runs (pipeline_name, source_name, status) "
    "VALUES (:pipeline_name, :source_name, 'running') "
    "RETURNING pipeline_run_id"
)

_FINISH_SQL = text(
    "UPDATE audit.pipeline_runs SET "
    "status = :status, finished_at = now(), "
    "extracted_rows = :extracted_rows, inserted_rows = :inserted_rows, "
    "updated_rows = :updated_rows, rejected_rows = :rejected_rows, "
    "error_message = :error_message "
    "WHERE pipeline_run_id = :run_id"
)


@contextmanager
def track_pipeline_run(
    engine: Engine, pipeline_name: str, source_name: str | None = None
) -> Iterator[PipelineRunStats]:
    stats = PipelineRunStats()

    with engine.begin() as conn:
        run_id = conn.execute(
            _START_SQL, {"pipeline_name": pipeline_name, "source_name": source_name}
        ).scalar_one()

    try:
        yield stats
    except Exception as exc:
        logger.exception("Pipeline '%s' failed", pipeline_name)
        _finish(engine, run_id, "failed", stats, error_message=str(exc))
        raise
    else:
        logger.info(
            "Pipeline '%s' finished: extracted=%d inserted=%d updated=%d rejected=%d",
            pipeline_name,
            stats.extracted_rows,
            stats.inserted_rows,
            stats.updated_rows,
            stats.rejected_rows,
        )
        _finish(engine, run_id, "success", stats)


def _finish(
    engine: Engine,
    run_id: int,
    status: str,
    stats: PipelineRunStats,
    error_message: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            _FINISH_SQL,
            {
                "status": status,
                "extracted_rows": stats.extracted_rows,
                "inserted_rows": stats.inserted_rows,
                "updated_rows": stats.updated_rows,
                "rejected_rows": stats.rejected_rows,
                "error_message": error_message,
                "run_id": run_id,
            },
        )
