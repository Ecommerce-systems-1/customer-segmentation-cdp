import sqlite3, pytest
from datetime import date, timedelta
from app.services.rfm_calculator import RFMCalculator

@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("CREATE TABLE orders (id TEXT PRIMARY KEY, customer_id TEXT, order_date TEXT, total_amount REAL, category TEXT)")
    conn.execute("INSERT INTO customers VALUES ('c1','Alice','alice@x.com')")
    today = date.today().isoformat()
    five_days_ago = (date.today() - timedelta(days=5)).isoformat()
    ten_days_ago  = (date.today() - timedelta(days=10)).isoformat()
    conn.execute("INSERT INTO orders VALUES ('o1','c1',?,50,'electronics')", (five_days_ago,))
    conn.execute("INSERT INTO orders VALUES ('o2','c1',?,100,'clothing')", (ten_days_ago,))
    conn.commit()
    yield conn
    conn.close()

def test_recency_is_days_since_last_order(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_customer(db, "c1", reference_date=date.today())
    assert rfm["recency"] == 5  # 5 days since last order

def test_frequency_counts_orders_in_90_days(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_customer(db, "c1", reference_date=date.today())
    assert rfm["frequency"] == 2

def test_monetary_sums_spend_in_90_days(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_customer(db, "c1", reference_date=date.today())
    assert rfm["monetary"] == pytest.approx(150.0)

def test_customer_with_no_orders_returns_zeros(db):
    db.execute("INSERT INTO customers VALUES ('c2','Bob','bob@x.com')")
    db.commit()
    calc = RFMCalculator()
    rfm = calc.compute_for_customer(db, "c2", reference_date=date.today())
    assert rfm["recency"] is None
    assert rfm["frequency"] == 0
    assert rfm["monetary"] == 0