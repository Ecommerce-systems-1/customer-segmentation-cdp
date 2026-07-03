from datetime import date, timedelta

class RFMCalculator:
    def __init__(self, window_days: int = 90):
        self.window_days = window_days

    def compute_for_customer(self, db, customer_id: str, reference_date: date) -> dict:
        cutoff = (reference_date - timedelta(days=self.window_days)).isoformat()
        ref_str = reference_date.isoformat()
        last_order = db.execute(
            "SELECT MAX(order_date) FROM orders WHERE customer_id=? AND order_date<=?",
            (customer_id, ref_str)
        ).fetchone()[0]
        recency = None
        if last_order:
            last_dt = date.fromisoformat(last_order)
            recency = (reference_date - last_dt).days
        row = db.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM orders WHERE customer_id=? AND order_date>=? AND order_date<=?",
            (customer_id, cutoff, ref_str)
        ).fetchone()
        return {"recency": recency, "frequency": row[0], "monetary": float(row[1])}

    def compute_all(self, db, reference_date: date) -> list[dict]:
        customers = db.execute("SELECT id FROM customers").fetchall()
        results = []
        for (cid,) in customers:
            rfm = self.compute_for_customer(db, cid, reference_date)
            rfm["customer_id"] = cid
            results.append(rfm)
        return results