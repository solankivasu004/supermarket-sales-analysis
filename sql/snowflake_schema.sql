-- Supermarket analytical Snowflake schema
PRAGMA foreign_keys = ON;

CREATE TABLE dim_city (city_key INTEGER PRIMARY KEY AUTOINCREMENT, city_name TEXT UNIQUE NOT NULL);
CREATE TABLE dim_store (
  store_key INTEGER PRIMARY KEY AUTOINCREMENT, store_id TEXT UNIQUE NOT NULL,
  branch TEXT NOT NULL, city_key INTEGER NOT NULL, FOREIGN KEY(city_key) REFERENCES dim_city(city_key));
CREATE TABLE dim_product_line (product_line_key INTEGER PRIMARY KEY AUTOINCREMENT, product_line TEXT UNIQUE NOT NULL);
CREATE TABLE dim_product (
  product_key INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT UNIQUE NOT NULL,
  product_name TEXT NOT NULL, product_line_key INTEGER NOT NULL, unit_price REAL NOT NULL,
  FOREIGN KEY(product_line_key) REFERENCES dim_product_line(product_line_key));
CREATE TABLE dim_member_type (member_type_key INTEGER PRIMARY KEY AUTOINCREMENT, member_type TEXT UNIQUE NOT NULL);
CREATE TABLE dim_customer (
  customer_key INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT UNIQUE NOT NULL,
  customer_name TEXT NOT NULL, gender TEXT NOT NULL, member_type_key INTEGER NOT NULL,
  FOREIGN KEY(member_type_key) REFERENCES dim_member_type(member_type_key));
CREATE TABLE dim_payment (payment_key INTEGER PRIMARY KEY AUTOINCREMENT, payment_method TEXT UNIQUE NOT NULL);
CREATE TABLE dim_date (
  date_key INTEGER PRIMARY KEY, full_date TEXT UNIQUE NOT NULL, day_num INTEGER NOT NULL,
  month_num INTEGER NOT NULL, month_name TEXT NOT NULL, quarter_num INTEGER NOT NULL, year_num INTEGER NOT NULL);
CREATE TABLE fact_sales (
  sale_key INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id TEXT UNIQUE NOT NULL, date_key INTEGER NOT NULL,
  customer_key INTEGER NOT NULL, product_key INTEGER NOT NULL, store_key INTEGER NOT NULL, payment_key INTEGER NOT NULL,
  quantity INTEGER NOT NULL, gross_sales REAL NOT NULL, tax REAL NOT NULL, total_sales REAL NOT NULL, rating REAL NOT NULL,
  FOREIGN KEY(date_key) REFERENCES dim_date(date_key), FOREIGN KEY(customer_key) REFERENCES dim_customer(customer_key),
  FOREIGN KEY(product_key) REFERENCES dim_product(product_key), FOREIGN KEY(store_key) REFERENCES dim_store(store_key),
  FOREIGN KEY(payment_key) REFERENCES dim_payment(payment_key));

