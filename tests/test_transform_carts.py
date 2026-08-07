from etl.transform.carts import transform_carts

RAW_CART = {
    "id": 1,
    "userId": 1,
    "total": 13037.88,
    "discountedTotal": 11510.81,
    "totalProducts": 2,
    "totalQuantity": 7,
    "products": [
        {
            "id": 162,
            "title": "Blue Frock",
            "price": 29.99,
            "quantity": 4,
            "total": 119.96,
            "discountPercentage": 12.13,
            "discountedTotal": 105.41,
        },
        {
            "id": 113,
            "title": "Generic Motorcycle",
            "price": 3999.99,
            "quantity": 3,
            "total": 11999.97,
            "discountPercentage": 12.1,
            "discountedTotal": 10547.97,
        },
    ],
}


def test_transform_carts_produces_header_and_exploded_items():
    result = transform_carts([RAW_CART])

    assert len(result.carts) == 1
    assert result.carts.iloc[0]["cart_id"] == 1
    assert result.carts.iloc[0]["user_id"] == 1

    assert len(result.cart_items) == 2
    assert set(result.cart_items["product_id"]) == {162, 113}
    assert all(result.cart_items["cart_id"] == 1)


def test_transform_carts_empty_input_returns_empty_frames():
    result = transform_carts([])

    assert result.carts.empty
    assert result.cart_items.empty
