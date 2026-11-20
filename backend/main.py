import os
import shutil
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.schemas import (
    PredictRequest,
    PredictResponse,
    BatchPredictRequest,
    BatchPredictResponse,
    TrainRequest,
    TrainResponse,
    VisualizeResponse,
    StatusResponse,
)
from backend.nlp_pipeline import ComplaintNLPPipeline
from backend.templates import PRESET_COMPLAINTS

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api")

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "backend", "data")
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_DATASET = os.path.join(BASE_DIR, "archive (3)", "Tweets.csv")

# Global pipeline instance
pipeline: Optional[ComplaintNLPPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("Initializing NLP Pipeline...")
    pipeline = ComplaintNLPPipeline(model_store_dir=os.path.join(BASE_DIR, "backend", "model_store"))
    
    # Auto-train default model if not already trained
    if not pipeline.is_trained:
        if os.path.exists(DEFAULT_DATASET):
            logger.info(f"Pre-training default model on {DEFAULT_DATASET}...")
            try:
                df = pd.read_csv(DEFAULT_DATASET)
                pipeline.train(
                    df=df,
                    sample_size=1800,
                    n_clusters=6,
                    dbscan_eps=0.48,
                    dbscan_min_samples=4,
                    similarity_threshold=0.58,
                    dataset_name="Twitter Airline Sentiment (Default)"
                )
                logger.info("Auto-training complete!")
            except Exception as e:
                logger.error(f"Auto-training failed: {e}", exc_info=True)
        else:
            logger.warning("Default dataset not found. Model waiting for manual train/upload.")
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title="Intelligent Customer Complaint Routing & AI Reply Decision System",
    description="NLP-powered complaint routing, clustering, anomaly detection, and AI/Human decision engine.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend Vite dev server (usually http://localhost:5173) and any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status", response_model=StatusResponse)
def get_status():
    """Returns current model status, configuration, and cluster details."""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    return pipeline.get_status()


@app.get("/presets")
def get_presets():
    """Returns preset test complaints dynamically adapted to the active dataset."""
    if pipeline is not None and pipeline.is_trained:
        return {"presets": pipeline.get_dynamic_presets()}
    return {"presets": PRESET_COMPLAINTS}


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    1. Upload CSV dataset:
    Validates CSV, checks for a 'text' or complaint column, and stores in backend/data.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV (.csv)")
    
    dest_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate CSV content
        df = pd.read_csv(dest_path, nrows=50)
        text_cols = [c for c in df.columns if any(k in c.lower() for k in ["text", "complaint", "content", "tweet", "message"])]
        
        row_count = sum(1 for _ in open(dest_path, "r", encoding="utf-8", errors="ignore")) - 1
        
        # Sanitize preview rows to prevent NaN values from breaking JSON serialization
        clean_preview = [
            {k: ("" if pd.isna(v) else v) for k, v in row.items()}
            for row in df.head(3).to_dict(orient="records")
        ]
        
        return {
            "status": "success",
            "filename": file.filename,
            "filepath": dest_path,
            "total_rows": max(row_count, 0),
            "columns": df.columns.tolist(),
            "detected_text_column": text_cols[0] if text_cols else None,
            "preview": clean_preview,
            "message": f"Successfully uploaded '{file.filename}' with {row_count} rows."
        }
    except Exception as e:
        logger.error(f"Error handling upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/train", response_model=TrainResponse)
def train_model(payload: TrainRequest):
    """
    2. Train clustering and anomaly detection models:
    - KMeans (main clustering)
    - DBSCAN (anomaly detection)
    - PCA (2D visualization)
    - spaCy preprocessing & SentenceTransformer embeddings
    """
    global pipeline
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    dataset_file = payload.dataset_path
    if not dataset_file or not os.path.exists(dataset_file):
        # Fallback to default dataset or latest uploaded
        uploaded_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
        if uploaded_files:
            dataset_file = sorted(uploaded_files, key=os.path.getmtime, reverse=True)[0]
        elif os.path.exists(DEFAULT_DATASET):
            dataset_file = DEFAULT_DATASET
        else:
            raise HTTPException(status_code=400, detail="No dataset found. Please upload a CSV first.")
    
    try:
        df = pd.read_csv(dataset_file)
        result = pipeline.train(
            df=df,
            sample_size=payload.sample_size,
            n_clusters=payload.n_clusters,
            dbscan_eps=payload.dbscan_eps,
            dbscan_min_samples=payload.dbscan_min_samples,
            similarity_threshold=payload.similarity_threshold,
            dataset_name=os.path.basename(dataset_file)
        )
        return result
    except Exception as e:
        logger.error(f"Training error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/predict", response_model=PredictResponse)
def predict_complaint(payload: PredictRequest):
    """
    3. Predict endpoint:
    Input: complaint text
    Output: cluster, sentiment, decision (AI/HUMAN), reason, suggested reply, anomaly status, PCA point
    """
    if pipeline is None or not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline is not trained yet. Please train first.")
    
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Complaint text cannot be empty.")
    
    try:
        result = pipeline.predict(
            text=payload.text.strip(),
            similarity_threshold=payload.similarity_threshold
        )
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/batch_predict", response_model=BatchPredictResponse)
def batch_predict(payload: BatchPredictRequest):
    """Predict for multiple complaints in batch."""
    if pipeline is None or not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline is not trained yet.")
    
    results = []
    ai_count = 0
    human_count = 0
    anomaly_count = 0
    
    for text in payload.texts[:100]:  # Limit to 100 for responsiveness
        if text and text.strip():
            pred = pipeline.predict(text=text.strip(), similarity_threshold=payload.similarity_threshold)
            results.append(pred)
            if pred["decision"] == "AI":
                ai_count += 1
            else:
                human_count += 1
            if pred["is_anomaly"]:
                anomaly_count += 1
                
    summary = {
        "total": len(results),
        "ai_count": ai_count,
        "human_count": human_count,
        "ai_percentage": round((ai_count / len(results) * 100) if results else 0, 1),
        "anomaly_count": anomaly_count
    }
    return {"results": results, "summary": summary}


@app.get("/visualize", response_model=VisualizeResponse)
def get_visualization():
    """
    4. Visualize endpoint:
    Returns 2D PCA cluster coordinates, centroids, anomalies, and summary.
    """
    if pipeline is None or not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline is not trained yet.")
    
    data = pipeline.get_visualization_data()
    return data


@app.get("/clusters")
def get_clusters():
    """Returns detailed cluster breakdown and keywords."""
    if pipeline is None or not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline is not trained yet.")
    
    data = pipeline.get_visualization_data()
    return {"clusters": data["clusters_summary"]}


@app.get("/hierarchy")
def get_hierarchy():
    """Returns Hierarchical Agglomerative Linkage tree (dendrogram) and HDBSCAN cluster data."""
    if pipeline is None or not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline is not trained yet.")
    
    return pipeline.get_hierarchy_data()


# Serve frontend static assets if built
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
