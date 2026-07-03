import math
from datetime import date

from app.services.rfm_calculator import RFMCalculator

SIZE_ORDINAL = {"Small": 0, "Medium": 1, "Large": 2}
LOYALTY_ORDINAL = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 3}

# Order matters: this is the model's feature vector layout.
FEATURE_NAMES = [
    # behavioral
    "frequency", "monetary", "avg_order_value", "login_trend", "features_adopted",
    # status & tenure
    "recency", "tenure_days", "clv", "loyalty_ordinal",
    # firmographic
    "size_ordinal", "revenue_log", "employees_log",
    # service & support interactions
    "tickets_per_month", "avg_resolution_hours", "escalation_rate",
    "avg_csat", "nps", "late_payment_rate",
    # product & contract usage
    "utilization_rate", "is_monthly_contract",
]

# Human-readable driver text per feature, keyed by whether a higher value
# pushes churn risk up (True) or down (False) for that account.
DRIVER_TEXT = {
    "frequency": ("Order frequency above average", "Order frequency below average"),
    "monetary": ("Recent spend above average", "Recent spend below average"),
    "avg_order_value": ("Average order value above average", "Average order value below average"),
    "login_trend": ("Login activity rising", "Login activity declining"),
    "features_adopted": ("Broad feature adoption", "Low feature adoption"),
    "recency": ("Long gap since last order", "Recent purchase activity"),
    "tenure_days": ("Long-tenured account", "Short account tenure"),
    "clv": ("High customer lifetime value", "Low customer lifetime value"),
    "loyalty_ordinal": ("High loyalty tier", "Low loyalty tier"),
    "size_ordinal": ("Large company profile", "Small company profile"),
    "revenue_log": ("High company revenue", "Low company revenue"),
    "employees_log": ("Large workforce", "Small workforce"),
    "tickets_per_month": ("Support ticket rate above average", "Few support tickets"),
    "avg_resolution_hours": ("Slow ticket resolutions", "Fast ticket resolutions"),
    "escalation_rate": ("Frequent ticket escalations", "Rare ticket escalations"),
    "avg_csat": ("High support satisfaction", "Low support satisfaction"),
    "nps": ("Positive NPS", "Negative NPS"),
    "late_payment_rate": ("Late invoice payments", "On-time invoice payments"),
    "utilization_rate": ("High service utilization", "Low service utilization"),
    "is_monthly_contract": ("Month-to-month contract", "Annual contract"),
}


class FeatureBuilder:
    """Builds the per-account feature dict spanning all five parameter categories."""

    def __init__(self, window_days: int = 90):
        self.rfm = RFMCalculator(window_days=window_days)
        self.window_days = window_days

    def build_all(self, db, reference_date: date) -> list[dict]:
        return [self.build_for_account(db, dict(row), reference_date)
                for row in db.execute("SELECT * FROM accounts").fetchall()]

    def build_for_account(self, db, account: dict, reference_date: date) -> dict:
        aid = account["id"]
        rfm = self.rfm.compute_for_account(db, aid, reference_date)
        recency = rfm["recency"] if rfm["recency"] is not None else self.window_days
        frequency = rfm["frequency"]
        monetary = rfm["monetary"]

        tenure_days = (reference_date - date.fromisoformat(account["signup_date"])).days
        clv = account["mrr"] * max(1, tenure_days) / 30.0

        months = self._months_per_window()
        tickets = db.execute(
            """SELECT COUNT(*), COALESCE(AVG(resolution_hours),0), COALESCE(AVG(escalated),0),
                      COALESCE(AVG(csat_score),3)
               FROM support_tickets WHERE account_id=?""", (aid,)).fetchone()
        late = db.execute(
            "SELECT COALESCE(AVG(1 - paid_on_time),0) FROM invoices WHERE account_id=?",
            (aid,)).fetchone()[0]

        usage = db.execute(
            """SELECT logins, utilization_rate, features_adopted
               FROM usage_metrics WHERE account_id=? ORDER BY month""", (aid,)).fetchall()
        login_trend, utilization, features_adopted = self._usage_features(usage)

        return {
            "account_id": aid,
            "churned": account["churned"],
            "frequency": frequency,
            "monetary": monetary,
            "avg_order_value": monetary / frequency if frequency else 0.0,
            "login_trend": login_trend,
            "features_adopted": features_adopted,
            "recency": recency,
            "tenure_days": tenure_days,
            "clv": clv,
            "loyalty_ordinal": LOYALTY_ORDINAL.get(account["loyalty_tier"], 0),
            "size_ordinal": SIZE_ORDINAL.get(account["size_tier"], 0),
            "revenue_log": math.log10(max(1.0, account["annual_revenue"])),
            "employees_log": math.log10(max(1, account["employees"])),
            "tickets_per_month": tickets[0] / months,
            "avg_resolution_hours": float(tickets[1]),
            "escalation_rate": float(tickets[2]),
            "avg_csat": float(tickets[3]),
            "nps": account["nps_score"] if account["nps_score"] is not None else 0,
            "late_payment_rate": float(late),
            "utilization_rate": utilization,
            "is_monthly_contract": 1 if account["contract_type"] == "monthly" else 0,
        }

    def _months_per_window(self) -> float:
        return max(1.0, self.window_days / 30.0)

    @staticmethod
    def _usage_features(usage_rows) -> tuple[float, float, int]:
        if not usage_rows:
            return 1.0, 0.0, 0
        logins = [r["logins"] for r in usage_rows]
        half = max(1, len(logins) // 2)
        prior = sum(logins[:half]) / half
        recent = sum(logins[-half:]) / half
        trend = recent / prior if prior > 0 else 1.0
        utilization = sum(r["utilization_rate"] for r in usage_rows) / len(usage_rows)
        features_adopted = usage_rows[-1]["features_adopted"]
        return trend, utilization, features_adopted
