---
title: B2B Customer Segmentation & Churn Predictor
emoji: 🧩
colorFrom: purple
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
short_description: B2B account segmentation + interpretable churn scoring
---

# B2B Customer Segmentation & Churn Predictor

300 synthetic cloud-services accounts — Large/Medium/Small companies across industries — segmented with KMeans (RFM + utilization + support load) and churn-scored by an interpretable logistic-regression model with named risk drivers per account.

The landing page is an interactive API console — click any endpoint to call the live API.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/segments` | Segment summary (size, avg CLV, avg churn probability) |
| GET | `/api/accounts?segment=X&risk_band=Y` | Filtered accounts |
| GET | `/api/accounts/{id}` | Account profile with churn drivers |
| GET | `/api/churn/summary` | Risk-band distribution + top at-risk accounts |
| GET | `/api/churn/model` | AUC / precision / recall + coefficients |
| POST | `/api/refresh` | Recompute segments + churn scores |

## Stack

Python 3.11 · FastAPI · SQLite · scikit-learn · Pydantic v2 · Next.js 14 (static export) · Tailwind CSS · Docker
