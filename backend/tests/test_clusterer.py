from app.services.clusterer import CLUSTER_FEATURES, KMeansClusterer, SEGMENT_LABELS

def make_feature_rows(n=100):
    import random
    random.seed(42)
    rows = []
    for i in range(n):
        row = {"account_id": f"a{i}"}
        for f in CLUSTER_FEATURES:
            row[f"{f}_norm"] = random.random()
        rows.append(row)
    return rows

def test_produces_5_clusters():
    clusterer = KMeansClusterer(n_clusters=5, random_state=42)
    result = clusterer.cluster(make_feature_rows())
    labels = {r["segment"] for r in result}
    assert len(labels) == 5

def test_all_known_segment_names():
    clusterer = KMeansClusterer(n_clusters=5, random_state=42)
    result = clusterer.cluster(make_feature_rows(200))
    assert {r["segment"] for r in result}.issubset(set(SEGMENT_LABELS))

def test_deterministic_with_same_seed():
    c = KMeansClusterer(n_clusters=5, random_state=0)
    data = make_feature_rows()
    r1 = [x["segment"] for x in c.cluster(data)]
    r2 = [x["segment"] for x in c.cluster(data)]
    assert r1 == r2

def test_healthiest_row_is_champion():
    # One clearly healthy account, one clearly unhealthy, plus noise
    rows = make_feature_rows(50)
    healthy = {"account_id": "healthy", "recency_norm": 0.0, "frequency_norm": 1.0,
               "monetary_norm": 1.0, "utilization_rate_norm": 1.0, "tickets_per_month_norm": 0.0}
    unhealthy = {"account_id": "unhealthy", "recency_norm": 1.0, "frequency_norm": 0.0,
                 "monetary_norm": 0.0, "utilization_rate_norm": 0.0, "tickets_per_month_norm": 1.0}
    result = KMeansClusterer(random_state=42).cluster(rows + [healthy, unhealthy])
    by_id = {r["account_id"]: r["segment"] for r in result}
    assert by_id["healthy"] == "Strategic Champions"
    assert by_id["unhealthy"] == "Dormant"
