# Supermarket Sales Analysis

## Warehouse load

- Source rows: 1,801; loaded fact rows: 1,799
- Data-quality actions: {'duplicates': 1, 'invalid_quantity': 1, 'imputed_payment': 1}
- Dimensions: 7; schema: Snowflake (product-line and city outriggers)

## Executive findings

- Total revenue: **$60,010.26**
- Highest-revenue city: **Delhi ($21,163.65)**
- Highest-revenue product line: **Sports & Travel ($14,126.70)**
- Most used payment method: **Upi (741 transactions)**

## Customer segmentation

RFM features were standardised and clustered with K-Means (k=4). Segment labels are assigned from the average monetary value of each cluster. See `data/processed/customer_rfm_segments.csv`.

| Segment | Revenue |
|---|---:|
| High Value | $25,448.27 |
| Regular | $24,645.08 |
| Occasional | $7,825.82 |
| At Risk | $2,091.09 |

## OLAP

Reusable roll-up, slice, and dice queries are in `sql/olap_queries.sql`. Charts are in `outputs/visualizations/`.

