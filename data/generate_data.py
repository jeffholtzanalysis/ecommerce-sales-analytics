"""
Generates a reproducible, synthetic e-commerce sales dataset: customers,
employees, products, orders, and order line items for FY2025.

Simulates a mid-size online retailer selling office/electronics/home goods
through a small inside-sales team, with realistic order statuses
(completed / cancelled / returned), multi-item orders, and seasonal demand.

Run:
    python3 data/generate_data.py

Writes CSVs to data/: customers.csv, employees.csv, products.csv,
orders.csv, order_items.csv
"""

import os
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))

FIRST_NAMES = [
    "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley",
    "Daniel", "Megan", "Christopher", "Amanda", "Matthew", "Lauren", "Joshua",
    "Rachel", "Andrew", "Nicole", "Ryan", "Samantha",
]
LAST_NAMES = [
    "Miller", "Johnson", "Brown", "Davis", "Wilson", "Anderson", "Taylor",
    "Thomas", "Moore", "Jackson", "Martin", "Lee", "Harris", "Clark", "Lewis",
    "Walker", "Hall", "Allen", "Young", "King",
]
CITIES_STATES = [
    ("Chicago", "IL"), ("Milwaukee", "WI"), ("Madison", "WI"), ("Rockford", "IL"),
    ("Kenosha", "WI"), ("Janesville", "WI"), ("Beloit", "WI"), ("Racine", "WI"),
    ("Naperville", "IL"), ("Waukegan", "IL"), ("Green Bay", "WI"),
    ("Appleton", "WI"), ("Aurora", "IL"), ("Evanston", "IL"), ("Elgin", "IL"),
]

# (product_name, category, price, cost)
PRODUCT_TEMPLATES = [
    ("Wireless Mouse", "Electronics", 29.99, 14.00),
    ("Mechanical Keyboard", "Electronics", 89.99, 48.00),
    ("USB-C Hub", "Electronics", 44.99, 22.00),
    ("27-inch Monitor", "Electronics", 229.99, 145.00),
    ("Noise-Canceling Headset", "Electronics", 119.99, 62.00),
    ("Laptop Stand", "Office Supplies", 49.99, 24.00),
    ("Desk Organizer", "Office Supplies", 24.99, 10.00),
    ("Printer Paper Case", "Office Supplies", 39.99, 22.00),
    ("Ergonomic Office Chair", "Furniture", 249.99, 145.00),
    ("Standing Desk", "Furniture", 399.99, 235.00),
    ("Filing Cabinet", "Furniture", 179.99, 105.00),
    ("Bookshelf", "Furniture", 159.99, 88.00),
    ("Coffee Maker", "Home & Kitchen", 79.99, 42.00),
    ("Water Bottle", "Home & Kitchen", 19.99, 8.00),
    ("Desk Lamp", "Home & Kitchen", 34.99, 16.00),
    ("Backpack", "Accessories", 69.99, 31.00),
    ("Laptop Sleeve", "Accessories", 39.99, 17.00),
    ("Cable Management Kit", "Accessories", 22.99, 9.00),
    ("Webcam", "Electronics", 74.99, 38.00),
    ("Portable SSD", "Electronics", 129.99, 78.00),
]

EMPLOYEES = [
    (201, "Alex Carter", "Sales"), (202, "Morgan Reed", "Sales"),
    (203, "Taylor Brooks", "Sales"), (204, "Jordan Hayes", "Sales"),
    (205, "Casey Morgan", "Sales"), (206, "Jamie Parker", "Sales"),
    (207, "Riley Cooper", "Sales"), (208, "Drew Bennett", "Sales"),
]

N_CUSTOMERS = 200
N_ORDERS = 1800
ORDER_YEAR = 2025

# A handful of employees close noticeably more (and bigger) deals than the
# rest, so a sales-performance ranking has something to say.
EMPLOYEE_WEIGHTS = [3, 3, 2, 2, 1, 1, 1, 1]

# Monthly demand multiplier: Q4 holiday ramp + a small back-to-school bump,
# a January slump after the holidays.
MONTH_WEIGHTS = {
    1: 0.75, 2: 0.85, 3: 0.90, 4: 0.95, 5: 1.00, 6: 1.00,
    7: 0.95, 8: 1.05, 9: 1.10, 10: 1.15, 11: 1.45, 12: 1.65,
}


def build_customers():
    start_signup = date(2024, 1, 1)
    rows = []
    for cid in range(1001, 1001 + N_CUSTOMERS):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        city, state = random.choice(CITIES_STATES)
        signup = start_signup + timedelta(days=random.randint(0, 650))
        rows.append((cid, fn, ln, city, state, signup.isoformat()))
    return pd.DataFrame(
        rows,
        columns=["customer_id", "first_name", "last_name", "city", "state", "signup_date"],
    )


def build_products():
    rows = [
        (pid, name, cat, price, cost)
        for pid, (name, cat, price, cost) in enumerate(PRODUCT_TEMPLATES, start=101)
    ]
    return pd.DataFrame(rows, columns=["product_id", "product_name", "category", "price", "cost"])


def build_employees():
    return pd.DataFrame(EMPLOYEES, columns=["employee_id", "employee_name", "department"])


def weighted_order_date():
    """Pick a day in ORDER_YEAR, biased toward higher-weight months."""
    month = random.choices(list(MONTH_WEIGHTS.keys()), weights=list(MONTH_WEIGHTS.values()))[0]
    if month == 12:
        next_month = date(ORDER_YEAR + 1, 1, 1)
    else:
        next_month = date(ORDER_YEAR, month + 1, 1)
    days_in_month = (next_month - date(ORDER_YEAR, month, 1)).days
    return date(ORDER_YEAR, month, 1) + timedelta(days=random.randint(0, days_in_month - 1))


def build_orders_and_items(customers, products, employees):
    product_records = list(products.itertuples(index=False))
    employee_ids = [e[0] for e in EMPLOYEES]

    orders, order_items = [], []
    order_id = 50001
    item_id = 1
    for _ in range(N_ORDERS):
        customer_id = random.choice(customers["customer_id"].tolist())
        order_date = weighted_order_date()
        employee_id = random.choices(employee_ids, weights=EMPLOYEE_WEIGHTS)[0]

        r = random.random()
        status = "Completed" if r < 0.90 else ("Cancelled" if r < 0.96 else "Returned")

        orders.append((order_id, customer_id, employee_id, order_date.isoformat(), status))

        for _ in range(random.randint(1, 4)):
            product_id, name, cat, price, cost = random.choice(product_records)
            qty = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 12, 6, 2])[0]
            order_items.append((item_id, order_id, product_id, qty))
            item_id += 1
        order_id += 1

    orders_df = pd.DataFrame(
        orders, columns=["order_id", "customer_id", "employee_id", "order_date", "status"]
    )
    items_df = pd.DataFrame(
        order_items, columns=["order_item_id", "order_id", "product_id", "quantity"]
    )
    return orders_df, items_df


def main():
    customers = build_customers()
    products = build_products()
    employees = build_employees()
    orders, order_items = build_orders_and_items(customers, products, employees)

    customers.to_csv(os.path.join(HERE, "customers.csv"), index=False)
    employees.to_csv(os.path.join(HERE, "employees.csv"), index=False)
    products.to_csv(os.path.join(HERE, "products.csv"), index=False)
    orders.to_csv(os.path.join(HERE, "orders.csv"), index=False)
    order_items.to_csv(os.path.join(HERE, "order_items.csv"), index=False)

    print(f"customers:    {len(customers):>6,}")
    print(f"employees:    {len(employees):>6,}")
    print(f"products:     {len(products):>6,}")
    print(f"orders:       {len(orders):>6,}")
    print(f"order_items:  {len(order_items):>6,}")


if __name__ == "__main__":
    main()
