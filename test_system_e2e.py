import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 75)
    print("E2E COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 75)
    
    # 1. Status
    status_code, status_data = request("/status")
    print(f"[1/6] GET /status -> HTTP {status_code}")
    print(f"      Model Trained: {status_data['is_trained']}")
    print(f"      Dataset: {status_data['dataset_name']}")
    print(f"      Sample Size: {status_data['sample_size']}")
    print(f"      Total Clusters: {status_data['n_clusters']}")
    print(f"      Clusters: {[c['name'] for c in status_data['clusters']]}")
    assert status_data["is_trained"] is True, "Model is not trained!"
    
    # 2. Presets
    _, presets_data = request("/presets")
    presets = presets_data["presets"]
    print(f"\n[2/6] GET /presets -> {len(presets)} test presets available")
    
    # 3. Individual Predictions & Decisions
    print("\n[3/6] POST /predict -> Validating decision engine paths:")
    success_count = 0
    for p in presets:
        _, pred = request("/predict", method="POST", data={
            "text": p["text"],
            "similarity_threshold": 0.50
        })
        is_match = pred["decision"] == p["expected_decision"]
        if is_match:
            success_count += 1
        print(f"   [{p['id']}] {p['category']}:")
        print(f"      Decision: {pred['decision']} (Expected: {p['expected_decision']}) -> {'PASSED' if is_match else 'FAIL'}")
        print(f"      Cluster: {pred['cluster_name']} (Similarity: {pred['similarity']:.3f})")
        print(f"      Sentiment: {pred['sentiment']} (Compound: {pred['sentiment_scores']['compound']}) | Anomaly: {pred['is_anomaly']}")
        print(f"      Reason: {pred['reason']}")
        print(f"      Reply: {pred['suggested_reply'][:90]}...")
    
    print(f"\n   Decision Engine accuracy: {success_count}/{len(presets)} presets passed ({success_count/len(presets):.0%})")
    assert success_count == len(presets), "Not all presets passed!"

    # 4. Batch Prediction
    print("\n[4/6] POST /batch_predict -> Testing bulk complaint routing:")
    batch_texts = [p["text"] for p in presets]
    _, batch_res = request("/batch_predict", method="POST", data={
        "texts": batch_texts,
        "similarity_threshold": 0.50
    })
    summary = batch_res["summary"]
    print(f"      Batch processed: {summary['total']} complaints")
    print(f"      AI Auto-Reply: {summary['ai_count']} ({summary['ai_percentage']}%)")
    print(f"      Escalated to Human: {summary['human_count']}")
    print(f"      Anomalies: {summary['anomaly_count']}")
    assert len(batch_res["results"]) == len(batch_texts), "Batch result count mismatch"

    # 5. 2D PCA Visualization
    print("\n[5/6] GET /visualize -> Validating 2D PCA coordinates:")
    _, vis_data = request("/visualize")
    print(f"      Total 2D points: {vis_data['total_points']}")
    print(f"      Centroids count: {len(vis_data['centroids'])}")
    print(f"      PCA Variance Explained: {vis_data['variance_ratio']}")
    assert vis_data["total_points"] > 0, "No visualization points returned"

    # 6. Frontend Assets
    print("\n[6/6] GET / -> Verifying static frontend bundle:")
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
        assert "<div id=\"root\"></div>" in html, "Root div missing from HTML!"
        print(f"      Single Page Application index.html served cleanly ({len(html)} bytes)")

    print("\n" + "=" * 75)
    print("ALL E2E CHECKS PASSED SUCCESSFULLY (100% OPERATIONAL)")
    print("=" * 75)

if __name__ == "__main__":
    main()
