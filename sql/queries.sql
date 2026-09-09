-- E-Commerce Sales & Customer Analytics
-- Analyst queries answering the business questions in README.md
-- SQLite dialect. Run via sql/run_queries.py, output saved to sample_output.txt

-- 1. Data quality: row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'employees', COUNT(*) FROM employees
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;

-- 2. Order status breakdown (cancellation / return rate)
SELECT
    status,
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1) AS pct_of_orders
FROM orders
GROUP BY status
ORDER BY orders DESC;

-- 3. Overall sales KPIs (completed orders only)
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS total_customers,
    ROUND(SUM(oi.quantity * p.price), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * (p.price - p.cost)), 2) AS total_profit,
    ROUND(SUM(oi.quantity * (p.price - p.cost)) / SUM(oi.quantity * p.price) * 100, 1) AS gross_margin_pct,
    ROUND(SUM(oi.quantity * p.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'Completed';

-- 4. Monthly revenue trend
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY month
ORDER BY month;

-- 5. Top products by revenue and profit
SELECT
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue,
    ROUND(SUM(oi.quantity * (p.price - p.cost)), 2) AS profit,
    ROUND(AVG((p.price - p.cost) / p.price) * 100, 1) AS margin_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- 6. Category performance (revenue, profit, margin)
SELECT
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue,
    ROUND(SUM(oi.quantity * (p.price - p.cost)), 2) AS profit,
    ROUND(SUM(oi.quantity * (p.price - p.cost)) / SUM(oi.quantity * p.price) * 100, 1) AS margin_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY revenue DESC;

-- 7. Top 10 customers by lifetime revenue
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.city || ', ' || c.state AS location,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY c.customer_id
ORDER BY revenue DESC
LIMIT 10;

-- 8. Customer value concentration (Pareto / 80-20 check)
-- Ranks customers by revenue and buckets them into quartiles to see how
-- concentrated revenue is among the top spenders.
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * p.price) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.status = 'Completed'
    GROUP BY o.customer_id
),
ranked AS (
    SELECT
        revenue,
        NTILE(4) OVER (ORDER BY revenue DESC) AS quartile
    FROM customer_revenue
)
SELECT
    CASE quartile
        WHEN 1 THEN 'Top 25% of customers'
        WHEN 2 THEN '2nd quartile'
        WHEN 3 THEN '3rd quartile'
        WHEN 4 THEN 'Bottom 25% of customers'
    END AS segment,
    COUNT(*) AS customers,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM customer_revenue), 1) AS pct_of_revenue
FROM ranked
GROUP BY quartile
ORDER BY quartile;

-- 9. Sales rep (employee) performance
SELECT
    e.employee_name,
    COUNT(DISTINCT o.order_id) AS completed_orders,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue,
    ROUND(SUM(oi.quantity * p.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM employees e
JOIN orders o ON e.employee_id = o.employee_id AND o.status = 'Completed'
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY e.employee_id, e.employee_name
ORDER BY revenue DESC;

-- 10. Revenue by state (geographic concentration)
SELECT
    c.state,
    COUNT(DISTINCT c.customer_id) AS customers,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'Completed'
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY c.state
ORDER BY revenue DESC;
