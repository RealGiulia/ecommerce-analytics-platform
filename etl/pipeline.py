"""Orchestrates the full extract -> bronze -> silver -> load flow.

Each stage is intentionally decoupled through storage rather than passed
in-memory: extraction lands raw JSON in the bronze bucket, transformation
reads bronze back and writes cleaned Parquet to the silver bucket, and
loading reads silver back into Postgres. That mirrors how a real data lake
pipeline is operated (and lets any stage be re-run independently against
what an earlier stage already produced for the same ingestion date).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from etl.extract import extract_carts, extract_products, extract_users
from etl.load import (
    get_engine,
    load_fact_orders,
    load_raw_table,
    track_pipeline_run,
    upsert_dim_customer,
    upsert_dim_date,
    upsert_dim_product,
)
from etl.logging_setup import get_logger
from etl.storage import DataLakeClient
from etl.transform import transform_carts, transform_products, transform_users

logger = get_logger(__name__)

PIPELINE_NAME = "ecommerce_medallion_pipeline"


def run_extract_to_bronze(lake: DataLakeClient, ingestion_date: date) -> dict[str, int]:
    counts = {}

    products = extract_products()
    lake.write_bronze("products", ingestion_date, products)
    counts["products"] = len(products)

    users = extract_users()
    lake.write_bronze("users", ingestion_date, users)
    counts["users"] = len(users)

    carts = extract_carts()
    lake.write_bronze("carts", ingestion_date, carts)
    counts["carts"] = len(carts)

    return counts


def run_bronze_to_silver(lake: DataLakeClient, ingestion_date: date) -> dict[str, int]:
    counts = {}

    raw_products = lake.read_bronze("products", ingestion_date)
    products_df = transform_products(raw_products)
    lake.write_silver("products", ingestion_date, products_df)
    counts["products"] = len(products_df)

    raw_users = lake.read_bronze("users", ingestion_date)
    users_df = transform_users(raw_users)
    lake.write_silver("users", ingestion_date, users_df)
    counts["users"] = len(users_df)

    raw_carts = lake.read_bronze("carts", ingestion_date)
    carts_silver = transform_carts(raw_carts)
    lake.write_silver("carts", ingestion_date, carts_silver.carts)
    lake.write_silver("cart_items", ingestion_date, carts_silver.cart_items)
    counts["carts"] = len(carts_silver.carts)
    counts["cart_items"] = len(carts_silver.cart_items)

    return counts


def run_silver_to_warehouse(lake: DataLakeClient, ingestion_date: date) -> dict[str, int]:
    engine = get_engine()
    counts = {}

    products_df = lake.read_silver("products", ingestion_date)
    counts["raw.products"] = load_raw_table(engine, products_df, "products")

    users_df = lake.read_silver("users", ingestion_date)
    counts["raw.users"] = load_raw_table(engine, users_df, "users")

    carts_df = lake.read_silver("carts", ingestion_date)
    counts["raw.carts"] = load_raw_table(engine, carts_df, "carts")

    cart_items_df = lake.read_silver("cart_items", ingestion_date)
    counts["raw.cart_items"] = load_raw_table(engine, cart_items_df, "cart_items")

    upsert_dim_date(engine, {ingestion_date})
    upsert_dim_product(engine)
    upsert_dim_customer(engine)
    counts["fact_orders"] = load_fact_orders(engine, ingestion_date)

    return counts


def run_full_pipeline(ingestion_date: date | None = None) -> None:
    ingestion_date = ingestion_date or datetime.now(UTC).date()
    lake = DataLakeClient()
    lake.ensure_buckets()
    engine = get_engine()

    logger.info("Starting pipeline run for ingestion_date=%s", ingestion_date)

    with track_pipeline_run(engine, PIPELINE_NAME, source_name="dummyjson_api") as stats:
        extract_counts = run_extract_to_bronze(lake, ingestion_date)
        stats.extracted_rows = sum(extract_counts.values())
        logger.info("Bronze layer written: %s", extract_counts)

        silver_counts = run_bronze_to_silver(lake, ingestion_date)
        logger.info("Silver layer written: %s", silver_counts)

        warehouse_counts = run_silver_to_warehouse(lake, ingestion_date)
        stats.inserted_rows = sum(warehouse_counts.values())
        logger.info("Warehouse loaded: %s", warehouse_counts)

    logger.info("Pipeline run for ingestion_date=%s completed successfully", ingestion_date)
