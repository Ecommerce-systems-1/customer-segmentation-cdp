import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.getenv("DB_PATH", ":memory:")

_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    size_tier TEXT NOT NULL,
    annual_revenue REAL NOT NULL,
    employees INTEGER NOT NULL,
    signup_date TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    plan_tier TEXT NOT NULL,
    mrr REAL NOT NULL,
    nps_score INTEGER,
    loyalty_tier TEXT NOT NULL,
    churned INTEGER NOT NULL DEFAULT 0,
    segment TEXT,
    cluster_id INTEGER,
    rfm_recency INTEGER,
    rfm_frequency INTEGER,
    rfm_monetary REAL,
    clv REAL,
    churn_probability REAL,
    churn_risk_band TEXT,
    churn_drivers TEXT
);
CREATE TABLE IF NOT EXISTS service_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    service_type TEXT NOT NULL,
    order_date TEXT NOT NULL,
    amount REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_account ON service_orders(account_id, order_date);
CREATE TABLE IF NOT EXISTS usage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    month TEXT NOT NULL,
    logins INTEGER NOT NULL,
    active_users INTEGER NOT NULL,
    utilization_rate REAL NOT NULL,
    features_adopted INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_account ON usage_metrics(account_id, month);
CREATE TABLE IF NOT EXISTS support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    opened_date TEXT NOT NULL,
    severity TEXT NOT NULL,
    resolution_hours REAL,
    escalated INTEGER NOT NULL DEFAULT 0,
    csat_score INTEGER
);
CREATE INDEX IF NOT EXISTS idx_tickets_account ON support_tickets(account_id, opened_date);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    invoice_date TEXT NOT NULL,
    amount REAL NOT NULL,
    paid_on_time INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_invoices_account ON invoices(account_id, invoice_date);
"""

INDUSTRIES = ["Finance", "Healthcare", "Retail", "Manufacturing", "Media",
              "Technology", "Logistics", "Education"]
SERVICE_TYPES = ["compute", "storage", "database", "ml", "security", "networking"]
COMPANY_STEMS = ["Acme", "Globex", "Initech", "Umbra", "Vertex", "Nimbus", "Quanta",
                 "Helix", "Orion", "Zenith", "Cobalt", "Aurora", "Summit", "Pioneer"]
COMPANY_SUFFIX = ["Corp", "Systems", "Group", "Labs", "Industries", "Solutions",
                  "Partners", "Holdings", "Networks", "Dynamics"]

# (size_tier, revenue range $M, employees range, mrr range, plan tiers)
SIZE_PROFILES = {
    "Large": ((500, 5000), (2000, 50000), (20000, 120000), ["enterprise"]),
    "Medium": ((50, 500), (200, 2000), (4000, 20000), ["standard", "enterprise"]),
    "Small": ((1, 50), (5, 200), (300, 4000), ["basic", "standard"]),
}

# Archetypes drive every dynamic signal. Ranges deliberately overlap between
# retained and churned so the label is learnable but not separable.
# Fields: weight, order count 90d, order recency days, login trend (recent/prior ratio),
# utilization, tickets 90d, escalation prob, csat, nps, on-time prob,
# annual-contract prob, tenure days, churned
ARCHETYPES = [
    dict(name="healthy_champion", weight=20, orders=(6, 14), recency=(1, 12),
         login_trend=(0.95, 1.30), util=(0.65, 0.95), tickets=(0, 3),
         escalate=0.05, csat=(4, 5), nps=(40, 90), on_time=0.98,
         annual=0.85, tenure=(400, 1400), churned=0),
    dict(name="steady_adopter", weight=25, orders=(3, 8), recency=(5, 30),
         login_trend=(0.85, 1.10), util=(0.45, 0.75), tickets=(1, 5),
         escalate=0.10, csat=(3, 5), nps=(10, 60), on_time=0.95,
         annual=0.60, tenure=(250, 900), churned=0),
    dict(name="new_onboarding", weight=15, orders=(1, 4), recency=(3, 25),
         login_trend=(1.05, 1.60), util=(0.20, 0.55), tickets=(2, 7),
         escalate=0.15, csat=(3, 5), nps=(0, 50), on_time=0.95,
         annual=0.40, tenure=(30, 180), churned=0),
    dict(name="at_risk", weight=15, orders=(1, 3), recency=(25, 60),
         login_trend=(0.45, 0.85), util=(0.15, 0.45), tickets=(4, 10),
         escalate=0.30, csat=(2, 4), nps=(-40, 20), on_time=0.85,
         annual=0.25, tenure=(200, 800), churned=0),
    dict(name="churned", weight=25, orders=(0, 2), recency=(45, 88),
         login_trend=(0.25, 0.70), util=(0.05, 0.35), tickets=(5, 14),
         escalate=0.45, csat=(1, 3), nps=(-80, 0), on_time=0.70,
         annual=0.15, tenure=(150, 900), churned=1),
]

SEVERITIES = ["low", "medium", "high", "critical"]
LOYALTY_BY_TENURE = [(1000, "platinum"), (600, "gold"), (300, "silver"), (0, "bronze")]


# Label noise so the churn signal is learnable but not perfectly separable:
# some at-risk accounts do churn, some churn-signature accounts get saved by
# intervention, and the occasional healthy account leaves without warning.
LABEL_FLIP = {"at_risk": 0.25, "churned": 0.12,
              "healthy_champion": 0.02, "steady_adopter": 0.02, "new_onboarding": 0.02}


def _label(rng: random.Random, arch: dict) -> int:
    churned = arch["churned"]
    if rng.random() < LABEL_FLIP[arch["name"]]:
        churned = 1 - churned
    return churned


def _pick_archetype(rng: random.Random) -> dict:
    total = sum(a["weight"] for a in ARCHETYPES)
    roll = rng.uniform(0, total)
    acc = 0
    for a in ARCHETYPES:
        acc += a["weight"]
        if roll <= acc:
            return a
    return ARCHETYPES[-1]


def _seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] > 0:
        return
    rng = random.Random(42)
    today = date.today()
    for i in range(1, 301):
        aid = f"acct-{i:04d}"
        arch = _pick_archetype(rng)
        size = rng.choices(["Large", "Medium", "Small"], weights=[2, 3, 5])[0]
        (rev_lo, rev_hi), (emp_lo, emp_hi), (mrr_lo, mrr_hi), plans = SIZE_PROFILES[size]
        tenure = rng.randint(*arch["tenure"])
        loyalty = next(t for cutoff, t in LOYALTY_BY_TENURE if tenure >= cutoff)
        conn.execute(
            """INSERT INTO accounts (id, company_name, industry, size_tier, annual_revenue,
               employees, signup_date, contract_type, plan_tier, mrr, nps_score,
               loyalty_tier, churned) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (aid,
             f"{rng.choice(COMPANY_STEMS)} {rng.choice(COMPANY_SUFFIX)}",
             rng.choice(INDUSTRIES), size,
             round(rng.uniform(rev_lo, rev_hi) * 1e6, 2),
             rng.randint(emp_lo, emp_hi),
             (today - timedelta(days=tenure)).isoformat(),
             "annual" if rng.random() < arch["annual"] else "monthly",
             rng.choice(plans),
             round(rng.uniform(mrr_lo, mrr_hi), 2),
             rng.randint(*arch["nps"]),
             loyalty, _label(rng, arch)),
        )
        _seed_orders(conn, rng, aid, arch, size, today)
        _seed_usage(conn, rng, aid, arch, size, today)
        _seed_tickets(conn, rng, aid, arch, today)
        _seed_invoices(conn, rng, aid, arch, today)
    conn.commit()


def _seed_orders(conn, rng, aid, arch, size, today):
    n_orders = rng.randint(*arch["orders"])
    scale = {"Large": 8.0, "Medium": 3.0, "Small": 1.0}[size]
    for k in range(n_orders):
        # first order sits at the archetype's recency; the rest spread older
        days_ago = rng.randint(*arch["recency"]) if k == 0 else rng.randint(arch["recency"][0], 89)
        conn.execute(
            "INSERT INTO service_orders (account_id, service_type, order_date, amount) VALUES (?,?,?,?)",
            (aid, rng.choice(SERVICE_TYPES),
             (today - timedelta(days=days_ago)).isoformat(),
             round(rng.uniform(500, 5000) * scale, 2)),
        )


def _seed_usage(conn, rng, aid, arch, size, today):
    base_logins = {"Large": 400, "Medium": 120, "Small": 30}[size]
    base_users = {"Large": 80, "Medium": 25, "Small": 6}[size]
    trend = rng.uniform(*arch["login_trend"])
    util = rng.uniform(*arch["util"])
    features = max(1, int(util * 12 + rng.randint(-2, 2)))
    # 6 months, oldest first; recent-3 vs prior-3 login ratio approximates `trend`
    for m in range(6, 0, -1):
        month = (today.replace(day=1) - timedelta(days=30 * (m - 1))).strftime("%Y-%m")
        ramp = trend ** ((6 - m) / 3)  # smooth drift toward the trend ratio
        conn.execute(
            "INSERT INTO usage_metrics (account_id, month, logins, active_users, utilization_rate, features_adopted) VALUES (?,?,?,?,?,?)",
            (aid, month,
             max(0, int(base_logins * ramp * rng.uniform(0.85, 1.15))),
             max(1, int(base_users * ramp * rng.uniform(0.85, 1.15))),
             round(min(1.0, max(0.0, util * rng.uniform(0.9, 1.1))), 3),
             features),
        )


def _seed_tickets(conn, rng, aid, arch, today):
    for _ in range(rng.randint(*arch["tickets"])):
        severity = rng.choices(SEVERITIES, weights=[4, 3, 2, 1])[0]
        base_hours = {"low": 8, "medium": 24, "high": 48, "critical": 72}[severity]
        # struggling accounts also wait longer for resolutions
        slow_factor = 1.6 if arch["churned"] else 1.0
        conn.execute(
            "INSERT INTO support_tickets (account_id, opened_date, severity, resolution_hours, escalated, csat_score) VALUES (?,?,?,?,?,?)",
            (aid, (today - timedelta(days=rng.randint(1, 89))).isoformat(),
             severity,
             round(base_hours * slow_factor * rng.uniform(0.5, 2.0), 1),
             1 if rng.random() < arch["escalate"] else 0,
             rng.randint(*arch["csat"])),
        )


def _seed_invoices(conn, rng, aid, arch, today):
    mrr = conn.execute("SELECT mrr FROM accounts WHERE id=?", (aid,)).fetchone()[0]
    for m in range(6):
        conn.execute(
            "INSERT INTO invoices (account_id, invoice_date, amount, paid_on_time) VALUES (?,?,?,?)",
            (aid, (today - timedelta(days=30 * m)).isoformat(),
             round(mrr * rng.uniform(0.95, 1.05), 2),
             1 if rng.random() < arch["on_time"] else 0),
        )


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
