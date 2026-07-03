# Data Model — B2B Customer Segmentation & Churn Predictor

Five tables: one static profile table (`accounts`) and four dynamic interaction tables. Persisted model outputs live on `accounts`.

```sql
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,                -- acct-0001
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL,             -- Finance | Healthcare | Retail | Manufacturing | Media | Technology | Logistics | Education
    size_tier TEXT NOT NULL,            -- Large | Medium | Small
    annual_revenue REAL NOT NULL,       -- USD
    employees INTEGER NOT NULL,
    signup_date TEXT NOT NULL,          -- ISO date → tenure
    contract_type TEXT NOT NULL,        -- monthly | annual
    plan_tier TEXT NOT NULL,            -- basic | standard | enterprise
    mrr REAL NOT NULL,                  -- monthly recurring revenue, USD
    nps_score INTEGER,                  -- -100..100 (account-level survey)
    loyalty_tier TEXT NOT NULL,         -- bronze | silver | gold | platinum
    churned INTEGER NOT NULL DEFAULT 0, -- ground-truth label used for training

    -- persisted pipeline outputs
    segment TEXT,
    cluster_id INTEGER,
    rfm_recency INTEGER,
    rfm_frequency INTEGER,
    rfm_monetary REAL,
    clv REAL,                           -- mrr * tenure months
    churn_probability REAL,             -- 0..1
    churn_risk_band TEXT,               -- Low | Medium | High | Critical
    churn_drivers TEXT                  -- JSON array of top-3 driver strings
);

CREATE TABLE IF NOT EXISTS service_orders (      -- cloud service purchases → RFM
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    service_type TEXT NOT NULL,          -- compute | storage | database | ml | security | networking
    order_date TEXT NOT NULL,
    amount REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_account ON service_orders(account_id, order_date);

CREATE TABLE IF NOT EXISTS usage_metrics (       -- monthly product engagement
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    month TEXT NOT NULL,                 -- YYYY-MM, last 6 months per account
    logins INTEGER NOT NULL,
    active_users INTEGER NOT NULL,
    utilization_rate REAL NOT NULL,      -- 0..1, purchased capacity actually used
    features_adopted INTEGER NOT NULL    -- count of product features in use
);
CREATE INDEX IF NOT EXISTS idx_usage_account ON usage_metrics(account_id, month);

CREATE TABLE IF NOT EXISTS support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    opened_date TEXT NOT NULL,
    severity TEXT NOT NULL,              -- low | medium | high | critical
    resolution_hours REAL,
    escalated INTEGER NOT NULL DEFAULT 0,
    csat_score INTEGER                   -- 1..5
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
```

## Feature vector (built by `feature_builder.py`)

| Category | Features |
|---|---|
| Behavioral | `frequency`, `monetary`, `avg_order_value`, `login_trend` (last 3 mo vs prior 3), `features_adopted` |
| Status & tenure | `recency`, `tenure_days`, `clv`, `loyalty_ordinal` |
| Firmographic | `size_ordinal` (Small=0 … Large=2), `revenue_log`, `employees_log` |
| Support | `tickets_per_month`, `avg_resolution_hours`, `escalation_rate`, `avg_csat`, `nps`, `late_payment_rate` |
| Product & contract | `utilization_rate`, `is_monthly_contract` |

## Seed archetypes (~300 accounts, `random.Random(42)`)

| Archetype | Share | Signature | churned |
|---|---|---|---|
| Healthy champion | ~20% | frequent recent orders, high utilization, few tickets, annual contract, high NPS | 0 |
| Steady adopter | ~25% | regular orders, moderate usage, normal support load | 0 |
| New / onboarding | ~15% | short tenure, ramping usage, some tickets (onboarding friction) | 0 |
| At-risk (retained) | ~15% | declining logins, rising tickets, monthly contract, low utilization | 0 |
| Churned | ~25% | same signature as at-risk but stronger: stale orders, very low utilization, heavy escalated tickets, late payments, low NPS | 1 |

Noise is injected in every archetype so the label is learnable but not linearly separable (target holdout AUC > 0.8, not 1.0).
