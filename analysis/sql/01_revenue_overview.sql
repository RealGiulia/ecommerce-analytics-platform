-- Headline KPIs for the loaded snapshot: revenue, orders, AOV.
SELECT
    COUNT(DISTINCT f.order_id)                              AS total_orders,
    COUNT(*)                                                  AS total_order_lines,
    COUNT(DISTINCT f.customer_key)                             AS total_customers,
    SUM(f.quantity)                                              AS total_units_sold,
    ROUND(SUM(f.net_amount), 2)                                   AS total_net_revenue,
    ROUND(SUM(f.discount_amount), 2)                               AS total_discount_given,
    ROUND(SUM(f.net_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS avg_order_value
FROM analytics.fact_orders f;
