"""Bronze -> silver transformation for the products entity.

Nested catalog content (reviews, image galleries, QR/barcodes) is dropped:
it has no analytical value for the star schema and only adds noise. The
``dimensions`` object is flattened into individual numeric columns.
"""

from __future__ import annotations

import pandas as pd

from etl.transform.cleaning import dedupe_by_id, utcnow


def transform_products(raw_products: list[dict]) -> pd.DataFrame:
    if not raw_products:
        return pd.DataFrame()

    ingested_at = utcnow()
    rows = []
    for product in raw_products:
        dimensions = product.get("dimensions") or {}
        meta = product.get("meta") or {}
        rows.append(
            {
                "product_id": product["id"],
                "title": product.get("title"),
                "category": product.get("category"),
                "brand": product.get("brand"),
                "sku": product.get("sku"),
                "price": product.get("price"),
                "discount_percentage": product.get("discountPercentage"),
                "rating": product.get("rating"),
                "stock": product.get("stock"),
                "weight": product.get("weight"),
                "width": dimensions.get("width"),
                "height": dimensions.get("height"),
                "depth": dimensions.get("depth"),
                "tags": ",".join(product.get("tags") or []),
                "warranty_information": product.get("warrantyInformation"),
                "shipping_information": product.get("shippingInformation"),
                "availability_status": product.get("availabilityStatus"),
                "return_policy": product.get("returnPolicy"),
                "minimum_order_quantity": product.get("minimumOrderQuantity"),
                "created_at_source": meta.get("createdAt"),
                "updated_at_source": meta.get("updatedAt"),
                "ingested_at": ingested_at,
            }
        )

    df = pd.DataFrame(rows)
    df["created_at_source"] = (
        pd.to_datetime(df["created_at_source"], errors="coerce", utc=True).dt.tz_localize(None)
    )
    df["updated_at_source"] = (
        pd.to_datetime(df["updated_at_source"], errors="coerce", utc=True).dt.tz_localize(None)
    )
    df["price"] = df["price"].astype(float)
    df["discount_percentage"] = df["discount_percentage"].astype(float)
    df["rating"] = df["rating"].astype(float)
    df["stock"] = df["stock"].astype("Int64")
    df["minimum_order_quantity"] = df["minimum_order_quantity"].astype("Int64")

    return dedupe_by_id(df, "product_id")
