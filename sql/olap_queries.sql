-- 1. Roll-up: monthly revenue by city
SELECT d.year_num, d.month_num, c.city_name, ROUND(SUM(f.total_sales),2) AS revenue
FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key
JOIN dim_store s ON f.store_key=s.store_key JOIN dim_city c ON s.city_key=c.city_key
GROUP BY d.year_num,d.month_num,c.city_name ORDER BY d.year_num,d.month_num,revenue DESC;

-- 2. Slice: member sales by product line
SELECT pl.product_line, ROUND(SUM(f.total_sales),2) AS revenue, COUNT(*) AS transactions
FROM fact_sales f JOIN dim_customer cu ON f.customer_key=cu.customer_key
JOIN dim_member_type mt ON cu.member_type_key=mt.member_type_key
JOIN dim_product p ON f.product_key=p.product_key JOIN dim_product_line pl ON p.product_line_key=pl.product_line_key
WHERE mt.member_type='Member' GROUP BY pl.product_line ORDER BY revenue DESC;

-- 3. Dice: Q4 sales for selected cities and product lines
SELECT c.city_name, pl.product_line, ROUND(SUM(f.total_sales),2) AS revenue
FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key JOIN dim_store s ON f.store_key=s.store_key
JOIN dim_city c ON s.city_key=c.city_key JOIN dim_product p ON f.product_key=p.product_key
JOIN dim_product_line pl ON p.product_line_key=pl.product_line_key
WHERE d.quarter_num=4 AND c.city_name IN ('Delhi','Mumbai')
GROUP BY c.city_name,pl.product_line ORDER BY revenue DESC;

