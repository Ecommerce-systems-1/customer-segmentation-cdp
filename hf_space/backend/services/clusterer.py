import numpy as np
from sklearn.cluster import KMeans

SEGMENT_LABELS = ["Champions", "Loyal Customers", "At-Risk", "Hibernating", "Lost"]

class KMeansClusterer:
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state

    def cluster(self, rfm_data: list[dict]) -> list[dict]:
        if not rfm_data:
            return rfm_data
        X = np.array([[r["rfm_r_norm"], r["rfm_f_norm"], r["rfm_m_norm"]] for r in rfm_data])
        km = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)
        km.fit(X)
        labels = self._assign_labels(km.cluster_centers_)
        for i, row in enumerate(rfm_data):
            row["cluster_id"] = int(km.labels_[i])
            row["segment"] = labels[int(km.labels_[i])]
        return rfm_data

    def _assign_labels(self, centers: np.ndarray) -> dict:
        # Score each centroid: sum of R+F+M norms; highest = Champions
        scores = centers.sum(axis=1)
        ranked = np.argsort(scores)[::-1]  # descending
        return {int(cluster_id): SEGMENT_LABELS[rank] for rank, cluster_id in enumerate(ranked)}