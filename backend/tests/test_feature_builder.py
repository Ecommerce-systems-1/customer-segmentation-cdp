import sqlite3
from datetime import date, timedelta

import pytest

from app.database import SCHEMA
from app.services.feature_builder import FEATURE_NAMES, FeatureBuilder


@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    yield conn
    conn.close()


def _insert_account(db, aid="a1", **overrides):
    row = dict(
        id=aid, company_name="Acme Corp", industry="Finance", size_tier="Medium",
        annual_revenue=100e6, employees=500,
        signup_date=(date.today() - timedelta(days=365)).isoformat(),
        contract_type="monthly", plan_tier="standard", mrr=5000.0,
        nps_score=20, loyalty_tier="silver", churned=0,
    )
    row.update(overrides)
    db.execute(
        """INSERT INTO accounts (id, company_name, industry, size_tier, annual_revenue,
           employees, signup_date, contract_type, plan_tier, mrr, nps_score,
           loyalty_tier, churned) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        tuple(row.values()))
    db.commit()
    return row


def test_features_cover_all_five_categories(db):
    _insert_account(db)
    ten_days_ago = (date.today() - timedelta(days=10)).isoformat()
    db.execute("INSERT INTO service_orders (account_id, service_type, order_date, amount) VALUES ('a1','compute',?,8000)", (ten_days_ago,))
    db.execute("INSERT INTO usage_metrics (account_id, month, logins, active_users, utilization_rate, features_adopted) VALUES ('a1','2026-05',100,20,0.6,7)")
    db.execute("INSERT INTO usage_metrics (account_id, month, logins, active_users, utilization_rate, features_adopted) VALUES ('a1','2026-06',50,10,0.5,7)")
    db.execute("INSERT INTO support_tickets (account_id, opened_date, severity, resolution_hours, escalated, csat_score) VALUES ('a1',?, 'high', 48, 1, 2)", (ten_days_ago,))
    db.execute("INSERT INTO invoices (account_id, invoice_date, amount, paid_on_time) VALUES ('a1',?,5000,0)", (ten_days_ago,))
    db.commit()

    features = FeatureBuilder().build_all(db, date.today())
    assert len(features) == 1
    f = features[0]
    for name in FEATURE_NAMES:
        assert name in f, f"missing feature {name}"
    assert f["recency"] == 10                      # status & tenure
    assert f["monetary"] == pytest.approx(8000)    # behavioral
    assert f["size_ordinal"] == 1                  # firmographic
    assert f["escalation_rate"] == pytest.approx(1.0)   # support
    assert f["late_payment_rate"] == pytest.approx(1.0)
    assert f["is_monthly_contract"] == 1           # contract usage
    assert f["login_trend"] == pytest.approx(0.5)  # 50 recent vs 100 prior
    assert f["clv"] == pytest.approx(5000 * 365 / 30, rel=0.01)


def test_account_with_no_activity_gets_safe_defaults(db):
    _insert_account(db, aid="a2", contract_type="annual", nps_score=None)
    f = FeatureBuilder().build_for_account(
        db, dict(db.execute("SELECT * FROM accounts WHERE id='a2'").fetchone()), date.today())
    assert f["recency"] == 90          # no orders -> window cap, not None
    assert f["frequency"] == 0
    assert f["avg_order_value"] == 0.0
    assert f["tickets_per_month"] == 0.0
    assert f["login_trend"] == 1.0     # no usage data -> flat
    assert f["utilization_rate"] == 0.0
    assert f["nps"] == 0
    assert f["is_monthly_contract"] == 0
    # every model feature is numeric and non-None
    assert all(f[name] is not None for name in FEATURE_NAMES)
