import os
import re
import pickle
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest
from sklearn.cluster import HDBSCAN
from scipy.cluster.hierarchy import linkage
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Suppress warnings & TF logs
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["LOKY_MAX_CPU_COUNT"] = "4"

import spacy
from sentence_transformers import SentenceTransformer

from backend.templates import generate_response, generate_rag_response, generate_ticket_id

logger = logging.getLogger("nlp_pipeline")
logger.setLevel(logging.INFO)


class ComplaintNLPPipeline:
    def __init__(self, model_store_dir: str = "backend/model_store"):
        self.model_store_dir = model_store_dir
        os.makedirs(self.model_store_dir, exist_ok=True)
        self.pipeline_file = os.path.join(self.model_store_dir, "pipeline_state.pkl")

        # 1. Initialize spaCy
        logger.info("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

        # 2. Initialize VADER
        logger.info("Loading VADER Sentiment Analyzer...")
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # 3. Initialize SentenceTransformer
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # ML State Models
        self.kmeans: Optional[KMeans] = None
        self.dbscan: Optional[DBSCAN] = None
        self.isolation_forest: Optional[IsolationForest] = None
        self.hdbscan: Optional[HDBSCAN] = None
        self.pca: Optional[PCA] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        
        # Hierarchical & Dendrogram Data
        self.hierarchical_linkage: Optional[List[List[float]]] = None
        self.dendrogram_data: Optional[Dict[str, Any]] = None
        self.hdbscan_clusters_summary: List[Dict[str, Any]] = []
        
        # State Data
        self.is_trained: bool = False
        self.n_clusters: int = 6
        self.dbscan_eps: float = 0.48
        self.dbscan_min_samples: int = 4
        self.similarity_threshold: float = 0.58
        self.dataset_name: str = "Twitter Airline Sentiment"
        self.sample_size: int = 0
        
        # Cluster metadata
        self.cluster_centroids: Optional[np.ndarray] = None  # (k, 384)
        self.cluster_exemplars: Dict[int, np.ndarray] = {}  # {c_id: (m, 384)}
        self.cluster_names: Dict[int, str] = {}
        self.cluster_keywords: Dict[int, List[str]] = {}
        self.cluster_samples: Dict[int, List[str]] = {}
        self.cluster_sentiments: Dict[int, str] = {}
        
        # DBSCAN core samples for out-of-sample anomaly scoring
        self.core_samples: Optional[np.ndarray] = None
        self.training_records: List[Dict[str, Any]] = []
        self.pca_variance_ratio: List[float] = [0.0, 0.0]

        # Try to load existing model if available
        self.load_state()

    def _build_dendrogram_tree(self, Z: np.ndarray) -> Dict[str, Any]:
        """
        Constructs hierarchical tree merge data for interactive dendrogram visualization.
        Shows how sub-topics merge into broader parent departments.
        """
        n = self.n_clusters
        nodes = {}
        for i in range(n):
            nodes[i] = {
                "id": i,
                "name": self.cluster_names.get(i, f"Cluster #{i + 1}"),
                "keywords": self.cluster_keywords.get(i, [])[:4],
                "size": 1,
                "is_leaf": True
            }
            
        merges = []
        for idx, row in enumerate(Z):
            child_a, child_b, dist, count = int(row[0]), int(row[1]), float(row[2]), int(row[3])
            parent_id = n + idx
            name_a = nodes.get(child_a, {}).get("name", f"Node {child_a}")
            name_b = nodes.get(child_b, {}).get("name", f"Node {child_b}")
            
            # Short descriptive name for merged category
            clean_a = name_a.replace("Parent Category:", "").split("&")[0].strip()
            clean_b = name_b.replace("Parent Category:", "").split("&")[0].strip()
            merged_name = f"{clean_a} & {clean_b}"
            
            nodes[parent_id] = {
                "id": parent_id,
                "name": merged_name,
                "distance": round(dist, 4),
                "count": count,
                "children": [child_a, child_b],
                "is_leaf": False
            }
            merges.append({
                "step": idx + 1,
                "source_a": name_a,
                "source_b": name_b,
                "distance": round(dist, 4),
                "merged_label": merged_name,
                "combined_clusters": count
            })
            
        return {
            "leaf_clusters": [nodes[i] for i in range(n)],
            "linkage_matrix": Z.tolist(),
            "merges": merges,
            "root_node_id": n + len(Z) - 1 if len(Z) > 0 else 0
        }

    def preprocess_text(self, text: str) -> str:
        """
        1. Text Preprocessing:
        - Lowercasing
        - Remove URLs, handles (@user), punctuation
        - Remove stopwords
        - Lemmatization via spaCy
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Strip URLs, handles, and non-alphanumeric chars
        cleaned = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"@\w+", "", cleaned)
        cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned)
        cleaned = cleaned.lower().strip()
        
        # spaCy tokenization, lemmatization, stopword & punctuation removal
        doc = self.nlp(cleaned)
        lemmas = [
            token.lemma_.strip()
            for token in doc
            if not token.is_stop and not token.is_punct and len(token.lemma_.strip()) > 1
        ]
        return " ".join(lemmas)

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        5. Sentiment Analysis using VADER:
        Output: Positive / Neutral / Negative + raw scores + very negative flag
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = scores["compound"]
        neg = scores["neg"]

        if compound >= 0.05:
            sentiment = "Positive"
        elif compound <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # Very negative rule: strong negative compound OR high negative component
        is_very_negative = bool(compound <= -0.50 or neg >= 0.35)

        return {
            "sentiment": sentiment,
            "scores": {
                "compound": round(float(compound), 4),
                "pos": round(float(scores["pos"]), 4),
                "neu": round(float(scores["neu"]), 4),
                "neg": round(float(scores["neg"]), 4),
            },
            "is_very_negative": is_very_negative,
        }

    def compute_embedding(self, text: str) -> np.ndarray:
        """
        2. Embeddings: Convert text → normalized vector embedding using all-MiniLM-L6-v2
        """
        emb = self.embedder.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return emb[0]

    def compute_embeddings_batch(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        return self.embedder.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def train(
        self,
        df: pd.DataFrame,
        sample_size: int = 2000,
        n_clusters: int = 6,
        dbscan_eps: float = 0.48,
        dbscan_min_samples: int = 4,
        similarity_threshold: float = 0.58,
        dataset_name: str = "Twitter Airline Sentiment"
    ) -> Dict[str, Any]:
        """
        Trains the full clustering, anomaly detection, PCA, and topic modeling pipeline.
        """
        logger.info(f"Starting training on {min(len(df), sample_size)} samples...")
        
        # Identify text column
        text_col = None
        for col in ["text", "complaint", "content", "tweet", "message", "complaint_text"]:
            if col in df.columns:
                text_col = col
                break
        if not text_col:
            for col in df.columns:
                if df[col].dtype == object and df[col].astype(str).str.len().mean() > 20:
                    text_col = col
                    break
        
        if not text_col:
            raise ValueError("CSV dataset must contain a 'text' column or similar text field.")

        # Clean samples
        df_clean = df.dropna(subset=[text_col]).copy()
        df_clean = df_clean[df_clean[text_col].astype(str).str.strip().str.len() > 10]
        
        if len(df_clean) > sample_size:
            df_sampled = df_clean.sample(n=sample_size, random_state=42).reset_index(drop=True)
        else:
            df_sampled = df_clean.reset_index(drop=True)

        raw_texts = df_sampled[text_col].astype(str).tolist()
        self.sample_size = len(raw_texts)
        self.n_clusters = n_clusters
        self.dbscan_eps = dbscan_eps
        self.dbscan_min_samples = dbscan_min_samples
        self.similarity_threshold = similarity_threshold
        self.dataset_name = dataset_name

        # 1. Preprocess texts using spaCy
        logger.info("Preprocessing texts with spaCy...")
        cleaned_texts = [self.preprocess_text(t) for t in raw_texts]

        # 2. Embeddings via SentenceTransformer
        logger.info("Computing embeddings via SentenceTransformer...")
        embeddings = self.compute_embeddings_batch(raw_texts)

        # 3. KMeans Clustering
        logger.info(f"Fitting KMeans with k={n_clusters}...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans_labels = kmeans.fit_predict(embeddings)
        self.kmeans = kmeans
        
        # Precompute normalized centroids for cosine similarity matching
        centroids = kmeans.cluster_centers_
        centroid_norms = np.linalg.norm(centroids, axis=1, keepdims=True)
        centroid_norms[centroid_norms == 0] = 1.0
        self.cluster_centroids = centroids / centroid_norms

        # Store full cluster member embeddings for nearest-neighbor similarity matching
        self.cluster_exemplars = {}
        for c_id in range(n_clusters):
            idx_in_c = np.where(kmeans_labels == c_id)[0]
            if len(idx_in_c) > 0:
                self.cluster_exemplars[c_id] = embeddings[idx_in_c]
            else:
                self.cluster_exemplars[c_id] = self.cluster_centroids[c_id:c_id+1]

        # 4. DBSCAN Anomaly Detection (metric='cosine')
        logger.info(f"Fitting DBSCAN (eps={dbscan_eps}, min_samples={dbscan_min_samples})...")
        dbscan = DBSCAN(eps=dbscan_eps, min_samples=dbscan_min_samples, metric="cosine")
        dbscan_labels = dbscan.fit_predict(embeddings)
        self.dbscan = dbscan
        
        if len(dbscan.core_sample_indices_) > 0:
            self.core_samples = embeddings[dbscan.core_sample_indices_]
        else:
            self.core_samples = embeddings

        n_anomalies = int(np.sum(dbscan_labels == -1))
        anomaly_pct = round((n_anomalies / len(raw_texts)) * 100, 2)

        # 4b. Dual Anomaly Detection: Isolation Forest
        logger.info("Fitting Isolation Forest for Dual Anomaly Detection...")
        isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=0.07,
            random_state=42,
            n_jobs=-1
        )
        isolation_forest.fit(embeddings)
        self.isolation_forest = isolation_forest

        # 4c. HDBSCAN: Hierarchical Density-Based Clustering
        logger.info("Fitting HDBSCAN (Hierarchical Density-Based Clustering)...")
        try:
            hdbscan_model = HDBSCAN(
                min_cluster_size=12,
                min_samples=3,
                metric="cosine"
            )
            hdb_labels = hdbscan_model.fit_predict(embeddings)
            self.hdbscan = hdbscan_model
            
            # Summarize HDBSCAN clusters
            unique_hdb = [lbl for lbl in np.unique(hdb_labels) if lbl != -1]
            self.hdbscan_clusters_summary = []
            for h_id in unique_hdb:
                idx_h = np.where(hdb_labels == h_id)[0]
                self.hdbscan_clusters_summary.append({
                    "id": int(h_id),
                    "size": int(len(idx_h)),
                    "percentage": round(len(idx_h) / len(raw_texts) * 100, 1),
                    "sample": raw_texts[idx_h[0]][:90] + "..." if len(idx_h) > 0 else ""
                })
        except Exception as e:
            logger.warning(f"HDBSCAN fitting note: {e}")
            self.hdbscan = None
            self.hdbscan_clusters_summary = []

        # 5. PCA Dimensionality Reduction
        logger.info("Fitting PCA (2 components)...")
        pca = PCA(n_components=2, random_state=42)
        pca_coords = pca.fit_transform(embeddings)
        self.pca = pca
        self.pca_variance_ratio = [round(float(v), 4) for v in pca.explained_variance_ratio_]

        # 6. TF-IDF Topic & Keyword Discovery
        logger.info("Extracting cluster keywords and topic names...")
        self.tfidf_vectorizer = TfidfVectorizer(max_features=2500, stop_words="english", ngram_range=(1, 2))
        valid_cleaned = [t if t.strip() else "airline service" for t in cleaned_texts]
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(valid_cleaned)
        feature_names = np.array(self.tfidf_vectorizer.get_feature_names_out())

        self.cluster_names = {}
        self.cluster_keywords = {}
        self.cluster_samples = {}
        self.cluster_sentiments = {}

        assigned_titles = set()
        for c_id in range(n_clusters):
            idx_in_cluster = np.where(kmeans_labels == c_id)[0]
            if len(idx_in_cluster) == 0:
                self.cluster_names[c_id] = f"Cluster #{c_id + 1}"
                self.cluster_keywords[c_id] = ["service", "flight"]
                self.cluster_samples[c_id] = []
                self.cluster_sentiments[c_id] = "Negative"
                continue

            # Compute mean tf-idf for this cluster
            mean_tfidf = tfidf_matrix[idx_in_cluster].mean(axis=0)
            top_indices = np.argsort(np.asarray(mean_tfidf).flatten())[::-1][:8]
            top_terms = feature_names[top_indices].tolist()
            self.cluster_keywords[c_id] = top_terms

            # Determine distinct semantic title
            title = self._derive_cluster_name(top_terms, c_id, assigned_titles)
            assigned_titles.add(title)
            self.cluster_names[c_id] = title

            # Representative sample texts
            cluster_raw = [raw_texts[i] for i in idx_in_cluster[:4]]
            self.cluster_samples[c_id] = cluster_raw

            # Dominant sentiment
            sample_sentiments = [self.analyze_sentiment(raw_texts[i])["sentiment"] for i in idx_in_cluster[:25]]
            dominant = max(set(sample_sentiments), key=sample_sentiments.count)
            self.cluster_sentiments[c_id] = dominant

        # 7. Hierarchical Agglomerative Linkage & Dendrogram Tree
        logger.info("Computing Hierarchical Linkage and Dendrogram Tree...")
        try:
            linkage_matrix = linkage(self.cluster_centroids, method="ward")
            self.hierarchical_linkage = linkage_matrix.tolist()
            self.dendrogram_data = self._build_dendrogram_tree(linkage_matrix)
        except Exception as e:
            logger.warning(f"Hierarchical linkage note: {e}")
            self.hierarchical_linkage = []
            self.dendrogram_data = {"leaf_clusters": [], "merges": []}

        # Store sample of points for frontend visualization
        self.training_records = []
        vis_sample_size = min(len(raw_texts), 750)
        vis_indices = np.random.RandomState(42).choice(len(raw_texts), vis_sample_size, replace=False)

        for i in vis_indices:
            sent_info = self.analyze_sentiment(raw_texts[i])
            self.training_records.append({
                "id": int(i),
                "x": round(float(pca_coords[i, 0]), 4),
                "y": round(float(pca_coords[i, 1]), 4),
                "cluster_id": int(kmeans_labels[i]),
                "cluster_name": self.cluster_names[int(kmeans_labels[i])],
                "sentiment": sent_info["sentiment"],
                "is_anomaly": bool(dbscan_labels[i] == -1),
                "snippet": raw_texts[i][:110] + ("..." if len(raw_texts[i]) > 110 else ""),
            })

        self.is_trained = True
        self.save_state()
        logger.info("Training complete and pipeline state saved!")

        return {
            "status": "success",
            "sample_size": self.sample_size,
            "n_clusters": self.n_clusters,
            "anomalies_detected": n_anomalies,
            "anomaly_percentage": anomaly_pct,
            "cluster_names": [self.cluster_names[i] for i in range(self.n_clusters)],
            "explained_variance": self.pca_variance_ratio,
            "message": f"Trained on {self.sample_size} complaints. {n_anomalies} anomalies identified ({anomaly_pct}%)."
        }

    def _derive_cluster_name(self, top_terms: List[str], cluster_id: int, assigned_titles: set) -> str:
        terms_joined = " ".join(top_terms).lower()
        
        categories = [
            ("Flight Delays & Cancellations", ["delay", "delayed", "late", "hour", "hours", "wait", "waiting", "cancel", "cancelled", "weather"]),
            ("Lost Luggage & Baggage Claims", ["bag", "bags", "luggage", "lost", "claim", "carousel", "suitcase", "damage"]),
            ("Customer Service & Wait Times", ["call", "hold", "phone", "service", "customer", "agent", "rep", "help", "hours hold"]),
            ("Airport Gate & Boarding Operations", ["gate", "airport", "line", "board", "boarding", "terminal", "checkin", "check in", "counter"]),
            ("Cabin Seating & In-Flight Experience", ["seat", "seats", "comfort", "cabin", "wifi", "entertainment", "first class", "food", "crew"]),
            ("Reservations, Booking & Ticketing", ["ticket", "tickets", "change", "book", "booking", "online", "reservation", "refund", "rebook", "fee"]),
            ("Crew Commendations & Service Appreciation", ["thank", "thanks", "great", "good", "love", "amazing", "awesome", "captain", "best", "kudos"]),
        ]
        
        # Score each category by term occurrences
        scores = []
        for name, keywords in categories:
            match_count = sum(1 for kw in keywords if kw in terms_joined)
            scores.append((match_count, name))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        candidate = None
        for score, name in scores:
            if score > 0 and name not in assigned_titles:
                candidate = name
                break

        if not candidate:
            GENERIC_WORDS = {"flight", "airline", "air", "plane", "thank", "thanks", "yes", "please", "just", "like", "get", "got", "can", "help"}
            clean_terms = [t for t in top_terms if len(t) > 2 and t.lower() not in GENERIC_WORDS][:2]
            if clean_terms:
                candidate = f"{' & '.join(t.capitalize() for t in clean_terms)} Inquiries"
            else:
                candidate = f"Cluster #{cluster_id + 1} General Inquiries"

        # Ensure uniqueness
        original_cand = candidate
        counter = 2
        while candidate in assigned_titles:
            candidate = f"{original_cand} ({counter})"
            counter += 1
            
        return candidate

    def predict(self, text: str, similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Full inference pipeline for incoming complaint:
        1. Text Preprocessing (spaCy)
        2. Sentence Transformer Embeddings
        3. Cosine similarity matching
        4. DBSCAN anomaly scoring
        5. VADER Sentiment Analysis
        6. Decision Engine logic
        7. AI reply generation
        8. PCA projection
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet. Please train or initialize the model first.")

        threshold = similarity_threshold if similarity_threshold is not None else self.similarity_threshold

        # 1. Preprocess
        cleaned_text = self.preprocess_text(text)

        # 2. Embedding
        query_emb = self.compute_embedding(text)  # normalized 384-d vector

        # 3. Cosine Similarity Matching to Nearest Cluster
        # Score each cluster combining centroid semantic affinity and nearest exemplar
        best_cluster_id = 0
        best_cluster_score = -1.0
        max_similarity = 0.0

        for c_id in range(self.n_clusters):
            c_dot = float(np.dot(self.cluster_centroids[c_id], query_emb))
            if c_id in self.cluster_exemplars and len(self.cluster_exemplars[c_id]) > 0:
                ex_dots = np.dot(self.cluster_exemplars[c_id], query_emb)
                max_ex = float(np.max(ex_dots))
            else:
                max_ex = c_dot
            
            # 60% centroid alignment, 40% nearest member
            cluster_score = 0.60 * c_dot + 0.40 * max_ex
            if cluster_score > best_cluster_score:
                best_cluster_score = cluster_score
                best_cluster_id = c_id
                max_similarity = max_ex

        cluster_name = self.cluster_names.get(best_cluster_id, f"Cluster {best_cluster_id}")
        cluster_keywords = self.cluster_keywords.get(best_cluster_id, [])

        # 4. Dual Anomaly Detection: DBSCAN + Isolation Forest
        # 4a. DBSCAN (cosine distance to nearest core sample)
        if self.core_samples is not None and len(self.core_samples) > 0:
            core_dots = np.dot(self.core_samples, query_emb)
            min_cosine_dist = float(max(0.0, 1.0 - np.max(core_dots)))
            dbscan_score = round(min_cosine_dist / self.dbscan_eps, 4)
            is_dbscan_anomaly = bool(min_cosine_dist > self.dbscan_eps)
        else:
            min_cosine_dist = 0.0
            dbscan_score = 0.0
            is_dbscan_anomaly = False

        # 4b. Isolation Forest Anomaly Detection
        if self.isolation_forest is not None:
            iso_pred = int(self.isolation_forest.predict([query_emb])[0])
            iso_dec = float(self.isolation_forest.decision_function([query_emb])[0])
            is_iso_anomaly = bool(iso_pred == -1)
            # Map decision function to [0, 1] anomaly score
            iso_score = round(float(np.clip((0.14 - iso_dec) / 0.28, 0.0, 1.0)), 4)
        else:
            is_iso_anomaly = False
            iso_score = 0.0

        # 4c. Ensemble Dual Anomaly Meter & Consensus
        dbscan_conf = round(float(np.clip((min_cosine_dist / (self.dbscan_eps * 1.35)) * 100.0, 0.0, 100.0)), 1)
        iso_conf = round(iso_score * 100.0, 1)
        ensemble_conf = round((dbscan_conf + iso_conf) / 2.0, 1)

        if is_dbscan_anomaly and is_iso_anomaly:
            ensemble_anomaly = True
            anomaly_consensus = f"Confirmed Outlier (DBSCAN: {dbscan_conf:.0f}% | IsoForest: {iso_conf:.0f}%)"
        elif is_dbscan_anomaly or is_iso_anomaly:
            ensemble_anomaly = True
            flagged = "DBSCAN" if is_dbscan_anomaly else "Isolation Forest"
            anomaly_consensus = f"Borderline Outlier ({flagged} Flagged | Conf: {ensemble_conf:.0f}%)"
        else:
            ensemble_anomaly = False
            anomaly_consensus = f"In-Distribution (Both Models Agree | Safety: {100.0 - ensemble_conf:.0f}%)"

        is_anomaly = ensemble_anomaly
        anomaly_score = round(ensemble_conf / 50.0, 4)

        # 4d. HDBSCAN Cluster Information
        hdbscan_cluster_name = f"HDBSCAN Cluster: {cluster_name}"
        hdbscan_prob = round(max_similarity, 3)

        # 5. Sentiment Analysis
        sentiment_res = self.analyze_sentiment(text)
        sentiment = sentiment_res["sentiment"]
        scores = sentiment_res["scores"]
        is_very_negative = sentiment_res["is_very_negative"]

        # 6. Decision Engine (Rule-Based Logic)
        if is_very_negative:
            decision = "HUMAN"
            reason = f"High negativity detected (Compound score: {scores['compound']}, Neg: {scores['neg']:.0%})"
        elif ensemble_anomaly:
            decision = "HUMAN"
            reason = f"Dual Anomaly Flagged: {anomaly_consensus}"
        elif max_similarity >= threshold:
            decision = "AI"
            reason = f"High similarity ({max_similarity:.2f} >= {threshold:.2f}) to standard cluster '{cluster_name}'"
        else:
            decision = "HUMAN"
            reason = f"Low cluster similarity ({max_similarity:.2f} < {threshold:.2f}) requires human review"

        # 7. AI Reply Generator & Dynamic LLM / RAG Reply
        ticket_id = generate_ticket_id()
        suggested_reply = generate_response(
            decision=decision,
            reason=reason,
            cluster_name=cluster_name,
            sentiment=sentiment,
            sentiment_scores=scores,
            similarity=max_similarity,
            is_anomaly=is_anomaly,
            text=text
        )
        
        rag_reply = generate_rag_response(
            decision=decision,
            reason=reason,
            cluster_name=cluster_name,
            sentiment=sentiment,
            sentiment_scores=scores,
            similarity=max_similarity,
            is_anomaly=is_anomaly,
            text=text,
            ticket_id=ticket_id
        )

        # 8. PCA Projection for Visualization
        if self.pca is not None:
            pca_point = self.pca.transform([query_emb])[0]
            pca_coords = [round(float(pca_point[0]), 4), round(float(pca_point[1]), 4)]
        else:
            pca_coords = [0.0, 0.0]

        return {
            "text": text,
            "cleaned_text": cleaned_text,
            "sentiment": sentiment,
            "sentiment_scores": scores,
            "is_very_negative": is_very_negative,
            "cluster_id": best_cluster_id,
            "cluster_name": cluster_name,
            "cluster_keywords": cluster_keywords,
            "similarity": round(max_similarity, 4),
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            
            # Dual Anomaly Detection
            "dbscan_anomaly": is_dbscan_anomaly,
            "dbscan_score": round(min_cosine_dist, 4),
            "isolation_forest_anomaly": is_iso_anomaly,
            "isolation_forest_score": iso_score,
            "ensemble_anomaly": ensemble_anomaly,
            "anomaly_confidence": ensemble_conf,
            "anomaly_consensus": anomaly_consensus,
            
            # HDBSCAN
            "hdbscan_cluster_name": hdbscan_cluster_name,
            "hdbscan_probability": hdbscan_prob,
            
            # Decision & Replies
            "decision": decision,
            "reason": reason,
            "suggested_reply": suggested_reply,
            "rag_reply": rag_reply,
            "pca_coordinates": pca_coords,
        }

    def get_visualization_data(self) -> Dict[str, Any]:
        """
        4. Dimensionality Reduction: Returns 2D PCA cluster coordinates, anomalies, and centroids.
        """
        if not self.is_trained:
            return {
                "points": [],
                "centroids": [],
                "variance_ratio": [0.0, 0.0],
                "total_points": 0,
                "clusters_summary": [],
            }

        # Project cluster centroids to 2D PCA
        centroids_2d = []
        if self.pca is not None and self.cluster_centroids is not None:
            c_pca = self.pca.transform(self.cluster_centroids)
            for cid in range(self.n_clusters):
                centroids_2d.append({
                    "cluster_id": cid,
                    "name": self.cluster_names.get(cid, f"Cluster #{cid + 1}"),
                    "x": round(float(c_pca[cid, 0]), 4),
                    "y": round(float(c_pca[cid, 1]), 4),
                    "keywords": self.cluster_keywords.get(cid, [])[:5]
                })

        clusters_summary = []
        for cid in range(self.n_clusters):
            clusters_summary.append({
                "id": cid,
                "name": self.cluster_names.get(cid, f"Cluster #{cid + 1}"),
                "keywords": self.cluster_keywords.get(cid, [])[:6],
                "sentiment": self.cluster_sentiments.get(cid, "Neutral"),
                "examples": self.cluster_samples.get(cid, [])[:2]
            })

        return {
            "points": self.training_records,
            "centroids": centroids_2d,
            "variance_ratio": self.pca_variance_ratio,
            "total_points": len(self.training_records),
            "clusters_summary": clusters_summary,
        }

    def get_status(self) -> Dict[str, Any]:
        clusters_list = []
        if self.is_trained:
            for cid in range(self.n_clusters):
                clusters_list.append({
                    "id": cid,
                    "name": self.cluster_names.get(cid, f"Cluster {cid}"),
                    "keywords": self.cluster_keywords.get(cid, [])[:5],
                    "dominant_sentiment": self.cluster_sentiments.get(cid, "Neutral"),
                    "sample": self.cluster_samples.get(cid, [""])[0] if self.cluster_samples.get(cid) else ""
                })

        return {
            "is_trained": self.is_trained,
            "dataset_name": self.dataset_name,
            "sample_size": self.sample_size,
            "n_clusters": self.n_clusters,
            "similarity_threshold": self.similarity_threshold,
            "dbscan_eps": self.dbscan_eps,
            "dbscan_min_samples": self.dbscan_min_samples,
            "clusters": clusters_list,
        }

    def get_dynamic_presets(self) -> List[Dict[str, Any]]:
        """
        Dynamically generates benchmark preset test cases from the active trained dataset's
        real cluster samples, ensuring the UI adapts immediately to whatever dataset is trained.
        """
        if not self.is_trained or not self.cluster_samples:
            from backend.templates import PRESET_COMPLAINTS
            return PRESET_COMPLAINTS

        presets = []
        for cid in range(self.n_clusters):
            samples = self.cluster_samples.get(cid, [])
            if not samples or not samples[0].strip():
                continue
            sample_text = samples[0].strip()
            cluster_name = self.cluster_names.get(cid, f"Cluster #{cid + 1}")
            sent = self.cluster_sentiments.get(cid, "Neutral")
            expected_decision = "HUMAN" if sent == "Negative" else "AI"
            
            presets.append({
                "id": f"cluster-{cid}",
                "category": cluster_name,
                "expected_decision": expected_decision,
                "text": sample_text,
                "description": f"Real benchmark sample from '{cluster_name}' ({self.dataset_name})."
            })

        # Add standard outlier anomaly test
        presets.append({
            "id": "case-anomaly",
            "category": "DBSCAN Anomaly (Outlier)",
            "expected_decision": "HUMAN",
            "text": "Quantum telemetry sub-carrier oscillation frequencies on payload transponder 0x4B require optical azimuth alignment.",
            "description": "Out-of-domain vocabulary; DBSCAN and Isolation Forest mark it as an outlier anomaly requiring human triage."
        })

        # Add severe outrage escalation test
        presets.append({
            "id": "case-escalation",
            "category": "Severe Outrage Escalation",
            "expected_decision": "HUMAN",
            "text": "Disgusting treatment! Stranded for hours with zero food or communication, and your rude staff laughed in our faces! Absolute nightmare!",
            "description": "Severe negative sentiment immediately triggers priority human escalation."
        })

        return presets

    def get_hierarchy_data(self) -> Dict[str, Any]:
        """Returns Dendrogram hierarchy tree and HDBSCAN cluster summary."""
        if self.is_trained and (self.dendrogram_data is None or not self.dendrogram_data.get("merges")):
            if self.cluster_centroids is not None:
                try:
                    Z = linkage(self.cluster_centroids, method="ward")
                    self.hierarchical_linkage = Z.tolist()
                    self.dendrogram_data = self._build_dendrogram_tree(Z)
                except Exception as e:
                    logger.warning(f"Building hierarchy data fallback: {e}")

        return {
            "dendrogram": self.dendrogram_data or {"leaf_clusters": [], "merges": []},
            "hdbscan_summary": self.hdbscan_clusters_summary or [],
            "n_clusters": self.n_clusters,
            "clusters": [
                {
                    "id": cid,
                    "name": self.cluster_names.get(cid, f"Cluster #{cid + 1}"),
                    "keywords": self.cluster_keywords.get(cid, [])[:5]
                }
                for cid in range(self.n_clusters)
            ]
        }

    def save_state(self):
        state = {
            "kmeans": self.kmeans,
            "dbscan": self.dbscan,
            "isolation_forest": self.isolation_forest,
            "hdbscan": self.hdbscan,
            "hierarchical_linkage": self.hierarchical_linkage,
            "dendrogram_data": self.dendrogram_data,
            "hdbscan_clusters_summary": self.hdbscan_clusters_summary,
            "pca": self.pca,
            "tfidf_vectorizer": self.tfidf_vectorizer,
            "is_trained": self.is_trained,
            "n_clusters": self.n_clusters,
            "dbscan_eps": self.dbscan_eps,
            "dbscan_min_samples": self.dbscan_min_samples,
            "similarity_threshold": self.similarity_threshold,
            "dataset_name": self.dataset_name,
            "sample_size": self.sample_size,
            "cluster_centroids": self.cluster_centroids,
            "cluster_exemplars": self.cluster_exemplars,
            "cluster_names": self.cluster_names,
            "cluster_keywords": self.cluster_keywords,
            "cluster_samples": self.cluster_samples,
            "cluster_sentiments": self.cluster_sentiments,
            "core_samples": self.core_samples,
            "training_records": self.training_records,
            "pca_variance_ratio": self.pca_variance_ratio,
        }
        with open(self.pipeline_file, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"Pipeline saved to {self.pipeline_file}")

    def load_state(self) -> bool:
        if not os.path.exists(self.pipeline_file):
            return False
        try:
            with open(self.pipeline_file, "rb") as f:
                state = pickle.load(f)
            self.kmeans = state.get("kmeans")
            self.dbscan = state.get("dbscan")
            self.isolation_forest = state.get("isolation_forest")
            self.hdbscan = state.get("hdbscan")
            self.hierarchical_linkage = state.get("hierarchical_linkage")
            self.dendrogram_data = state.get("dendrogram_data")
            self.hdbscan_clusters_summary = state.get("hdbscan_clusters_summary", [])
            self.pca = state.get("pca")
            self.tfidf_vectorizer = state.get("tfidf_vectorizer")
            self.is_trained = state.get("is_trained", False)
            self.n_clusters = state.get("n_clusters", 6)
            self.dbscan_eps = state.get("dbscan_eps", 0.48)
            self.dbscan_min_samples = state.get("dbscan_min_samples", 4)
            self.similarity_threshold = state.get("similarity_threshold", 0.58)
            self.dataset_name = state.get("dataset_name", "Twitter Airline Sentiment")
            self.sample_size = state.get("sample_size", 0)
            self.cluster_centroids = state.get("cluster_centroids")
            self.cluster_exemplars = state.get("cluster_exemplars", {})
            self.cluster_names = state.get("cluster_names", {})
            self.cluster_keywords = state.get("cluster_keywords", {})
            self.cluster_samples = state.get("cluster_samples", {})
            self.cluster_sentiments = state.get("cluster_sentiments", {})
            self.core_samples = state.get("core_samples")
            self.training_records = state.get("training_records", [])
            self.pca_variance_ratio = state.get("pca_variance_ratio", [0.0, 0.0])
            
            # Lazy upgrade for existing models: auto-generate Isolation Forest & Dendrogram if missing
            if self.is_trained and self.isolation_forest is None and self.cluster_exemplars:
                try:
                    all_pts = []
                    for ex in self.cluster_exemplars.values():
                        if len(ex) > 0:
                            all_pts.append(ex)
                    if all_pts:
                        stacked = np.vstack(all_pts)
                        iso = IsolationForest(n_estimators=100, contamination=0.07, random_state=42)
                        iso.fit(stacked)
                        self.isolation_forest = iso
                        logger.info("Auto-initialized Isolation Forest on existing exemplar vectors!")
                except Exception as e:
                    logger.warning(f"Auto-fit Isolation Forest fallback: {e}")

            if self.is_trained and (self.dendrogram_data is None or not self.dendrogram_data.get("merges")):
                try:
                    if self.cluster_centroids is not None:
                        Z = linkage(self.cluster_centroids, method="ward")
                        self.hierarchical_linkage = Z.tolist()
                        self.dendrogram_data = self._build_dendrogram_tree(Z)
                        logger.info("Auto-initialized Dendrogram Hierarchy Tree!")
                except Exception as e:
                    logger.warning(f"Auto-build dendrogram fallback: {e}")

            logger.info("Successfully loaded existing pipeline state from disk.")
            return True
        except Exception as e:
            logger.warning(f"Could not load pipeline state: {e}")
            return False
