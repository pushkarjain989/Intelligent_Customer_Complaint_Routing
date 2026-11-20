from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., description="Customer complaint text")
    similarity_threshold: Optional[float] = Field(0.50, ge=0.0, le=1.0, description="Cosine similarity threshold for AI reply")


class PredictResponse(BaseModel):
    text: str
    cleaned_text: str
    sentiment: str
    sentiment_scores: Dict[str, float]
    is_very_negative: bool
    cluster_id: int
    cluster_name: str
    cluster_keywords: List[str]
    similarity: float
    is_anomaly: bool
    anomaly_score: float
    
    # Dual Anomaly Detection (DBSCAN + Isolation Forest)
    dbscan_anomaly: bool = False
    dbscan_score: float = 0.0
    isolation_forest_anomaly: bool = False
    isolation_forest_score: float = 0.0
    ensemble_anomaly: bool = False
    anomaly_confidence: float = 0.0
    anomaly_consensus: str = "In-Distribution"
    
    # HDBSCAN & Hierarchical Cluster Info
    hdbscan_cluster_name: str = "Standard Cluster"
    hdbscan_probability: float = 1.0
    
    # Dynamic LLM / RAG Generation
    decision: str  # "AI" or "HUMAN"
    reason: str
    suggested_reply: str
    rag_reply: Optional[Dict[str, Any]] = None
    
    pca_coordinates: List[float]


class BatchPredictRequest(BaseModel):
    texts: List[str]
    similarity_threshold: Optional[float] = 0.50


class BatchPredictResponse(BaseModel):
    results: List[PredictResponse]
    summary: Dict[str, Any]


class TrainRequest(BaseModel):
    sample_size: Optional[int] = Field(2000, ge=100, le=14000)
    n_clusters: Optional[int] = Field(6, ge=2, le=15)
    dbscan_eps: Optional[float] = Field(0.48, ge=0.1, le=1.0)
    dbscan_min_samples: Optional[int] = Field(4, ge=2, le=20)
    similarity_threshold: Optional[float] = Field(0.50, ge=0.0, le=1.0)
    dataset_path: Optional[str] = None


class TrainResponse(BaseModel):
    status: str
    sample_size: int
    n_clusters: int
    anomalies_detected: int
    anomaly_percentage: float
    cluster_names: List[str]
    explained_variance: List[float]
    message: str


class VisualizePoint(BaseModel):
    id: int
    x: float
    y: float
    cluster_id: int
    cluster_name: str
    sentiment: str
    is_anomaly: bool
    snippet: str


class VisualizeResponse(BaseModel):
    points: List[VisualizePoint]
    centroids: List[Dict[str, Any]]
    variance_ratio: List[float]
    total_points: int
    clusters_summary: List[Dict[str, Any]]


class ClusterInfo(BaseModel):
    id: int
    name: str
    size: int
    percentage: float
    keywords: List[str]
    representative_examples: List[str]
    dominant_sentiment: str


class StatusResponse(BaseModel):
    is_trained: bool
    dataset_name: str
    sample_size: int
    n_clusters: int
    similarity_threshold: float
    dbscan_eps: float
    dbscan_min_samples: int
    clusters: List[Dict[str, Any]]
