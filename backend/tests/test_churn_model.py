from datetime import date

import pytest

from app.database import get_db
from app.services.churn_model import ChurnModel, risk_band
from app.services.feature_builder import FeatureBuilder


@pytest.fixture(scope="module")
def scored_rows():
    rows = FeatureBuilder().build_all(get_db(), date.today())
    model = ChurnModel()
    model.train(rows)
    return model, model.score_all(rows)


def test_holdout_auc_above_0_8(scored_rows):
    model, _ = scored_rows
    assert model.metrics["auc"] > 0.8


def test_probabilities_in_range(scored_rows):
    _, rows = scored_rows
    assert all(0.0 <= r["churn_probability"] <= 1.0 for r in rows)


def test_risk_band_boundaries():
    assert risk_band(0.1) == "Low"
    assert risk_band(0.25) == "Medium"
    assert risk_band(0.5) == "High"
    assert risk_band(0.75) == "Critical"
    assert risk_band(0.99) == "Critical"


def test_bands_monotonic_with_probability(scored_rows):
    _, rows = scored_rows
    order = ["Low", "Medium", "High", "Critical"]
    for r in rows:
        assert r["churn_risk_band"] == risk_band(r["churn_probability"])
    ranked = sorted(rows, key=lambda r: r["churn_probability"])
    band_indices = [order.index(r["churn_risk_band"]) for r in ranked]
    assert band_indices == sorted(band_indices)


def test_high_risk_accounts_have_named_drivers(scored_rows):
    _, rows = scored_rows
    risky = [r for r in rows if r["churn_risk_band"] in ("High", "Critical")]
    assert risky, "seed data should produce high-risk accounts"
    for r in risky:
        assert 1 <= len(r["churn_drivers"]) <= 3
        assert all(isinstance(d, str) and d for d in r["churn_drivers"])


def test_churners_concentrate_in_top_bands(scored_rows):
    # BRD KPI: >=80% of true churners land in High or Critical
    _, rows = scored_rows
    churners = [r for r in rows if r["churned"] == 1]
    captured = [r for r in churners if r["churn_risk_band"] in ("High", "Critical")]
    assert len(captured) / len(churners) >= 0.8


def test_global_coefficients_exposed(scored_rows):
    model, _ = scored_rows
    coefs = model.global_coefficients()
    assert len(coefs) == 8
    assert all("feature" in c and "coefficient" in c for c in coefs)


def test_score_before_train_raises():
    with pytest.raises(RuntimeError):
        ChurnModel().score_all([])
