import pytest
from app.services.rfm_normalizer import RFMNormalizer

def test_normalizer_scales_to_0_1():
    data = [
        {"account_id": "a1", "recency": 10, "frequency": 5, "monetary": 500},
        {"account_id": "a2", "recency": 100, "frequency": 1, "monetary": 50},
    ]
    norm = RFMNormalizer()
    result = norm.normalize(data)
    assert result[0]["recency_norm"] == pytest.approx(0.0)   # raw min-max, direction handled downstream
    assert result[1]["recency_norm"] == pytest.approx(1.0)
    assert result[0]["frequency_norm"] == pytest.approx(1.0)
    assert result[1]["frequency_norm"] == pytest.approx(0.0)

def test_normalizer_handles_zero_range():
    data = [{"account_id": "a1", "recency": 5, "frequency": 3, "monetary": 100} for _ in range(3)]
    norm = RFMNormalizer()
    result = norm.normalize(data)
    # All same value -> scaled to a constant within [0, 1]
    assert all(0 <= r["recency_norm"] <= 1 for r in result)

def test_normalizer_accepts_custom_feature_list():
    data = [
        {"account_id": "a1", "utilization_rate": 0.9, "tickets_per_month": 0.5},
        {"account_id": "a2", "utilization_rate": 0.1, "tickets_per_month": 4.0},
    ]
    norm = RFMNormalizer()
    result = norm.normalize(data, features=("utilization_rate", "tickets_per_month"))
    assert result[0]["utilization_rate_norm"] == pytest.approx(1.0)
    assert result[1]["tickets_per_month_norm"] == pytest.approx(1.0)

def test_rows_missing_features_get_zero_norms():
    data = [
        {"account_id": "a1", "recency": 10, "frequency": 5, "monetary": 500},
        {"account_id": "a2", "recency": None, "frequency": 0, "monetary": 0},
    ]
    RFMNormalizer().normalize(data)
    assert data[1]["recency_norm"] == 0.0
    assert data[1]["frequency_norm"] == 0.0
