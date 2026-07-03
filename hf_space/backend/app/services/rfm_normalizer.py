from sklearn.preprocessing import MinMaxScaler
import numpy as np

DEFAULT_FEATURES = ("recency", "frequency", "monetary")


class RFMNormalizer:
    """Min-max normalizes named features in place, adding `<name>_norm` keys."""

    def normalize(self, data: list[dict], features: tuple[str, ...] = DEFAULT_FEATURES) -> list[dict]:
        norm_keys = [f"{f}_norm" for f in features]
        valid = [r for r in data if all(r.get(f) is not None for f in features)]
        if not valid:
            for r in data:
                r.update({k: 0.5 for k in norm_keys})
            return data
        # Raw min-max on all axes; direction is not inverted here (e.g. low
        # recency = recent = better) — the clusterer accounts for direction
        # when ranking segments
        matrix = np.array([[r[f] for f in features] for r in valid], dtype=float)
        scaled = MinMaxScaler().fit_transform(matrix)
        for i, r in enumerate(valid):
            for j, k in enumerate(norm_keys):
                r[k] = float(scaled[i, j])
        for r in data:
            if r.get(norm_keys[0]) is None:
                r.update({k: 0.0 for k in norm_keys})
        return data
