"""Thin, resilient HTTP client for the DummyJSON REST API.

DummyJSON paginates list endpoints with ``limit``/``skip`` query params and
reports the total record count on every page, so a generic client can page
through any of the three endpoints (products/users/carts) the same way.
"""

from __future__ import annotations

import requests
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from etl.config import DataEndpointsConfig, endpoints_config
from etl.logging_setup import get_logger

logger = get_logger(__name__)


class DummyJsonClient:
    """Fetches complete collections from DummyJSON, transparently paginating."""

    def __init__(self, config: DataEndpointsConfig = endpoints_config) -> None:
        self._config = config
        self._session = requests.Session()

    def fetch_all(self, url: str, collection_key: str) -> list[dict]:
        """Page through a DummyJSON list endpoint and return every record.

        Args:
            url: Base endpoint, e.g. ``https://dummyjson.com/products``.
            collection_key: Name of the JSON array in the response
                (``"products"``, ``"users"`` or ``"carts"``).
        """
        records: list[dict] = []
        skip = 0
        total = None

        while total is None or skip < total:
            payload = self._get_page(url, skip=skip, limit=self._config.page_size)
            batch = payload[collection_key]
            records.extend(batch)
            total = payload["total"]
            skip += self._config.page_size

            logger.info(
                "Fetched %d/%d records from %s (skip=%d)",
                len(records),
                total,
                url,
                skip,
            )

            if not batch:
                break

        return records

    def _get_page(self, url: str, skip: int, limit: int) -> dict:
        retrying = Retrying(
            retry=retry_if_exception_type(
                (requests.ConnectionError, requests.Timeout, requests.HTTPError)
            ),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            stop=stop_after_attempt(self._config.max_retries),
            reraise=True,
        )
        return retrying(self._request, url, params={"limit": limit, "skip": skip})

    def _request(self, url: str, params: dict) -> dict:
        response = self._session.get(url, params=params, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.json()
