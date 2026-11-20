import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ComplaintInput from './components/ComplaintInput';
import DecisionCard from './components/DecisionCard';
import ClusterVisualization from './components/ClusterVisualization';
import ClusterOverview from './components/ClusterOverview';
import DatasetManager from './components/DatasetManager';
import BatchProcessor from './components/BatchProcessor';

export default function App() {
  const [activeTab, setActiveTab] = useState('decision');
  
  // Model & System state
  const [status, setStatus] = useState(null);
  const [presets, setPresets] = useState([]);
  const [visData, setVisData] = useState(null);
  const [hierarchyData, setHierarchyData] = useState(null);
  
  // Interactive complaint routing state
  const [complaintText, setComplaintText] = useState("");
  const [threshold, setThreshold] = useState(0.50);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Fetch initial metadata and data
  const fetchData = async () => {
    try {
      const [resStatus, resPresets, resVis, resHier] = await Promise.all([
        fetch('/status').then((r) => (r.ok ? r.json() : null)),
        fetch('/presets').then((r) => (r.ok ? r.json() : { presets: [] })),
        fetch('/visualize').then((r) => (r.ok ? r.json() : null)),
        fetch('/hierarchy').then((r) => (r.ok ? r.json() : null)),
      ]);

      if (resStatus) setStatus(resStatus);
      if (resPresets?.presets) setPresets(resPresets.presets);
      if (resVis) setVisData(resVis);
      if (resHier) setHierarchyData(resHier);
      return { resStatus, resPresets, resVis, resHier };
    } catch (err) {
      console.error('Error fetching system data:', err);
    }
  };

  useEffect(() => {
    fetchData().then((data) => {
      const firstPreset = data?.resPresets?.presets?.[0];
      if (firstPreset?.text) {
        setComplaintText(firstPreset.text);
        handleAnalyze(firstPreset.text);
      }
    });
  }, []);

  // Run initial prediction if not yet analyzed
  useEffect(() => {
    if (status?.is_trained && !analysisResult && complaintText) {
      handleAnalyze(complaintText);
    }
  }, [status]);

  const handleAnalyze = async (overrideText) => {
    const textToSend = overrideText !== undefined ? overrideText : complaintText;
    if (!textToSend || !textToSend.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSend.trim(),
          similarity_threshold: threshold,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Prediction failed');
      }

      setAnalysisResult(data);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPreset = (preset) => {
    setComplaintText(preset.text);
    handleAnalyze(preset.text);
  };

  const handleSelectSample = (sampleText) => {
    setComplaintText(sampleText);
    setActiveTab('decision');
    handleAnalyze(sampleText);
  };

  const handleTrainSuccess = async () => {
    const data = await fetchData();
    const newPresets = data?.resPresets?.presets;
    if (newPresets && newPresets.length > 0) {
      const first = newPresets[0];
      setComplaintText(first.text);
      handleAnalyze(first.text);
    }
    setActiveTab('decision');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} status={status} />

      <main className="main-content">
        {errorMsg && (
          <div style={{
            padding: '0.85rem 1.25rem',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#f43f5e',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span><strong>Notice:</strong> {errorMsg}</span>
            <button
              onClick={() => setErrorMsg(null)}
              style={{ background: 'transparent', border: 'none', color: '#f43f5e', cursor: 'pointer', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>
        )}

        {/* TAB 1: DECISION ROUTING WORKBENCH */}
        {activeTab === 'decision' && (
          <div className="grid-2col">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <ComplaintInput
                text={complaintText}
                setText={setComplaintText}
                threshold={threshold}
                setThreshold={setThreshold}
                presets={presets}
                onAnalyze={() => handleAnalyze()}
                isLoading={isLoading}
                onSelectPreset={handleSelectPreset}
              />

              {/* Compact 2D PCA Projection Widget */}
              {visData && (
                <div className="glass-panel" style={{ overflow: 'hidden' }}>
                  <div className="card-header" style={{ padding: '0.9rem 1.25rem' }}>
                    <div className="card-title" style={{ fontSize: '0.92rem' }}>
                      <span>Live 2D PCA Embedding Projection</span>
                    </div>
                    <button
                      className="btn-secondary"
                      style={{ padding: '0.3rem 0.65rem', fontSize: '0.72rem' }}
                      onClick={() => setActiveTab('visualize')}
                    >
                      Expand Map
                    </button>
                  </div>
                  <div style={{ height: '240px', padding: '0.5rem' }}>
                    <ClusterVisualization 
                      visData={visData} 
                      hierarchyData={hierarchyData}
                      activePoint={analysisResult} 
                      isLoading={isLoading} 
                      isCompact={true}
                    />
                  </div>
                </div>
              )}
            </div>

            <div>
              <DecisionCard 
                result={analysisResult} 
                threshold={threshold} 
              />
            </div>
          </div>
        )}

        {/* TAB 2: FULL 2D PCA CLUSTER VISUALIZATION */}
        {activeTab === 'visualize' && (
          <ClusterVisualization 
            visData={visData} 
            hierarchyData={hierarchyData}
            activePoint={analysisResult} 
            isLoading={isLoading} 
          />
        )}

        {/* TAB 3: CLUSTER TAXONOMY */}
        {activeTab === 'clusters' && (
          <ClusterOverview 
            clusters={visData?.clusters_summary} 
            onSelectSample={handleSelectSample} 
          />
        )}

        {/* TAB 4: DATASET & MODEL STUDIO */}
        {activeTab === 'train' && (
          <DatasetManager 
            onTrainSuccess={handleTrainSuccess} 
            currentStatus={status} 
          />
        )}

        {/* TAB 5: BATCH TRIAGE */}
        {activeTab === 'batch' && (
          <BatchProcessor 
            threshold={threshold}
            presets={presets}
            datasetName={status?.dataset_name}
          />
        )}
      </main>
    </div>
  );
}
