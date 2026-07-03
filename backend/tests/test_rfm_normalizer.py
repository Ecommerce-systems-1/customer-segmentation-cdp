import pytest
from app.services.rfm_normalizer import RFMNormalizer

def test_normalizer_scales_to_0_1():
    data = [
        {"customer_id": "c1", "recency": 10, "frequency": 5, "monetary": 500},
        {"customer_id": "c2", "recency": 100, "frequency": 1, "monetary": 50},
    ]
    norm = RFMNormalizer()
    result = norm.normalize(data)
    assert result[0]["rfm_r_norm"] == pytest.approx(0.0)   # lower recency = better; normalized inverted
    assert result[1]["rfm_r_norm"] == pytest.approx(1.0)   # higher recency = worse
    assert result[0]["rfm_f_norm"] == pytest.approx(1.0)
    assert result[1]["rfm_f_norm"] == pytest.approx(0.0)

def test_normalizer_handles_zero_range():
    data = [{"customer_id": "c1", "recency": 5, "frequency": 3, "monetary": 100}] * 3
    norm = RFMNormalizer()
    result = norm.normalize(data)
    # All same value → normalized to 0.5 (or 0, acceptable)
    assert all(0 <= r["rfm_r_norm"] <= 1 for r in result)