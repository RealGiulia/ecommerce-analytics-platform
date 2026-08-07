"""Bronze -> silver transformation for the carts entity.

Each cart embeds a list of product lines. That list is exploded into a
separate ``cart_items`` grain (one row per product-within-cart) since it
maps directly onto the ``fact_orders`` grain downstream; the cart header
(totals, owning user) becomes its own ``carts`` table.
"""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd

from etl.transform.cleaning import dedupe_by_id, utcnow


class CartsSilver(NamedTuple):
    carts: pd.DataFrame
    cart_items: pd.DataFrame


def transform_carts(raw_carts: list[dict]) -> CartsSilver:
    if not raw_carts:
        return CartsSilver(pd.DataFrame(), pd.DataFrame())

    ingested_at = utcnow()
    cart_rows = []
    item_rows = []

    for cart in raw_carts:
        cart_id = cart["id"]
        cart_rows.append(
            {
                "cart_id": cart_id,
                "user_id": cart.get("userId"),
                "total": cart.get("total"),
                "discounted_total": cart.get("discountedTotal"),
                "total_products": cart.get("totalProducts"),
                "total_quantity": cart.get("totalQuantity"),
                "ingested_at": ingested_at,
            }
        )
        for item in cart.get("products", []):
            item_rows.append(
                {
                    "cart_id": cart_id,
                    "product_id": item.get("id"),
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "quantity": item.get("quantity"),
                    "total": item.get("total"),
                    "discount_percentage": item.get("discountPercentage"),
                    "discounted_total": item.get("discountedTotal"),
                    "ingested_at": ingested_at,
                }
            )

    carts_df = pd.DataFrame(cart_rows)
    carts_df["total"] = carts_df["total"].astype(float)
    carts_df["discounted_total"] = carts_df["discounted_total"].astype(float)
    carts_df = dedupe_by_id(carts_df, "cart_id")

    cart_items_df = pd.DataFrame(item_rows)
    cart_items_df["price"] = cart_items_df["price"].astype(float)
    cart_items_df["total"] = cart_items_df["total"].astype(float)
    cart_items_df["discounted_total"] = cart_items_df["discounted_total"].astype(float)
    cart_items_df["quantity"] = cart_items_df["quantity"].astype("Int64")
    cart_items_df = cart_items_df.drop_duplicates(
        subset=["cart_id", "product_id"], keep="last"
    ).reset_index(drop=True)

    return CartsSilver(carts_df, cart_items_df)
