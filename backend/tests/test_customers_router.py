from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_customer_profile():
    resp = client.get("/api/customers/cust-0001")
    assert resp.status_code == 200
    data = resp.json()
    assert "segment" in data
    assert "rfm_recency" in data
    assert data["segment"] in ["Champions","Loyal Customers","At-Risk","Hibernating","Lost"]

def test_unknown_customer_404():
    resp = client.get("/api/customers/does-not-exist")
    assert resp.status_code == 404

def test_get_segments():
    resp = client.get("/api/segments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert all("size" in s and "avg_recency" in s for s in data)

def test_refresh_segments():
    resp = client.post("/api/segments/refresh")
    assert resp.status_code == 200
    assert "time_taken_ms" in resp.json()
    assert "segments" in resp.json()

def test_filter_by_segment():
    resp = client.get("/api/customers?segment=Champions&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert all(c["segment"] == "Champions" for c in data["customers"])