from etl.transform.products import transform_products

RAW_PRODUCT = {
    "id": 1,
    "title": "Essence Mascara",
    "category": "beauty",
    "brand": "Essence",
    "sku": "BEA-001",
    "price": 9.99,
    "discountPercentage": 10.48,
    "rating": 2.56,
    "stock": 99,
    "weight": 4,
    "dimensions": {"width": 15.14, "height": 13.08, "depth": 22.99},
    "tags": ["beauty", "mascara"],
    "warrantyInformation": "1 week warranty",
    "shippingInformation": "Ships in 3-5 business days",
    "availabilityStatus": "In Stock",
    "returnPolicy": "No return policy",
    "minimumOrderQuantity": 48,
    "meta": {"createdAt": "2025-04-30T09:41:02.053Z", "updatedAt": "2025-04-30T09:41:02.053Z"},
    "reviews": [{"rating": 3, "comment": "meh"}],
    "images": ["https://example.com/1.webp"],
}


def test_transform_products_flattens_dimensions_and_drops_noise():
    df = transform_products([RAW_PRODUCT])

    assert len(df) == 1
    row = df.iloc[0]
    assert row["product_id"] == 1
    assert row["width"] == 15.14
    assert row["height"] == 13.08
    assert row["depth"] == 22.99
    assert row["tags"] == "beauty,mascara"
    assert "reviews" not in df.columns
    assert "images" not in df.columns
    assert "dimensions" not in df.columns


def test_transform_products_dedupes_by_product_id():
    df = transform_products([RAW_PRODUCT, RAW_PRODUCT])

    assert len(df) == 1


def test_transform_products_empty_input_returns_empty_dataframe():
    df = transform_products([])

    assert df.empty
