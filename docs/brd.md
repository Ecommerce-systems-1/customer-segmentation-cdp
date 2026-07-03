# BRD — B2B Customer Segmentation & Churn Predictor

## Business context

We are a cloud-services provider. Customers are companies (Large / Medium / Small size tiers, multiple industries) that purchase cloud services (compute, storage, database, ML, security, networking) on monthly or annual contracts and contact technical support to resolve issues. This system segments those accounts and predicts which are likely to churn, using five parameter categories: behavioral, customer status & tenure, firmographic, service & support interactions, and product & contract usage.

## Business requirements

### BR-1: Account segmentation
- Every account is clustered into one of five segments: **Strategic Champions, Steady Adopters, Growing Accounts, At-Risk, Dormant**.
- Clustering uses normalized features spanning RFM (over service orders), utilization, and support load — not RFM alone.
- Segment summary reports size, average CLV, and average churn probability per segment.

### BR-2: Churn prediction
- Every account receives a churn probability in [0, 1] from an interpretable classifier (logistic regression) trained on labeled historical outcomes.
- Probability maps to a risk band: **Low (<0.25), Medium (<0.50), High (<0.75), Critical (≥0.75)**.
- Each account exposes its **top 3 churn drivers** in human-readable form (e.g., "Login activity declining", "Support ticket rate above average", "Month-to-month contract").

### BR-3: Model transparency
- Model quality metrics — **AUC, precision, recall** on a held-out set — are exposed via the API.
- Global feature coefficients are exposed so users can inspect what the model has learned.
- Acceptance: AUC > 0.8 on the synthetic holdout; ≥80% of true churners fall in the High + Critical bands.

### BR-4: Query & filtering
- Accounts are listable and filterable by **segment, size tier, industry, and risk band**, with pagination.
- Individual account view returns the full profile: firmographics, contract, RFM scores, CLV, segment, churn probability, risk band, and drivers.

### BR-5: Refresh on demand
- A single API call recomputes features → segments → churn scores for all accounts and reports timing.

### BR-6: Demonstration data
- The system self-seeds ~300 synthetic accounts with realistic archetypes (healthy champions, steady adopters, new/onboarding, at-risk, churned) whose churn labels correlate — with noise — to the documented indicators, so the model has learnable, non-trivial signal.

## Out of scope
- Real-data ingestion pipelines, authentication, multi-model comparison, B2C demographics (age/gender), automated outreach/actions.

## KPIs
| KPI | Target |
|---|---|
| Holdout AUC | > 0.8 |
| Churner capture in top-2 risk bands | ≥ 80% |
| Full refresh latency (300 accounts) | < 5 s |
| Accounts with named drivers | 100% |
