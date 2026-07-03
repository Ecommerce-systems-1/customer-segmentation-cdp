from datetime import date, timedelta

class RFMCalculator:
    def __init__(self, window_days: int = 90):
        self.window_days = window_days

    def compute_for_account(self, db, account_id: str, reference_date: date) -> dict:
        cutoff = (reference_date - timedelta(days=self.window_days)).isoformat()
        ref_str = reference_date.isoformat()
        last_order = db.execute(
            "SELECT MAX(order_date) FROM service_orders WHERE account_id=? AND order_date<=?",
            (account_id, ref_str)
        ).fetchone()[0]
        recency = None
        if last_order:
            last_dt = date.fromisoformat(last_order)
            recency = (reference_date - last_dt).days
        row = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount),0) FROM service_orders WHERE account_id=? AND order_date>=? AND order_date<=?",
            (account_id, cutoff, ref_str)
        ).fetchone()
        return {"recency": recency, "frequency": row[0], "monetary": float(row[1])}

    def compute_all(self, db, reference_date: date) -> list[dict]:
        accounts = db.execute("SELECT id FROM accounts").fetchall()
        results = []
        for (aid,) in accounts:
            rfm = self.compute_for_account(db, aid, reference_date)
            rfm["account_id"] = aid
            results.append(rfm)
        return results