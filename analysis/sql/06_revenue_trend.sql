-- Net revenue and order count by ingestion date, for a day-over-day trend.
-- Only meaningful once the pipeline has been backfilled across multiple
-- dates (see analysis/README.md, "Nota sobre análise temporal").
SELECT
    dd.full_date,
    ROUND(SUM(f.net_amount), 2)  AS net_revenue,
    COUNT(DISTINCT f.order_id)   AS orders
FROM analytics.fact_orders f
JOIN analytics.dim_date dd ON dd.date_key = f.order_date_key
GROUP BY dd.full_date
ORDER BY dd.full_date;
