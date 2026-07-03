# Architecture — B2B Customer Segmentation & Churn Predictor

FastAPI + SQLite + scikit-learn backend, Next.js 14 endpoint-explorer frontend.

## Pipeline

```
seed (database.py)
  └─ synthetic B2B accounts + service_orders + usage_metrics + support_tickets + invoices
        │
        ▼
feature_builder.py ── per-account feature vector across the 5 parameter categories
        │                (RFM via rfm_calculator.py over service_orders, tenure, CLV,
        │                 firmographics, support load, NPS, payment history,
        │                 login trend, utilization, contract type)
        ├──────────────────────────────┐
        ▼                              ▼
rfm_normalizer.py               churn_model.py
(min-max any named features)    (LogisticRegression, 75/25 split,
        │                        churn probability + risk band +
        ▼                        top-3 named drivers, AUC/precision/recall)
clusterer.py                           │
(KMeans → 5 B2B segments)              │
        └──────────────┬───────────────┘
                       ▼
              accounts table (persisted scores)
                       ▼
              routers/accounts.py (REST API)
                       ▼
              frontend/pages/index.tsx (endpoint explorer)
```

## Components

| Component | Responsibility |
|---|---|
| `app/database.py` | Schema, singleton connection, deterministic synthetic seed (archetype-driven, `random.Random(42)`) |
| `app/services/rfm_calculator.py` | Recency / frequency / monetary over `service_orders`, 90-day window |
| `app/services/feature_builder.py` | Assembles the full feature dict per account (all five categories) |
| `app/services/rfm_normalizer.py` | Min-max normalization of any named feature list |
| `app/services/clusterer.py` | KMeans over normalized features; ranked-centroid labeling into 5 B2B segments |
| `app/services/churn_model.py` | Trains logistic regression on `churned` labels; scores all accounts; drivers + holdout metrics |
| `app/routers/accounts.py` | REST API + `refresh_scores()` orchestrator |
| `app/main.py` | App wiring, CORS, `/health`, static frontend mount |

## API surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + counts |
| GET | `/api/accounts` | list; filters: segment, size_tier, industry, risk_band; paginated |
| GET | `/api/accounts/{id}` | full profile incl. churn probability + drivers |
| GET | `/api/segments` | per-segment size, avg CLV, avg churn probability |
| GET | `/api/churn/summary` | accounts per risk band + top at-risk accounts |
| GET | `/api/churn/model` | AUC, precision, recall, top global coefficients |
| POST | `/api/refresh` | recompute features → segments → churn scores |

## Key decisions

- **SQLite in-memory by default** (`DB_PATH` env overrides) — zero-setup demo, same pattern as before the elevation.
- **Logistic regression over gradient boosting** — interpretability is a business requirement (BR-3); coefficients × standardized feature values give per-account drivers directly.
- **Training at refresh time** — the model retrains on each refresh (~300 rows, sub-second); no model persistence needed at this scale.
- **Startup scoring on import** — mirrors the previous `refresh_segments()` on-import behavior so tests using `TestClient` see scored data without lifespan events.
