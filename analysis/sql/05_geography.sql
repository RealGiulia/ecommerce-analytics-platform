-- Top 10 countries by net revenue.
SELECT
    dc.state,
    COUNT(DISTINCT dc.customer_key)  AS customers,
    ROUND(SUM(f.net_amount), 2)      AS net_revenue
FROM analytics.fact_orders f
JOIN analytics.dim_customer dc ON dc.customer_key = f.customer_key
GROUP BY dc.state
ORDER BY net_revenue DESC
LIMIT 10;
