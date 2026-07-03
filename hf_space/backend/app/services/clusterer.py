import numpy as np
from sklearn.cluster import KMeans

SEGMENT_LABELS = ["Strategic Champions", "Steady Adopters", "Growing Accounts",
                  "At-Risk", "Dormant"]

# Feature -> direction used both to build the cluster matrix (from `<name>_norm`
# keys) and to rank centroids: +1 means higher is healthier, -1 the opposite.
CLUSTER_FEATURES = {
    "recency": -1,           # low = recent purchase = healthy
    "frequency": +1,
    "monetary": +1,
    "utilization_rate": +1,
    "tickets_per_month": -1,  # heavy support load = unhealthy
}


class KMeansClusterer:
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state

    def cluster(self, data: list[dict]) -> list[dict]:
        if not data:
            return data
        keys = [f"{f}_norm" for f in CLUSTER_FEATURES]
        X = np.array([[r[k] for k in keys] for r in data])
        n = min(self.n_clusters, len(data))
        km = KMeans(n_clusters=n, random_state=self.random_state, n_init=10)
        km.fit(X)
        labels = self._assign_labels(km.cluster_centers_)
        for i, row in enumerate(data):
            row["cluster_id"] = int(km.labels_[i])
            row["segment"] = labels[int(km.labels_[i])]
        return data

    def _assign_labels(self, centers: np.ndarray) -> dict:
        # Health score per centroid: negative-direction features contribute
        # (1 - value); highest score = Strategic Champions
        signs = list(CLUSTER_FEATURES.values())
        scores = np.zeros(len(centers))
        for j, sign in enumerate(signs):
            scores += centers[:, j] if sign > 0 else (1 - centers[:, j])
        ranked = np.argsort(scores)[::-1]  # descending
        return {int(cluster_id): SEGMENT_LABELS[rank] for rank, cluster_id in enumerate(ranked)}
