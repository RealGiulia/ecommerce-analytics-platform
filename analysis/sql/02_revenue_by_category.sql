-- Net revenue and unit volume by product category.
SELECT
    dp.category,
    SUM(f.quantity)              AS units_sold,
    ROUND(SUM(f.net_amount), 2)  AS net_revenue
FROM analytics.fact_orders f
JOIN analytics.dim_product dp ON dp.product_key = f.product_key
GROUP BY dp.category
ORDER BY net_revenue DESC;
