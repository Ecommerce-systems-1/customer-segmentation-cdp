from sklearn.preprocessing import MinMaxScaler
import numpy as np

class RFMNormalizer:
    def normalize(self, rfm_data: list[dict]) -> list[dict]:
        valid = [r for r in rfm_data if r["recency"] is not None]
        if not valid:
            for r in rfm_data:
                r.update({"rfm_r_norm": 0.5, "rfm_f_norm": 0.5, "rfm_m_norm": 0.5})
            return rfm_data
        # Recency: invert (lower days = better customer → higher norm score)
        matrix = np.array([[r["recency"], r["frequency"], r["monetary"]] for r in valid])
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(matrix)
        scaled[:, 0] = 1 - scaled[:, 0]  # invert recency
        for i, r in enumerate(valid):
            r["rfm_r_norm"] = float(scaled[i, 0])
            r["rfm_f_norm"] = float(scaled[i, 1])
            r["rfm_m_norm"] = float(scaled[i, 2])
        for r in rfm_data:
            if r.get("rfm_r_norm") is None:
                r.update({"rfm_r_norm": 0.0, "rfm_f_norm": 0.0, "rfm_m_norm": 0.0})
        return rfm_data