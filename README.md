# Supermarket Sales Analysis & Customer Segmentation (DWDM)

An end-to-end Data Warehousing and Data Mining project for a supermarket chain. It uses **locally generated CSV source files**, a **Snowflake schema**, ETL/preprocessing, OLAP-style SQL, and K-Means customer segmentation. No external data or Python packages are required.

## Project structure

```
data/raw/                 Generated operational CSVs (customers, products, stores, sales)
data/processed/           Cleaned sales file and customer RFM metrics
sql/                      Snowflake DDL and OLAP query library
src/generate_data.py      Reproducible source-data generator
src/pipeline.py           ETL, warehouse load, OLAP execution, mining and visual outputs
outputs/                  SQLite warehouse, reports, segment CSV, SVG charts
```

## Business questions

1. Which city, product line and member type produce the most revenue?
2. How do sales vary by month and payment method?
3. Who are the highest-value customers, and which customers are at risk?
4. What customer groups emerge from Recency, Frequency and Monetary (RFM) behaviour?

## Run

From the repository root (Python 3.10+):

```powershell
python src/generate_data.py
python src/pipeline.py
```

Open `outputs/analysis_report.md` for results and `outputs/visualizations/` for charts. The warehouse is `outputs/supermarket_warehouse.db`; it can be inspected with any SQLite client.

## Architecture

```
Raw CSV files -> validation & standardisation -> cleaned CSV -> SQLite warehouse
                                                     |             |
                                                     v             v
                                               RFM feature set  OLAP SQL cubes
                                                     |
                                                     v
                                              K-Means segments + charts
```

## Snowflake schema

`fact_sales` is the central fact table. It links to `dim_date`, `dim_customer`, `dim_product`, `dim_store`, `dim_payment`, and `dim_member_type`. Product hierarchy is normalized through `dim_product_line`; store geography is normalized through `dim_city`. This exposes the product and location hierarchies required for roll-up/drill-down OLAP.

The supplied DDL is portable SQL; SQLite is deliberately used as the local warehouse engine so the entire submission runs offline. It can be adapted to Snowflake/PostgreSQL by replacing `INTEGER PRIMARY KEY AUTOINCREMENT` and `INSERT OR IGNORE` syntax.

## Data notes

The generator uses a fixed seed and creates 1,800 transactions for 2024. It intentionally introduces a small number of missing payment methods, duplicate rows, whitespace/case inconsistencies, and invalid quantities. The ETL pipeline records and removes/corrects these issues before the warehouse load.

## Reference note

The requested Food Delivery-DWDM repository informed the project-style scope (separate data, SQL, scripts, outputs, and documentation). This repository implements an original supermarket-domain data model, data generator, analysis, and code.

