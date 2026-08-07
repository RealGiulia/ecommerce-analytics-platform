"""S3-compatible client for the MinIO data lake (bronze = raw JSON landing,
silver = cleaned/typed Parquet).

Every object is partitioned by an ``ingestion_date`` so that re-running the
pipeline for a given day is idempotent and old snapshots stay queryable.
"""

from __future__ import annotations

import json
from datetime import date
from io import BytesIO

import boto3
import pandas as pd
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from etl.config import DataLakeConfig, lake_config
from etl.logging_setup import get_logger

logger = get_logger(__name__)


class DataLakeClient:
    """Wraps boto3's S3 client with bronze/silver read-write helpers."""

    def __init__(self, config: DataLakeConfig = lake_config) -> None:
        self._config = config
        self._s3 = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def ensure_buckets(self) -> None:
        for bucket in (self._config.bronze_bucket, self._config.silver_bucket):
            self._ensure_bucket(bucket)

    def _ensure_bucket(self, bucket: str) -> None:
        try:
            self._s3.head_bucket(Bucket=bucket)
        except ClientError:
            logger.info("Creating bucket %s", bucket)
            self._s3.create_bucket(Bucket=bucket)

    # -- Bronze: raw JSON, exactly as received from the source API ----------

    def write_bronze(self, entity: str, ingestion_date: date, records: list[dict]) -> str:
        key = self._bronze_key(entity, ingestion_date)
        body = json.dumps(records, default=str).encode("utf-8")
        self._s3.put_object(
            Bucket=self._config.bronze_bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        logger.info(
            "Wrote %d bronze records to s3://%s/%s", len(records), self._config.bronze_bucket, key
        )
        return key

    def read_bronze(self, entity: str, ingestion_date: date) -> list[dict]:
        key = self._bronze_key(entity, ingestion_date)
        response = self._s3.get_object(Bucket=self._config.bronze_bucket, Key=key)
        return json.loads(response["Body"].read())

    def _bronze_key(self, entity: str, ingestion_date: date) -> str:
        return f"{entity}/ingestion_date={ingestion_date.isoformat()}/{entity}.json"

    # -- Silver: cleaned, typed, flattened Parquet ---------------------------

    def write_silver(self, entity: str, ingestion_date: date, df: pd.DataFrame) -> str:
        key = self._silver_key(entity, ingestion_date)
        buffer = BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        self._s3.put_object(
            Bucket=self._config.silver_bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        logger.info("Wrote %d silver rows to s3://%s/%s", len(df), self._config.silver_bucket, key)
        return key

    def read_silver(self, entity: str, ingestion_date: date) -> pd.DataFrame:
        key = self._silver_key(entity, ingestion_date)
        response = self._s3.get_object(Bucket=self._config.silver_bucket, Key=key)
        return pd.read_parquet(BytesIO(response["Body"].read()), engine="pyarrow")

    def _silver_key(self, entity: str, ingestion_date: date) -> str:
        return f"{entity}/ingestion_date={ingestion_date.isoformat()}/{entity}.parquet"
