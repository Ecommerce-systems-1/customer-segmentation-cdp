import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.getenv("DB_PATH", ":memory:")

_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    segment TEXT,
    cluster_id INTEGER,
    rfm_recency INTEGER,
    rfm_frequency INTEGER,
    rfm_monetary REAL
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id, order_date);
"""

FIRST = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack"]
LAST = ["Smith", "Jones", "Chen", "Patel", "Garcia", "Kim", "Muller", "Rossi", "Silva", "Novak"]

# (min_orders, max_orders, min_days_ago, max_days_ago, min_amount, max_amount)
BEHAVIOR_PROFILES = [
    (8, 15, 1, 10, 80, 300),    # champions: frequent, recent, big spenders
    (4, 8, 5, 25, 40, 150),     # loyal
    (2, 4, 30, 55, 30, 120),    # at-risk: used to buy, going quiet
    (1, 2, 55, 80, 15, 80),     # hibernating
    (0, 1, 80, 89, 10, 50),     # lost
]


def _seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] > 0:
        return
    rng = random.Random(42)
    today = date.today()
    for i in range(1, 201):
        cid = f"cust-{i:04d}"
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        profile = BEHAVIOR_PROFILES[(i - 1) % len(BEHAVIOR_PROFILES)]
        created = (today - timedelta(days=rng.randint(90, 720))).isoformat()
        conn.execute(
            "INSERT INTO customers (id, name, email, created_at) VALUES (?,?,?,?)",
            (cid, name, f"{cid}@example.com", created),
        )
        min_o, max_o, min_d, max_d, min_a, max_a = profile
        for _ in range(rng.randint(min_o, max_o)):
            order_date = (today - timedelta(days=rng.randint(min_d, max_d))).isoformat()
            conn.execute(
                "INSERT INTO orders (customer_id, order_date, total_amount) VALUES (?,?,?)",
                (cid, order_date, round(rng.uniform(min_a, max_a), 2)),
            )
    conn.commit()


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if DB_PATH != ":memory:":
            os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        _seed(_conn)
    return _conn
