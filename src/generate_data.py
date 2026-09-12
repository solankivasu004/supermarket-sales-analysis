"""Create reproducible, realistic supermarket operational CSV files."""
from __future__ import annotations
import csv, random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
random.seed(20240912)

CITIES = [("S001", "A", "Delhi"), ("S002", "B", "Mumbai"), ("S003", "C", "Bengaluru")]
LINES = {
    "Groceries": [("Rice 5kg", 18.5), ("Olive Oil 1L", 12.0), ("Coffee 500g", 9.5)],
    "Health & Beauty": [("Shampoo", 7.0), ("Face Wash", 6.5), ("Vitamins", 14.0)],
    "Home & Lifestyle": [("Storage Box", 8.0), ("Desk Lamp", 22.0), ("Towels", 11.5)],
    "Electronic Accessories": [("USB Cable", 5.0), ("Power Bank", 25.0), ("Headphones", 18.0)],
    "Fashion Accessories": [("Wallet", 15.0), ("Scarf", 12.0), ("Watch", 35.0)],
    "Sports & Travel": [("Water Bottle", 9.0), ("Yoga Mat", 20.0), ("Travel Bag", 32.0)],
}
FIRST = ["Aarav", "Diya", "Kabir", "Ananya", "Rohan", "Isha", "Vikram", "Meera", "Arjun", "Nisha"]
LAST = ["Sharma", "Patel", "Khan", "Reddy", "Singh", "Das", "Gupta", "Iyer"]

def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    customers = []
    for i in range(1, 241):
        members = "Member" if i <= 150 else "Normal"
        customers.append({"customer_id": f"C{i:04d}", "customer_name": f"{random.choice(FIRST)} {random.choice(LAST)}",
                          "gender": random.choice(["Female", "Male"]), "member_type": members})
    products = []
    for line, items in LINES.items():
        for idx, (name, price) in enumerate(items, 1):
            products.append({"product_id": f"P{len(products)+1:03d}", "product_name": name, "product_line": line, "unit_price": price})
    stores = [{"store_id": sid, "branch": branch, "city": city} for sid, branch, city in CITIES]
    write_csv(RAW / "customers.csv", customers[0].keys(), customers)
    write_csv(RAW / "products.csv", products[0].keys(), products)
    write_csv(RAW / "stores.csv", stores[0].keys(), stores)

    # Higher activity and baskets for members provide meaningful segmentation.
    start = date(2024, 1, 1); sales = []
    for i in range(1, 1801):
        customer = random.choices(customers, weights=[3 if x["member_type"] == "Member" else 1 for x in customers])[0]
        product = random.choice(products); store = random.choice(stores)
        txn_date = start + timedelta(days=random.randrange(366)); quantity = random.choices([1,2,3,4,5], [42,30,16,8,4])[0]
        gross = round(float(product["unit_price"]) * quantity, 2); tax = round(gross * 0.05, 2)
        sales.append({"invoice_id": f"INV{i:05d}", "sale_date": txn_date.isoformat(), "customer_id": customer["customer_id"],
                      "product_id": product["product_id"], "store_id": store["store_id"], "quantity": quantity,
                      "gross_sales": gross, "tax": tax, "total_sales": round(gross + tax, 2),
                      "payment_method": random.choices(["Cash", "Card", "UPI"], [25,35,40])[0],
                      "rating": round(random.uniform(5.5, 10), 1)})
    # Deliberate realistic dirty records to demonstrate preprocessing.
    sales[12]["payment_method"] = ""; sales[34]["store_id"] = " s001 "; sales[67]["payment_method"] = "upi"
    sales[88]["quantity"] = 0; sales.append(sales[110].copy())  # duplicate invoice
    write_csv(RAW / "sales.csv", sales[0].keys(), sales)
    print(f"Created {len(customers)} customers, {len(products)} products, {len(stores)} stores, {len(sales)} source sales rows in {RAW}")

if __name__ == "__main__": main()

