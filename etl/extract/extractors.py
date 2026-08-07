"""Entity-specific extraction functions, one per DummyJSON endpoint."""

from __future__ import annotations

from etl.config import DataEndpointsConfig, endpoints_config
from etl.extract.api_client import DummyJsonClient
from etl.logging_setup import get_logger

logger = get_logger(__name__)


def extract_products(
    client: DummyJsonClient | None = None,
    config: DataEndpointsConfig = endpoints_config,
) -> list[dict]:
    client = client or DummyJsonClient(config)
    logger.info("Extracting products from %s", config.products_url)
    return client.fetch_all(config.products_url, collection_key="products")


def extract_users(
    client: DummyJsonClient | None = None,
    config: DataEndpointsConfig = endpoints_config,
) -> list[dict]:
    client = client or DummyJsonClient(config)
    logger.info("Extracting users from %s", config.customers_url)
    return client.fetch_all(config.customers_url, collection_key="users")


def extract_carts(
    client: DummyJsonClient | None = None,
    config: DataEndpointsConfig = endpoints_config,
) -> list[dict]:
    client = client or DummyJsonClient(config)
    logger.info("Extracting carts from %s", config.carts_url)
    return client.fetch_all(config.carts_url, collection_key="carts")
