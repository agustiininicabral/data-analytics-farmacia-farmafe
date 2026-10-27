-- QUERY: monthly_sales
SELECT
    substr(sale_date, 1, 7) AS month,
    COUNT(DISTINCT transaction_id) AS transactions,
    SUM(quantity) AS units,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct)), 2) AS net_sales,
    ROUND(SUM(quantity * unit_cost), 2) AS cogs,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct) - quantity * unit_cost), 2) AS gross_profit
FROM sales
GROUP BY substr(sale_date, 1, 7)
ORDER BY month;

-- QUERY: category_sales
SELECT
    p.category,
    COUNT(DISTINCT s.transaction_id) AS transactions,
    SUM(s.quantity) AS units,
    ROUND(SUM(s.quantity * s.unit_price * (1 - s.discount_pct)), 2) AS net_sales,
    ROUND(SUM(s.quantity * s.unit_price * (1 - s.discount_pct) - s.quantity * s.unit_cost), 2) AS gross_profit
FROM sales AS s
JOIN products AS p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY net_sales DESC;

-- QUERY: channel_sales
SELECT
    channel,
    COUNT(DISTINCT transaction_id) AS transactions,
    SUM(quantity) AS units,
    ROUND(SUM(quantity * unit_price * (1 - discount_pct)), 2) AS net_sales
FROM sales
GROUP BY channel
ORDER BY net_sales DESC;

-- QUERY: stock_alerts
SELECT
    p.product_id,
    p.product_name,
    p.category,
    i.stock_on_hand,
    p.reorder_point
FROM inventory AS i
JOIN products AS p ON p.product_id = i.product_id
WHERE i.stock_on_hand <= p.reorder_point
ORDER BY i.stock_on_hand, p.product_id;
