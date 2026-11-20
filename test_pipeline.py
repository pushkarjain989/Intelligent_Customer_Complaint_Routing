import os
os.environ["USE_TF"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import pandas as pd
from backend.nlp_pipeline import ComplaintNLPPipeline
from backend.templates import PRESET_COMPLAINTS

def main():
    print("=" * 70)
    print("TESTING COMPLAINT NLP PIPELINE ON PRESETS")
    print("=" * 70)
    pipeline = ComplaintNLPPipeline()
    print(f"Pipeline loaded. is_trained = {pipeline.is_trained}, clusters = {pipeline.n_clusters}")
    print(f"Active Dataset: {pipeline.dataset_name}")
    print("Cluster names:", [pipeline.cluster_names[i] for i in range(pipeline.n_clusters)])
    print("-" * 70)
    
    threshold = 0.50
    presets = pipeline.get_dynamic_presets()
    all_matched = True
    for p in presets:
        res = pipeline.predict(p["text"], similarity_threshold=threshold)
        expected = p["expected_decision"]
        actual = res["decision"]
        match_str = "MATCH" if expected == actual else "MISMATCH"
        if expected != actual:
            all_matched = False
        print(f"Case {p['id']} [{p['category']}]:")
        print(f"  Expected: {expected} | Actual: {actual} -> {match_str}")
        print(f"  Cluster: {res['cluster_name']}")
        print(f"  Similarity: {res['similarity']:.4f} (Threshold: {threshold})")
        print(f"  Anomaly: {res['is_anomaly']} (score: {res['anomaly_score']}) | Sentiment: {res['sentiment']}")
        print(f"  Reason: {res['reason']}")
        print(f"  Reply Preview: {res['suggested_reply'][:80]}...")
        print()
    
    print("=" * 70)
    print(f"All presets matched expected decisions: {all_matched}")
    print("=" * 70)

if __name__ == "__main__":
    main()

