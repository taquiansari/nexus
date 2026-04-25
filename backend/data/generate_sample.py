"""
Generate a sample messy sales CSV for demo purposes.
Run this script to create the sample_sales.csv file.
"""
import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Food & Beverage"]
PRODUCTS = {
    "Electronics": ["Wireless Headphones", "USB-C Hub", "Smart Watch", "Bluetooth Speaker", "Laptop Stand"],
    "Clothing": ["Running Shoes", "Winter Jacket", "Cotton T-Shirt", "Denim Jeans", "Wool Sweater"],
    "Home & Garden": ["LED Desk Lamp", "Plant Pot Set", "Air Purifier", "Kitchen Scale", "Throw Blanket"],
    "Sports": ["Yoga Mat", "Resistance Bands", "Water Bottle", "Jump Rope", "Foam Roller"],
    "Books": ["Python Cookbook", "Design Patterns", "AI Fundamentals", "Data Science Guide", "Web Dev Manual"],
    "Food & Beverage": ["Organic Coffee", "Protein Bars", "Green Tea Set", "Dark Chocolate", "Trail Mix"],
}
REGIONS = ["North", "South", "East", "West", "Central", None, None]  # Some nulls

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]  # Intentionally inconsistent

def generate_sample_data():
    rows = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)

    for i in range(1, 501):
        # Random date in 2025
        days_offset = random.randint(0, (end_date - start_date).days)
        date = start_date + timedelta(days=days_offset)

        # Randomly pick date format (messy!)
        date_str = date.strftime(random.choice(DATE_FORMATS))

        category = random.choice(CATEGORIES)
        product = random.choice(PRODUCTS[category])
        quantity = random.randint(1, 20)
        unit_price = round(random.uniform(5.0, 500.0), 2)
        revenue = round(quantity * unit_price, 2)
        region = random.choice(REGIONS)

        # Introduce messiness
        row = {
            "transaction_id": f"TXN-{i:04d}",
            "date": date_str,
            "product": product,
            "category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "revenue": revenue,
            "region": region if region else "",
        }

        # Randomly null out some fields (5% chance)
        if random.random() < 0.05:
            row["quantity"] = ""
        if random.random() < 0.05:
            row["unit_price"] = ""
        if random.random() < 0.03:
            row["revenue"] = ""

        # Add some duplicates (~4% chance)
        rows.append(row)
        if random.random() < 0.04:
            rows.append(dict(row))  # Exact duplicate

        # Add some outliers — zero revenue
        if random.random() < 0.02:
            outlier = dict(row)
            outlier["transaction_id"] = f"TXN-{i:04d}-X"
            outlier["revenue"] = 0.0
            rows.append(outlier)

    return rows

if __name__ == "__main__":
    data = generate_sample_data()
    output_path = os.path.join(os.path.dirname(__file__), "sample_sales.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["transaction_id", "date", "product", "category", "quantity", "unit_price", "revenue", "region"])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} rows → {output_path}")
