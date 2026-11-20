import React, { useState } from 'react';
import { 
  ListChecks, 
  Play, 
  Bot, 
  UserCheck, 
  AlertTriangle, 
  FileSpreadsheet,
  CheckCircle,
  Copy
} from 'lucide-react';

const DEFAULT_BATCH_TEXTS = [
  "Flight UA458 from Chicago is delayed by 45 minutes. Can you provide updated departure time?",
  "My checked bag has not arrived on carousel 4 after flight 892. Where can I track my luggage?",
  "Disgusting treatment! Stranded my elderly mother for 14 hours with no food, no water! Absolute nightmare!",
  "Quantum telemetry sub-carrier oscillation frequencies on payload transponder 0x4B require optical azimuth alignment.",
  "I want to change my seat from 14B to an aisle seat on tomorrow's morning flight to Dallas.",
  "Something seemed strange about the whole check-in process yesterday.",
  "Huge thank you to Captain Dave and the cabin crew on flight 214! You turned a stressful day into a wonderfully comfortable journey!",
  "Lost baggage tag number AA-88912, bag was never transferred during our Philadelphia layover."
];

export default function BatchProcessor({ threshold, presets = [], datasetName }) {
  const getInitialBatchText = () => {
    if (presets && presets.length > 0) {
      return presets.map((p) => p.text).join('\n\n');
    }
    return DEFAULT_BATCH_TEXTS.join('\n\n');
  };

  const [inputText, setInputText] = useState(getInitialBatchText());
  const [loading, setLoading] = useState(false);
  const [batchResponse, setBatchResponse] = useState(null);
  const [error, setError] = useState(null);

  // Automatically sync batch input with active dataset presets
  React.useEffect(() => {
    if (presets && presets.length > 0) {
      setInputText(presets.map((p) => p.text).join('\n\n'));
    }
  }, [presets, datasetName]);

  const handleResetToDataset = () => {
    if (presets && presets.length > 0) {
      setInputText(presets.map((p) => p.text).join('\n\n'));
    } else {
      setInputText(DEFAULT_BATCH_TEXTS.join('\n\n'));
    }
  };

  const handleRunBatch = async () => {
    const lines = inputText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 5);

    if (lines.length === 0) {
      setError('Please enter at least one complaint to analyze.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/batch_predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          texts: lines,
          similarity_threshold: threshold,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Batch processing failed');
      }
      setBatchResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>
          Batch Complaint Routing & Analytics
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Evaluate multiple customer tickets simultaneously to observe automated vs human routing distribution ratios.
        </p>
      </div>

      <div className="grid-2col">
        {/* INPUT COLUMN */}
        <div className="glass-panel">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="card-title">
              <FileSpreadsheet size={18} className="text-accent" />
              <span>Multi-Complaint Input ({datasetName || 'Active Model'})</span>
            </div>
            <button
              className="btn-secondary"
              onClick={handleResetToDataset}
              style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
              title="Populate with representative complaints from current model clusters"
            >
              🔄 Load Current Model Samples
            </button>
          </div>
          <div className="card-body">
            <textarea
              className="complaint-textarea"
              style={{ minHeight: '280px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter complaints separated by newlines..."
            />

            <button
              className="btn-primary"
              onClick={handleRunBatch}
              disabled={loading}
              style={{ marginTop: '1rem' }}
              id="btn-run-batch"
            >
              {loading ? (
                <>
                  <div className="spinner"></div>
                  <span>Batch Processing NLP Routing...</span>
                </>
              ) : (
                <>
                  <Play size={18} />
                  <span>Run Batch Triage & Routing</span>
                </>
              )}
            </button>

            {error && (
              <div style={{ marginTop: '1rem', color: '#f43f5e', fontSize: '0.8rem' }}>
                {error}
              </div>
            )}
          </div>
        </div>

        {/* SUMMARY COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {batchResponse && (
            <div className="glass-panel">
              <div className="card-header">
                <div className="card-title">
                  <ListChecks size={18} className="text-accent" />
                  <span>Routing Aggregate Distribution</span>
                </div>
              </div>
              <div className="card-body">
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-header">Total Evaluated</div>
                    <div className="metric-val">{batchResponse.summary.total}</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-header" style={{ color: 'var(--color-ai)' }}>AI Auto-Replies</div>
                    <div className="metric-val" style={{ color: 'var(--color-ai)' }}>
                      {batchResponse.summary.ai_count} ({batchResponse.summary.ai_percentage}%)
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-header" style={{ color: 'var(--color-human)' }}>Human Escalations</div>
                    <div className="metric-val" style={{ color: 'var(--color-human)' }}>
                      {batchResponse.summary.human_count}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '1rem', background: 'var(--bg-elevated)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                    <span>AI Autonomous Resolution Rate</span>
                    <strong style={{ color: 'var(--color-ai)' }}>{batchResponse.summary.ai_percentage}%</strong>
                  </div>
                  <div className="metric-bar-bg" style={{ height: '8px' }}>
                    <div
                      className="metric-bar-fill"
                      style={{ width: `${batchResponse.summary.ai_percentage}%`, backgroundColor: 'var(--color-ai)' }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {!batchResponse && (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ListChecks size={36} style={{ margin: '0 auto 0.75rem auto' }} />
              <p>Click "Run Batch Triage & Routing" to calculate routing decisions for the complaints on the left.</p>
            </div>
          )}
        </div>
      </div>

      {/* DETAILED RESULTS TABLE */}
      {batchResponse && (
        <div className="glass-panel">
          <div className="card-header">
            <div className="card-title">
              <span>Detailed Triage Results ({batchResponse.results.length} Tickets)</span>
            </div>
          </div>
          <div className="card-body" style={{ padding: '0' }}>
            <div className="batch-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Decision</th>
                    <th>Complaint Snippet</th>
                    <th>Sentiment</th>
                    <th>Assigned Cluster</th>
                    <th>Similarity</th>
                    <th>Anomaly</th>
                    <th>Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {batchResponse.results.map((row, idx) => {
                    const isAi = row.decision === 'AI';
                    return (
                      <tr key={idx}>
                        <td>
                          <span className={`pill-expected ${isAi ? 'ai' : 'human'}`}>
                            {row.decision}
                          </span>
                        </td>
                        <td style={{ maxWidth: '280px' }} title={row.text}>
                          {row.text.length > 65 ? `${row.text.slice(0, 65)}...` : row.text}
                        </td>
                        <td>
                          <span style={{ 
                            color: row.sentiment === 'Positive' ? 'var(--color-pos)' : row.sentiment === 'Negative' ? 'var(--color-neg)' : 'var(--color-neu)',
                            fontWeight: 600
                          }}>
                            {row.sentiment}
                          </span>
                        </td>
                        <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                          {row.cluster_name}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {(row.similarity * 100).toFixed(1)}%
                        </td>
                        <td>
                          {row.is_anomaly ? (
                            <span style={{ color: 'var(--color-anomaly)', fontWeight: 600 }}>Yes ({row.anomaly_score.toFixed(1)}x)</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>No</span>
                          )}
                        </td>
                        <td style={{ fontSize: '0.75rem' }}>
                          {row.reason}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
