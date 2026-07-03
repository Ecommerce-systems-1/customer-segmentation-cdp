# B2B Customer Segmentation & Churn Predictor

Segments cloud-services business customers (Large/Medium/Small companies across industries) and predicts churn with an interpretable model. Combines static profiles with dynamic interaction data across five parameter categories: behavioral, status & tenure, firmographic, service & support interactions, and product & contract usage.

- KMeans segmentation over RFM + utilization + support-load features
- Logistic-regression churn scoring with risk bands and top-3 named drivers per account
- Holdout AUC / precision / recall exposed via API

Python · FastAPI · SQLite · scikit-learn · Next.js 14

Docs: [5-questions](docs/5-questions.md) · [BRD](docs/brd.md) · [Architecture](docs/architecture.md) · [Data model](docs/data-model.md)
