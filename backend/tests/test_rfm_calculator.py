import sqlite3
import pytest
from datetime import date, timedelta
from app.services.rfm_calculator import RFMCalculator

@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE accounts (id TEXT PRIMARY KEY, company_name TEXT)")
    conn.execute("CREATE TABLE service_orders (id TEXT PRIMARY KEY, account_id TEXT, service_type TEXT, order_date TEXT, amount REAL)")
    conn.execute("INSERT INTO accounts VALUES ('a1','Acme Corp')")
    five_days_ago = (date.today() - timedelta(days=5)).isoformat()
    ten_days_ago = (date.today() - timedelta(days=10)).isoformat()
    conn.execute("INSERT INTO service_orders VALUES ('o1','a1','compute',?,5000)", (five_days_ago,))
    conn.execute("INSERT INTO service_orders VALUES ('o2','a1','storage',?,10000)", (ten_days_ago,))
    conn.commit()
    yield conn
    conn.close()

def test_recency_is_days_since_last_order(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_account(db, "a1", reference_date=date.today())
    assert rfm["recency"] == 5  # 5 days since last service order

def test_frequency_counts_orders_in_90_days(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_account(db, "a1", reference_date=date.today())
    assert rfm["frequency"] == 2

def test_monetary_sums_spend_in_90_days(db):
    calc = RFMCalculator()
    rfm = calc.compute_for_account(db, "a1", reference_date=date.today())
    assert rfm["monetary"] == pytest.approx(15000.0)

def test_account_with_no_orders_returns_zeros(db):
    db.execute("INSERT INTO accounts VALUES ('a2','Globex Group')")
    db.commit()
    calc = RFMCalculator()
    rfm = calc.compute_for_account(db, "a2", reference_date=date.today())
    assert rfm["recency"] is None
    assert rfm["frequency"] == 0
    assert rfm["monetary"] == 0
