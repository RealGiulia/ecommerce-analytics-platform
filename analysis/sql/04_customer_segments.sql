-- Revenue and customer count by the age-bucket segment assigned in dim_customer.
SELECT
    dc.customer_segment,
    COUNT(DISTINCT dc.customer_key)  AS customers,
    ROUND(SUM(f.net_amount), 2)      AS net_revenue,
    ROUND(SUM(f.net_amount) / NULLIF(COUNT(DISTINCT dc.customer_key), 0), 2) AS revenue_per_customer
FROM analytics.fact_orders f
JOIN analytics.dim_customer dc ON dc.customer_key = f.customer_key
GROUP BY dc.customer_segment
ORDER BY net_revenue DESC;
