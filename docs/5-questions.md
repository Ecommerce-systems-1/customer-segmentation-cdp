# 5-Questions — B2B Customer Segmentation & Churn Predictor

## 1. What problem are we solving?

Our company sells cloud services (compute, storage, database, ML, security, networking) to business customers — companies of all sizes (Large, Medium, Small) across many industries. These customers buy services on monthly or annual contracts and reach out to technical support when they hit issues.

Today we cannot answer two questions that decide our revenue:

1. **Who are our customers, really?** Accounts are treated uniformly regardless of size, industry, spend pattern, or engagement — so success, sales, and support effort is spread evenly instead of where it matters.
2. **Who is about to leave?** Churn is discovered only after cancellation. The early signals — declining logins, shrinking service purchases, rising support ticket volume, low utilization on a month-to-month contract — are all in our data, but nothing connects them into a warning.

Segmentation and churn prediction rely on combining **static customer profiles** with **dynamic interaction data**, across five parameter categories:

| Category | Signals |
|---|---|
| **Behavioral** | Purchase frequency, average order value, feature adoption, engagement; declining login rates are direct early churn indicators |
| **Customer status & tenure** | Subscription duration, customer lifetime value (CLV), loyalty tier, RFM (recency, frequency, monetary) scores |
| **Firmographic** | Company size tier, industry, annual revenue, employee count |
| **Service & support interactions** | Ticket frequency, resolution times, escalations, CSAT, NPS, billing/payment history; frequent complaints correlate with churn |
| **Product & contract usage** | Contract length (month-to-month vs annual), utilization rates, plan tier |

## 2. Who is it for?

- **Customer Success managers** — need each account's segment, health, and churn risk with named reasons, so outreach is targeted and timely.
- **Sales / account management** — need firmographic + value segments to prioritize expansion.
- **Support leadership** — needs to see which at-risk accounts are support-heavy so escalations get priority handling.
- **Leadership** — needs churn-risk distribution and segment-level CLV to forecast revenue retention.

## 3. What does success look like?

- Every account is assigned to one of five actionable segments computed from normalized behavioral + usage + support features (KMeans over the feature vector).
- Every account gets a churn probability (0–1), a risk band (Low / Medium / High / Critical), and its **top 3 named risk drivers** (e.g., "login activity declining", "support ticket rate above average").
- On the synthetic holdout set the model achieves **AUC > 0.8**, and ≥80% of true churners land in the top two risk bands.
- Segments and churn scores refresh on demand in one API call and are queryable by segment, size tier, industry, and risk band.

## 4. Why now / why us?

Retention economics dominate B2B cloud: acquiring a new account costs multiples of retaining one, and expansion revenue comes disproportionately from healthy long-tenure accounts. All five signal categories already exist in our operational data (orders, usage telemetry, tickets, invoices, contracts) — this project connects them.

## 5. What are the risks?

- **Correlation ≠ causation** — a spike in tickets can mean a growing account onboarding a new team, not one about to leave. Mitigation: interpretable model (logistic regression) whose drivers a human can sanity-check before acting.
- **Synthetic data realism** — the demo trains on generated data with planted churn patterns; real deployment would need re-training and re-validation on production data.
- **Class imbalance** — churners are a minority (~20–25% here, often less in production); metrics must include precision/recall, not accuracy alone.
- **Stale scores** — features drift; scores must be recomputable on demand (POST /api/refresh).
