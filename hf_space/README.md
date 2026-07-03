---
title: Customer Segmentation CDP
emoji: 🧩
colorFrom: purple
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Customer Segmentation CDP

200 synthetic customers scored on Recency/Frequency/Monetary and clustered into 5 segments with KMeans.

The landing page is an interactive API console — click any endpoint to call the live API.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/segments` | Segment summary |
| GET | `/api/customers?segment=X` | Customers in a segment |
| GET | `/api/customers/{id}` | Customer profile |
| POST | `/api/segments/refresh` | Re-run clustering |

## Stack

Python 3.11 · FastAPI · SQLite · Pydantic v2 · Next.js 14 (static export) · Tailwind CSS · Docker
