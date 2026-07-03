import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.services.feature_builder import DRIVER_TEXT, FEATURE_NAMES

RISK_BANDS = [(0.25, "Low"), (0.50, "Medium"), (0.75, "High"), (1.01, "Critical")]


def risk_band(probability: float) -> str:
    return next(band for cutoff, band in RISK_BANDS if probability < cutoff)


class ChurnModel:
    """Interpretable churn classifier: logistic regression over the feature
    vector from FeatureBuilder, with per-account probability, risk band, and
    top-3 named drivers derived from coefficient x standardized value."""

    def __init__(self, test_size: float = 0.25, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.scaler: StandardScaler | None = None
        self.model: LogisticRegression | None = None
        self.metrics: dict = {}

    def train(self, feature_rows: list[dict]) -> dict:
        X = np.array([[r[f] for f in FEATURE_NAMES] for r in feature_rows], dtype=float)
        y = np.array([r["churned"] for r in feature_rows], dtype=int)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y)
        self.scaler = StandardScaler().fit(X_train)
        self.model = LogisticRegression(max_iter=1000, random_state=self.random_state)
        self.model.fit(self.scaler.transform(X_train), y_train)

        probs = self.model.predict_proba(self.scaler.transform(X_test))[:, 1]
        preds = (probs >= 0.5).astype(int)
        self.metrics = {
            "auc": round(float(roc_auc_score(y_test, probs)), 3),
            "precision": round(float(precision_score(y_test, preds, zero_division=0)), 3),
            "recall": round(float(recall_score(y_test, preds, zero_division=0)), 3),
            "train_size": int(len(y_train)),
            "test_size": int(len(y_test)),
        }
        return self.metrics

    def score_all(self, feature_rows: list[dict]) -> list[dict]:
        if self.model is None:
            raise RuntimeError("ChurnModel.train must be called before score_all")
        X = np.array([[r[f] for f in FEATURE_NAMES] for r in feature_rows], dtype=float)
        Z = self.scaler.transform(X)
        probs = self.model.predict_proba(Z)[:, 1]
        for i, row in enumerate(feature_rows):
            p = float(probs[i])
            row["churn_probability"] = round(p, 4)
            row["churn_risk_band"] = risk_band(p)
            row["churn_drivers"] = self._drivers(Z[i])
        return feature_rows

    def _drivers(self, z_row: np.ndarray, top_n: int = 3) -> list[str]:
        coefs = self.model.coef_[0]
        contributions = coefs * z_row  # >0 pushes toward churn
        top = np.argsort(contributions)[::-1][:top_n]
        drivers = []
        for j in top:
            if contributions[j] <= 0:
                break  # nothing else pushes this account toward churn
            high_text, low_text = DRIVER_TEXT[FEATURE_NAMES[j]]
            drivers.append(high_text if z_row[j] > 0 else low_text)
        return drivers

    def global_coefficients(self, top_n: int = 8) -> list[dict]:
        if self.model is None:
            return []
        coefs = self.model.coef_[0]
        order = np.argsort(np.abs(coefs))[::-1][:top_n]
        return [{"feature": FEATURE_NAMES[j], "coefficient": round(float(coefs[j]), 4)}
                for j in order]
