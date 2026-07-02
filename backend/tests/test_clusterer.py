import pytest
from services.clusterer import KMeansClusterer

def make_rfm_rows(n=100):
    import random
    random.seed(42)
    rows = []
    for i in range(n):
        r = random.random()
        f = random.random()
        m = random.random()
        rows.append({"customer_id": f"c{i}", "rfm_r_norm": r, "rfm_f_norm": f, "rfm_m_norm": m})
    return rows

def test_produces_5_clusters():
    clusterer = KMeansClusterer(n_clusters=5, random_state=42)
    result = clusterer.cluster(make_rfm_rows())
    labels = {r["segment"] for r in result}
    assert len(labels) == 5

def test_all_known_segment_names():
    clusterer = KMeansClusterer(n_clusters=5, random_state=42)
    result = clusterer.cluster(make_rfm_rows(200))
    valid = {"Champions","Loyal Customers","At-Risk","Hibernating","Lost"}
    assert {r["segment"] for r in result}.issubset(valid)

def test_deterministic_with_same_seed():
    c = KMeansClusterer(n_clusters=5, random_state=0)
    data = make_rfm_rows()
    r1 = [x["segment"] for x in c.cluster(data)]
    r2 = [x["segment"] for x in c.cluster(data)]
    assert r1 == r2