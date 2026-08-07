-- Landing tables for the silver layer read back out of MinIO.
-- These mirror the DummyJSON entities as full-snapshot loads (truncate +
-- insert on every pipeline run): the source API has no incremental /
-- updated-since capability, so the raw layer always reflects the latest
-- pull rather than an append-only history.

CREATE TABLE IF NOT EXISTS raw.products (
    product_id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(100),
    sku VARCHAR(100),
    price NUMERIC(18, 2),
    discount_percentage NUMERIC(5, 2),
    rating NUMERIC(3, 2),
    stock INTEGER,
    weight NUMERIC(10, 2),
    width NUMERIC(10, 2),
    height NUMERIC(10, 2),
    depth NUMERIC(10, 2),
    tags VARCHAR(500),
    warranty_information VARCHAR(255),
    shipping_information VARCHAR(255),
    availability_status VARCHAR(50),
    return_policy VARCHAR(255),
    minimum_order_quantity INTEGER,
    created_at_source TIMESTAMP,
    updated_at_source TIMESTAMP,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.users (
    user_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    username VARCHAR(100),
    age INTEGER,
    gender VARCHAR(20),
    birth_date DATE,
    role VARCHAR(50),
    university VARCHAR(255),
    company_name VARCHAR(255),
    company_department VARCHAR(100),
    company_title VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    state_code VARCHAR(10),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.carts (
    cart_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    total NUMERIC(18, 2),
    discounted_total NUMERIC(18, 2),
    total_products INTEGER,
    total_quantity INTEGER,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cart_items (
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    title VARCHAR(255),
    price NUMERIC(18, 2),
    quantity INTEGER,
    total NUMERIC(18, 2),
    discount_percentage NUMERIC(5, 2),
    discounted_total NUMERIC(18, 2),
    ingested_at TIMESTAMP NOT NULL,
    PRIMARY KEY (cart_id, product_id)
);
