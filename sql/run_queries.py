"""
Loads data/*.csv into a fresh SQLite database using schema.sql, then runs
every numbered query in queries.sql and prints/saves the results.

Run:
    python3 sql/run_queries.py

Writes sql/sample_output.txt (the query results, for reference without
needing to run anything) and data/ecommerce_sales_analytics.sqlite.
"""

import os
import re
import sqlite3

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "ecommerce_sales_analytics.sqlite")

TABLES = ["customers", "employees", "products", "orders", "order_items"]


def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.join(HERE, "schema.sql"), encoding="utf-8") as f:
        conn.executescript(f.read())
    for table in TABLES:
        df = pd.read_csv(os.path.join(DATA_DIR, f"{table}.csv"))
        df.to_sql(table, conn, if_exists="append", index=False)
    conn.commit()
    return conn


def split_queries(sql_text):
    """Split queries.sql into (comment_label, sql) blocks on '-- N.' markers."""
    blocks = re.split(r"\n(?=-- \d+\.)", sql_text.strip())
    parsed = []
    for block in blocks:
        lines = block.strip().splitlines()
        label_lines = [l for l in lines if l.startswith("--")]
        label = label_lines[0].lstrip("- ").strip() if label_lines else "query"
        sql = "\n".join(l for l in lines if not l.startswith("--")).strip()
        if sql:
            parsed.append((label, sql))
    return parsed


def main():
    conn = build_database()
    with open(os.path.join(HERE, "queries.sql"), encoding="utf-8") as f:
        queries = split_queries(f.read())

    out_lines = []
    for label, sql in queries:
        header = f"\n=== {label} ===\n"
        df = pd.read_sql_query(sql, conn)
        block = header + df.to_string(index=False) + "\n"
        print(block)
        out_lines.append(block)

    with open(os.path.join(HERE, "sample_output.txt"), "w", encoding="utf-8") as f:
        f.write("".join(out_lines))

    conn.close()
    print(f"\nWrote {DB_PATH}")
    print(f"Wrote {os.path.join(HERE, 'sample_output.txt')}")


if __name__ == "__main__":
    main()
