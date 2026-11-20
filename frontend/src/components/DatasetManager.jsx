import React, { useState } from 'react';
import { 
  Upload, 
  Database, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  FileText, 
  Sliders, 
  Layers, 
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

export default function DatasetManager({ onTrainSuccess, currentStatus }) {
  const [file, setFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Hyperparameters
  const [sampleSize, setSampleSize] = useState(1500);
  const [nClusters, setNClusters] = useState(6);
  const [dbscanEps, setDbscanEps] = useState(0.48);
  const [dbscanMinSamples, setDbscanMinSamples] = useState(4);
  const [simThreshold, setSimThreshold] = useState(0.72);

  // Training state
  const [trainLoading, setTrainLoading] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [trainError, setTrainError] = useState(null);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setUploadError('Please select a valid CSV file (.csv).');
      return;
    }

    setFile(selectedFile);
    setUploadError(null);
    setUploadLoading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        let errorMsg = 'Upload failed';
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errorMsg;
        } catch {
          errorMsg = await response.text();
        }
        throw new Error(errorMsg);
      }
      const data = await response.json();
      setUploadResult(data);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleTrain = async () => {
    setTrainLoading(true);
    setTrainError(null);
    setTrainResult(null);

    try {
      const payload = {
        sample_size: parseInt(sampleSize),
        n_clusters: parseInt(nClusters),
        dbscan_eps: parseFloat(dbscanEps),
        dbscan_min_samples: parseInt(dbscanMinSamples),
        similarity_threshold: parseFloat(simThreshold),
        dataset_path: uploadResult ? uploadResult.filepath : null,
      };

      const response = await fetch('/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorMsg = 'Training failed';
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errorMsg;
        } catch {
          errorMsg = await response.text();
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setTrainResult(data);
      if (onTrainSuccess) {
        onTrainSuccess();
      }
    } catch (err) {
      setTrainError(err.message);
    } finally {
      setTrainLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* HEADER STATUS */}
      <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>
              Dataset & Model Training Studio
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Upload new complaint CSV datasets, tune KMeans, DBSCAN, and PCA hyperparameters, and train the NLP pipeline.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div className="status-badge">
              <Database size={13} />
              <span>Active: {currentStatus?.dataset_name || 'Twitter Airline Sentiment'}</span>
            </div>
            <div className="status-badge" style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.25)' }}>
              <span>{currentStatus?.sample_size || 0} Samples Fitted</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2col">
        {/* LEFT COLUMN: UPLOAD & HYPERPARAMETERS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* UPLOAD PANEL */}
          <div className="glass-panel">
            <div className="card-header">
              <div className="card-title">
                <Upload size={18} className="text-accent" />
                <span>Upload Complaint CSV Dataset</span>
              </div>
            </div>
            <div className="card-body">
              <label className="upload-dropzone" htmlFor="csv-file-input">
                <input 
                  type="file" 
                  id="csv-file-input" 
                  accept=".csv" 
                  style={{ display: 'none' }} 
                  onChange={handleFileChange}
                />
                <Upload size={36} className="upload-icon" />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  {uploadLoading ? 'Uploading and validating...' : 'Click or Drag & Drop CSV File'}
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Dataset must contain a text/complaint column. (Default: Twitter Airline Sentiment Dataset)
                </p>
              </label>

              {uploadError && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: 'var(--radius-sm)', color: '#f43f5e', fontSize: '0.8rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <AlertCircle size={15} />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadResult && (
                <div style={{ marginTop: '1rem', padding: '0.85rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#10b981', fontWeight: 600, marginBottom: '0.4rem' }}>
                    <CheckCircle2 size={16} />
                    <span>Uploaded: {uploadResult.filename}</span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                    Total Rows: <strong>{uploadResult.total_rows}</strong> | Detected Text Column: <code style={{ color: '#ffffff' }}>{uploadResult.detected_text_column}</code>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* HYPERPARAMETERS */}
          <div className="glass-panel">
            <div className="card-header">
              <div className="card-title">
                <Sliders size={18} className="text-accent" />
                <span>Training Pipeline Hyperparameters</span>
              </div>
            </div>
            <div className="card-body">
              <div className="hyperparams-grid">
                <div className="param-input-group">
                  <label>Training Sample Size</label>
                  <input
                    type="number"
                    min="200"
                    max="10000"
                    step="100"
                    value={sampleSize}
                    onChange={(e) => setSampleSize(e.target.value)}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Recommended: 1,000–3,000
                  </div>
                </div>

                <div className="param-input-group">
                  <label>KMeans Clusters (k)</label>
                  <input
                    type="number"
                    min="3"
                    max="12"
                    value={nClusters}
                    onChange={(e) => setNClusters(e.target.value)}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Default: 6 distinct topics
                  </div>
                </div>

                <div className="param-input-group">
                  <label>DBSCAN Epsilon (eps)</label>
                  <input
                    type="number"
                    min="0.2"
                    max="0.9"
                    step="0.02"
                    value={dbscanEps}
                    onChange={(e) => setDbscanEps(e.target.value)}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Cosine distance threshold (0.45–0.52)
                  </div>
                </div>

                <div className="param-input-group">
                  <label>DBSCAN Min Samples</label>
                  <input
                    type="number"
                    min="2"
                    max="15"
                    value={dbscanMinSamples}
                    onChange={(e) => setDbscanMinSamples(e.target.value)}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Core sample density (3–6)
                  </div>
                </div>
              </div>

              <button
                className="btn-primary"
                onClick={handleTrain}
                disabled={trainLoading}
                id="btn-trigger-training"
              >
                {trainLoading ? (
                  <>
                    <div className="spinner"></div>
                    <span>Training SentenceTransformer, KMeans, DBSCAN & PCA...</span>
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    <span>Train / Re-fit ML Pipeline</span>
                  </>
                )}
              </button>

              {trainError && (
                <div style={{ marginTop: '1rem', padding: '0.85rem', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: 'var(--radius-sm)', color: '#f43f5e', fontSize: '0.8rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <AlertCircle size={15} />
                  <span>{trainError}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: TRAINING RESULTS & ARCHITECTURE SUMMARY */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {trainResult && (
            <div className="glass-panel" style={{ border: '1px solid var(--color-ai)' }}>
              <div className="card-header" style={{ background: 'var(--color-ai-bg)' }}>
                <div className="card-title" style={{ color: '#10b981' }}>
                  <CheckCircle2 size={18} />
                  <span>Model Training Successful!</span>
                </div>
              </div>
              <div className="card-body">
                <div style={{ marginBottom: '1rem', fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                  {trainResult.message}
                </div>

                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-header">Sample Size</div>
                    <div className="metric-val">{trainResult.sample_size}</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-header">Clusters</div>
                    <div className="metric-val">{trainResult.n_clusters}</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-header">Anomalies Detected</div>
                    <div className="metric-val" style={{ color: 'var(--color-anomaly)' }}>
                      {trainResult.anomalies_detected} ({trainResult.anomaly_percentage}%)
                    </div>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.4rem' }}>
                    Generated Topic Clusters
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {trainResult.cluster_names?.map((name, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', padding: '0.35rem 0.6rem', background: 'var(--bg-elevated)', borderRadius: '4px', color: 'var(--text-secondary)' }}>
                        Cluster #{i + 1}: <strong>{name}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PIPELINE ARCHITECTURE CARD */}
          <div className="glass-panel">
            <div className="card-header">
              <div className="card-title">
                <ShieldCheck size={18} className="text-accent" />
                <span>ML Pipeline & Decision Architecture</span>
              </div>
            </div>
            <div className="card-body" style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>1. Preprocessing:</strong> spaCy lemmatization, stopword removal, lowercase normalization.
              </div>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>2. Dense Embeddings:</strong> SentenceTransformer (<code style={{ color: '#a5b4fc' }}>all-MiniLM-L6-v2</code>) generating 384-dimensional unit vectors.
              </div>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>3. Clustering:</strong> KMeans unsupervised cluster modeling + TF-IDF cluster topic name derivation.
              </div>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>4. Anomaly Detection:</strong> DBSCAN (density-based spatial clustering) isolating noise outliers and high cosine distance deviations.
              </div>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>5. Sentiment:</strong> VADER sentiment scoring compound intensity and identifying severe customer outrage.
              </div>
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>6. Rule Decision Engine:</strong>
                <pre style={{ 
                  background: 'var(--bg-secondary)', 
                  padding: '0.65rem', 
                  borderRadius: 'var(--radius-sm)', 
                  marginTop: '0.35rem', 
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  lineHeight: 1.5,
                  color: '#93c5fd'
                }}>
{`IF sentiment == VERY_NEGATIVE OR dbscan == ANOMALY:
    ROUTE -> HUMAN AGENT (Priority Queue)
ELSE IF cosine_similarity >= threshold:
    ROUTE -> AI AUTO-REPLY (Empathetic Resolution)
ELSE:
    ROUTE -> HUMAN AGENT (Ambiguity Review)`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
