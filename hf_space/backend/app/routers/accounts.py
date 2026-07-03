import json
import time
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.services.feature_builder import FeatureBuilder
from app.services.rfm_normalizer import RFMNormalizer
from app.services.clusterer import CLUSTER_FEATURES, KMeansClusterer, SEGMENT_LABELS
from app.services.churn_model import ChurnModel, RISK_BANDS

router = APIRouter(prefix="/api", tags=["accounts"])

_builder = FeatureBuilder()
_normalizer = RFMNormalizer()
_clusterer = KMeansClusterer()
_churn = ChurnModel()


def refresh_scores() -> dict:
    db = get_db()
    start = time.perf_counter()
    rows = _builder.build_all(db, date.today())
    rows = _normalizer.normalize(rows, features=tuple(CLUSTER_FEATURES))
    rows = _clusterer.cluster(rows)
    model_metrics = _churn.train(rows)
    rows = _churn.score_all(rows)
    for r in rows:
        db.execute(
            """UPDATE accounts SET segment=?, cluster_id=?, rfm_recency=?, rfm_frequency=?,
               rfm_monetary=?, clv=?, churn_probability=?, churn_risk_band=?, churn_drivers=?
               WHERE id=?""",
            (r.get("segment"), r.get("cluster_id"), r["recency"], r["frequency"],
             round(r["monetary"], 2), round(r["clv"], 2), r["churn_probability"],
             r["churn_risk_band"], json.dumps(r["churn_drivers"]), r["account_id"]),
        )
    db.commit()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    return {"time_taken_ms": elapsed_ms, "model": model_metrics,
            "segments": _segment_summary()}


def _segment_summary() -> list[dict]:
    db = get_db()
    rows = db.execute(
        """SELECT segment, COUNT(*) AS size,
                  ROUND(AVG(clv), 2) AS avg_clv,
                  ROUND(AVG(churn_probability), 3) AS avg_churn_probability
           FROM accounts WHERE segment IS NOT NULL
           GROUP BY segment"""
    ).fetchall()
    by_name = {r["segment"]: dict(r) for r in rows}
    return [
        by_name.get(label, {"segment": label, "size": 0, "avg_clv": None,
                            "avg_churn_probability": None})
        for label in SEGMENT_LABELS
    ]


def _account_dict(row) -> dict:
    d = dict(row)
    if d.get("churn_drivers"):
        d["churn_drivers"] = json.loads(d["churn_drivers"])
    return d


@router.get("/accounts/{account_id}")
def get_account(account_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Account not found")
    return _account_dict(row)


@router.get("/accounts")
def list_accounts(
    segment: str | None = None,
    size_tier: str | None = None,
    industry: str | None = None,
    risk_band: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    db = get_db()
    filters = {"segment": segment, "size_tier": size_tier,
               "industry": industry, "churn_risk_band": risk_band}
    clauses = [f"{col}=?" for col, v in filters.items() if v is not None]
    params = [v for v in filters.values() if v is not None]
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = db.execute(f"SELECT COUNT(*) FROM accounts {where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM accounts {where} ORDER BY id LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size],
    ).fetchall()
    return {"total": total, "page": page, "page_size": page_size,
            "accounts": [_account_dict(r) for r in rows]}


@router.get("/segments")
def get_segments():
    return _segment_summary()


@router.get("/churn/summary")
def churn_summary():
    db = get_db()
    rows = db.execute(
        """SELECT churn_risk_band, COUNT(*) AS size
           FROM accounts WHERE churn_risk_band IS NOT NULL
           GROUP BY churn_risk_band"""
    ).fetchall()
    by_band = {r["churn_risk_band"]: r["size"] for r in rows}
    top = db.execute(
        """SELECT id, company_name, size_tier, industry, segment,
                  churn_probability, churn_risk_band, churn_drivers
           FROM accounts WHERE churn_probability IS NOT NULL
           ORDER BY churn_probability DESC LIMIT 10"""
    ).fetchall()
    return {
        "risk_bands": [{"band": band, "size": by_band.get(band, 0)}
                       for _, band in RISK_BANDS],
        "top_at_risk": [_account_dict(r) for r in top],
    }


@router.get("/churn/model")
def churn_model_info():
    return {"metrics": _churn.metrics, "top_coefficients": _churn.global_coefficients()}


@router.post("/refresh")
def post_refresh():
    return refresh_scores()
