CREATE TABLE IF NOT EXISTS analytics.fact_orders (
    order_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_id VARCHAR(100) NOT NULL,
    order_item_id VARCHAR(100) NOT NULL,

    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    order_date_key INTEGER NOT NULL,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(18, 2) NOT NULL,
    discount_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    gross_amount NUMERIC(18, 2) NOT NULL,
    net_amount NUMERIC(18, 2) NOT NULL,

    order_status VARCHAR(50),
    source_system VARCHAR(100),

    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Includes order_date_key (not just order_id/order_item_id) so a backfill
    -- for a *different* date adds new rows instead of colliding with -- and
    -- silently overwriting -- whichever date the row was first loaded with.
    -- Re-running the same date stays idempotent (see etl/load/fact_loader.py).
    CONSTRAINT uq_fact_order_item
        UNIQUE (order_id, order_item_id, order_date_key),

    CONSTRAINT fk_fact_customer
        FOREIGN KEY (customer_key)
        REFERENCES analytics.dim_customer (customer_key),

    CONSTRAINT fk_fact_product
        FOREIGN KEY (product_key)
        REFERENCES analytics.dim_product (product_key),

    CONSTRAINT fk_fact_order_date
        FOREIGN KEY (order_date_key)
        REFERENCES analytics.dim_date (date_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer
    ON analytics.fact_orders (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_orders_product
    ON analytics.fact_orders (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_orders_date
    ON analytics.fact_orders (order_date_key);