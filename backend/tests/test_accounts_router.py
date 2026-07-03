from fastapi.testclient import TestClient
from app.main import app
from app.services.clusterer import SEGMENT_LABELS

client = TestClient(app)

def test_get_account_profile():
    resp = client.get("/api/accounts/acct-0001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["segment"] in SEGMENT_LABELS
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["churn_risk_band"] in ["Low", "Medium", "High", "Critical"]
    assert isinstance(data["churn_drivers"], list)
    assert data["size_tier"] in ["Large", "Medium", "Small"]

def test_unknown_account_404():
    resp = client.get("/api/accounts/does-not-exist")
    assert resp.status_code == 404

def test_get_segments():
    resp = client.get("/api/segments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert all("size" in s and "avg_clv" in s and "avg_churn_probability" in s for s in data)

def test_refresh():
    resp = client.post("/api/refresh")
    assert resp.status_code == 200
    body = resp.json()
    assert "time_taken_ms" in body
    assert "segments" in body
    assert body["model"]["auc"] > 0.5

def test_filter_by_segment():
    resp = client.get("/api/accounts?segment=At-Risk&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert all(a["segment"] == "At-Risk" for a in data["accounts"])

def test_filter_by_risk_band_and_size():
    resp = client.get("/api/accounts?risk_band=Critical&size_tier=Small")
    assert resp.status_code == 200
    data = resp.json()
    assert all(a["churn_risk_band"] == "Critical" and a["size_tier"] == "Small"
               for a in data["accounts"])

def test_churn_summary():
    resp = client.get("/api/churn/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert [b["band"] for b in data["risk_bands"]] == ["Low", "Medium", "High", "Critical"]
    assert len(data["top_at_risk"]) == 10
    probs = [a["churn_probability"] for a in data["top_at_risk"]]
    assert probs == sorted(probs, reverse=True)

def test_churn_model_info():
    resp = client.get("/api/churn/model")
    assert resp.status_code == 200
    data = resp.json()
    assert {"auc", "precision", "recall"} <= set(data["metrics"])
    assert len(data["top_coefficients"]) > 0
