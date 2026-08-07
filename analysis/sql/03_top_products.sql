-- Top 10 products by net revenue, with category for context.
SELECT
    dp.product_name,
    dp.category,
    dp.brand,
    SUM(f.quantity)              AS units_sold,
    ROUND(SUM(f.net_amount), 2)  AS net_revenue
FROM analytics.fact_orders f
JOIN analytics.dim_product dp ON dp.product_key = f.product_key
GROUP BY dp.product_name, dp.category, dp.brand
ORDER BY net_revenue DESC
LIMIT 10;
