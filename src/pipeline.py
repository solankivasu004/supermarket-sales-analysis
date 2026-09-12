"""ETL, local Snowflake warehouse, OLAP summaries, K-Means mining and SVG dashboards."""
from __future__ import annotations
import csv, math, random, sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data" / "raw"; PROCESSED = ROOT / "data" / "processed"; OUT = ROOT / "outputs"; VIZ = OUT / "visualizations"

def read_csv(name):
    with (RAW / name).open(encoding="utf-8") as f: return list(csv.DictReader(f))
def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

def clean_sales(rows):
    cleaned, seen, rejected = [], set(), {"duplicates": 0, "invalid_quantity": 0, "imputed_payment": 0}
    for r in rows:
        r = {k: v.strip() for k, v in r.items()}; r["store_id"] = r["store_id"].upper(); r["payment_method"] = r["payment_method"].title()
        if r["invoice_id"] in seen: rejected["duplicates"] += 1; continue
        seen.add(r["invoice_id"])
        if int(r["quantity"]) <= 0: rejected["invalid_quantity"] += 1; continue
        if not r["payment_method"]: r["payment_method"] = "Unknown"; rejected["imputed_payment"] += 1
        for key in ("gross_sales", "tax", "total_sales", "rating"): r[key] = f"{float(r[key]):.2f}"
        cleaned.append(r)
    return cleaned, rejected

def connect_and_load(customers, products, stores, sales):
    OUT.mkdir(exist_ok=True); db_path = OUT / "supermarket_warehouse.db"
    if db_path.exists(): db_path.unlink()
    con = sqlite3.connect(db_path); con.executescript((ROOT / "sql" / "snowflake_schema.sql").read_text())
    cur = con.cursor()
    for s in stores: cur.execute("INSERT OR IGNORE INTO dim_city(city_name) VALUES(?)", (s["city"],))
    for s in stores:
        city = cur.execute("SELECT city_key FROM dim_city WHERE city_name=?", (s["city"],)).fetchone()[0]
        cur.execute("INSERT INTO dim_store(store_id,branch,city_key) VALUES(?,?,?)", (s["store_id"],s["branch"],city))
    for p in products: cur.execute("INSERT OR IGNORE INTO dim_product_line(product_line) VALUES(?)", (p["product_line"],))
    for p in products:
        line = cur.execute("SELECT product_line_key FROM dim_product_line WHERE product_line=?", (p["product_line"],)).fetchone()[0]
        cur.execute("INSERT INTO dim_product(product_id,product_name,product_line_key,unit_price) VALUES(?,?,?,?)", (p["product_id"],p["product_name"],line,p["unit_price"]))
    for c in customers: cur.execute("INSERT OR IGNORE INTO dim_member_type(member_type) VALUES(?)", (c["member_type"],))
    for c in customers:
        mt = cur.execute("SELECT member_type_key FROM dim_member_type WHERE member_type=?", (c["member_type"],)).fetchone()[0]
        cur.execute("INSERT INTO dim_customer(customer_id,customer_name,gender,member_type_key) VALUES(?,?,?,?)", (c["customer_id"],c["customer_name"],c["gender"],mt))
    for pm in sorted({x["payment_method"] for x in sales}): cur.execute("INSERT INTO dim_payment(payment_method) VALUES(?)", (pm,))
    for r in sales:
        dt = datetime.fromisoformat(r["sale_date"]); dk = int(dt.strftime("%Y%m%d"))
        cur.execute("INSERT OR IGNORE INTO dim_date VALUES(?,?,?,?,?,?,?)", (dk,r["sale_date"],dt.day,dt.month,dt.strftime("%B"),(dt.month-1)//3+1,dt.year))
        ids = []
        for table, field, value, key in [("dim_customer","customer_id",r["customer_id"],"customer_key"),("dim_product","product_id",r["product_id"],"product_key"),("dim_store","store_id",r["store_id"],"store_key"),("dim_payment","payment_method",r["payment_method"],"payment_key")]:
            ids.append(cur.execute(f"SELECT {key} FROM {table} WHERE {field}=?", (value,)).fetchone()[0])
        cur.execute("INSERT INTO fact_sales(invoice_id,date_key,customer_key,product_key,store_key,payment_key,quantity,gross_sales,tax,total_sales,rating) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (r["invoice_id"],dk,*ids,int(r["quantity"]),float(r["gross_sales"]),float(r["tax"]),float(r["total_sales"]),float(r["rating"])))
    con.commit(); return con

def kmeans(rows, k=4, rounds=60):
    # Standardised RFM features; deterministic simple K-Means avoids third-party packages.
    fields = ["recency_days", "frequency", "monetary"]
    means = {f: sum(float(r[f]) for r in rows)/len(rows) for f in fields}; stds = {f: math.sqrt(sum((float(r[f])-means[f])**2 for r in rows)/len(rows)) or 1 for f in fields}
    points = [[(float(r[f])-means[f])/stds[f] for f in fields] for r in rows]; random.seed(42); centers = [points[i][:] for i in [0, len(points)//3, 2*len(points)//3, -1]]
    labels = [0]*len(points)
    for _ in range(rounds):
        labels = [min(range(k), key=lambda j: sum((x[a]-centers[j][a])**2 for a in range(3))) for x in points]
        new = []
        for j in range(k):
            group = [p for p,l in zip(points,labels) if l == j]; new.append([sum(p[a] for p in group)/len(group) for a in range(3)] if group else centers[j])
        if new == centers: break
        centers = new
    # Human-readable labels based on monetary rank of clusters.
    totals = {j: sum(float(r["monetary"]) for r,l in zip(rows,labels) if l==j)/max(labels.count(j),1) for j in range(k)}
    ordered = sorted(totals, key=totals.get); names = {ordered[0]: "At Risk", ordered[1]: "Occasional", ordered[2]: "Regular", ordered[3]: "High Value"}
    for r,l in zip(rows,labels): r["cluster"] = l+1; r["segment"] = names[l]
    return rows

def svg_bar(path, title, pairs, colour="#2563eb"):
    maxv=max(v for _,v in pairs); width=720; h=340; bars=[]
    for i,(label,value) in enumerate(pairs):
        x=70+i*100; bh=220*value/maxv; bars.append(f'<rect x="{x}" y="{280-bh:.1f}" width="58" height="{bh:.1f}" fill="{colour}"/><text x="{x+29}" y="302" text-anchor="middle" font-size="11">{label}</text><text x="{x+29}" y="{272-bh:.1f}" text-anchor="middle" font-size="10">{value:,.0f}</text>')
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="30" y="35" font-size="20" font-family="Arial" font-weight="bold">{title}</text><line x1="55" y1="280" x2="690" y2="280" stroke="#555"/>{"".join(bars)}</svg>', encoding="utf-8")

def main():
    PROCESSED.mkdir(parents=True, exist_ok=True); VIZ.mkdir(parents=True, exist_ok=True)
    sales, quality = clean_sales(read_csv("sales.csv")); write_csv(PROCESSED / "sales_clean.csv", sales)
    con = connect_and_load(read_csv("customers.csv"), read_csv("products.csv"), read_csv("stores.csv"), sales); cur=con.cursor()
    # RFM snapshot: date 2024-12-31 (one day after source range).
    rfm = []
    for customer_id, recency, frequency, monetary in cur.execute("SELECT c.customer_id, CAST(julianday('2024-12-31')-julianday(MAX(d.full_date)) AS INT), COUNT(*), ROUND(SUM(f.total_sales),2) FROM fact_sales f JOIN dim_customer c ON f.customer_key=c.customer_key JOIN dim_date d ON f.date_key=d.date_key GROUP BY c.customer_id"):
        rfm.append({"customer_id":customer_id,"recency_days":recency,"frequency":frequency,"monetary":monetary})
    rfm=kmeans(rfm); write_csv(PROCESSED / "customer_rfm_segments.csv", rfm)
    city = cur.execute("SELECT ci.city_name, ROUND(SUM(f.total_sales),2) FROM fact_sales f JOIN dim_store s ON f.store_key=s.store_key JOIN dim_city ci ON s.city_key=ci.city_key GROUP BY ci.city_name ORDER BY 2 DESC").fetchall()
    line = cur.execute("SELECT pl.product_line, ROUND(SUM(f.total_sales),2) FROM fact_sales f JOIN dim_product p ON f.product_key=p.product_key JOIN dim_product_line pl ON p.product_line_key=pl.product_line_key GROUP BY pl.product_line ORDER BY 2 DESC").fetchall()
    segment = sorted(((name, sum(float(r['monetary']) for r in rfm if r['segment']==name)) for name in ["High Value","Regular","Occasional","At Risk"]), key=lambda x:x[1], reverse=True)
    svg_bar(VIZ / "revenue_by_city.svg", "Revenue by City", city); svg_bar(VIZ / "revenue_by_product_line.svg", "Revenue by Product Line", line, "#059669"); svg_bar(VIZ / "revenue_by_segment.svg", "Revenue by Customer Segment", segment, "#9333ea")
    total = cur.execute("SELECT ROUND(SUM(total_sales),2) FROM fact_sales").fetchone()[0]; top_city=city[0]; top_line=line[0]
    q = cur.execute("SELECT payment_method, COUNT(*) FROM fact_sales f JOIN dim_payment p ON f.payment_key=p.payment_key GROUP BY payment_method ORDER BY 2 DESC").fetchall()
    report = f"# Supermarket Sales Analysis\n\n## Warehouse load\n\n- Source rows: 1,801; loaded fact rows: {len(sales):,}\n- Data-quality actions: {quality}\n- Dimensions: 7; schema: Snowflake (product-line and city outriggers)\n\n## Executive findings\n\n- Total revenue: **${total:,.2f}**\n- Highest-revenue city: **{top_city[0]} (${top_city[1]:,.2f})**\n- Highest-revenue product line: **{top_line[0]} (${top_line[1]:,.2f})**\n- Most used payment method: **{q[0][0]} ({q[0][1]:,} transactions)**\n\n## Customer segmentation\n\nRFM features were standardised and clustered with K-Means (k=4). Segment labels are assigned from the average monetary value of each cluster. See `data/processed/customer_rfm_segments.csv`.\n\n| Segment | Revenue |\n|---|---:|\n" + "\n".join(f"| {name} | ${value:,.2f} |" for name,value in segment) + "\n\n## OLAP\n\nReusable roll-up, slice, and dice queries are in `sql/olap_queries.sql`. Charts are in `outputs/visualizations/`.\n"
    (OUT / "analysis_report.md").write_text(report, encoding="utf-8"); con.close()
    print("Pipeline complete. See outputs/analysis_report.md")

if __name__ == "__main__": main()

