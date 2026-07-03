import time
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.services.rfm_calculator import RFMCalculator
from app.services.rfm_normalizer import RFMNormalizer
from app.services.clusterer import KMeansClusterer, SEGMENT_LABELS

router = APIRouter(prefix="/api", tags=["customers"])

_calculator = RFMCalculator()
_normalizer = RFMNormalizer()
_clusterer = KMeansClusterer()


def refresh_segments() -> dict:
    db = get_db()
    start = time.perf_counter()
    rfm_data = _calculator.compute_all(db, date.today())
    rfm_data = _normalizer.normalize(rfm_data)
    rfm_data = _clusterer.cluster(rfm_data)
    for r in rfm_data:
        db.execute(
            "UPDATE customers SET segment=?, cluster_id=?, rfm_recency=?, rfm_frequency=?, rfm_monetary=? WHERE id=?",
            (r.get("segment"), r.get("cluster_id"), r["recency"], r["frequency"],
             r["monetary"], r["customer_id"]),
        )
    db.commit()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    return {"time_taken_ms": elapsed_ms, "segments": _segment_summary()}


def _segment_summary() -> list[dict]:
    db = get_db()
    rows = db.execute(
        """SELECT segment, COUNT(*) AS size,
                  ROUND(AVG(rfm_recency), 1) AS avg_recency,
                  ROUND(AVG(rfm_frequency), 1) AS avg_frequency,
                  ROUND(AVG(rfm_monetary), 2) AS avg_monetary
           FROM customers WHERE segment IS NOT NULL
           GROUP BY segment"""
    ).fetchall()
    by_name = {r["segment"]: dict(r) for r in rows}
    return [
        by_name.get(label, {"segment": label, "size": 0, "avg_recency": None,
                            "avg_frequency": None, "avg_monetary": None})
        for label in SEGMENT_LABELS
    ]


@router.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Customer not found")
    return dict(row)


@router.get("/customers")
def list_customers(
    segment: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    db = get_db()
    where, params = ("WHERE segment=?", [segment]) if segment else ("", [])
    total = db.execute(f"SELECT COUNT(*) FROM customers {where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM customers {where} ORDER BY id LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return {"total": total, "page": page, "page_size": page_size,
            "customers": [dict(r) for r in rows]}


@router.get("/segments")
def get_segments():
    return _segment_summary()


@router.post("/segments/refresh")
def post_refresh():
    return refresh_segments()
