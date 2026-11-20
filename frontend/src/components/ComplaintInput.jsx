import React from 'react';
import { Send, Sliders, Sparkles, RotateCcw, HelpCircle } from 'lucide-react';

export default function ComplaintInput({
  text,
  setText,
  threshold,
  setThreshold,
  presets,
  onAnalyze,
  isLoading,
  onSelectPreset
}) {
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (text.trim() && !isLoading) {
        onAnalyze();
      }
    }
  };

  return (
    <div className="glass-panel">
      <div className="card-header">
        <div>
          <div className="card-title">
            <Send size={18} className="text-accent" />
            <span>Complaint Intake & NLP Analysis</span>
          </div>
          <div className="card-subtitle">
            Input incoming customer message or select a benchmark preset to test routing rules
          </div>
        </div>
        {text && (
          <button
            className="btn-secondary"
            onClick={() => setText('')}
            title="Clear input"
            style={{ padding: '0.4rem 0.75rem' }}
          >
            <RotateCcw size={14} />
            <span>Clear</span>
          </button>
        )}
      </div>

      <div className="card-body">
        {/* Preset Benchmark Pills */}
        <div className="presets-section">
          <div className="section-label">
            <span>Benchmark Preset Test Cases</span>
            <span style={{ fontSize: '0.72rem', textTransform: 'none', color: 'var(--text-muted)' }}>
              1-click to test different decision branches
            </span>
          </div>
          <div className="preset-pills">
            {presets.map((preset) => {
              const isAi = preset.expected_decision === 'AI';
              return (
                <button
                  key={preset.id}
                  className="preset-pill"
                  onClick={() => onSelectPreset(preset)}
                  title={preset.description}
                  id={`preset-${preset.id}`}
                >
                  <span className={`pill-expected ${isAi ? 'ai' : 'human'}`}>
                    {preset.expected_decision}
                  </span>
                  <span>{preset.category}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Text Area */}
        <div className="textarea-wrapper">
          <textarea
            className="complaint-textarea"
            placeholder="Type or paste a customer complaint, inquiry, or feedback here... (Press Ctrl+Enter to analyze)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={5}
            id="complaint-input-box"
          />
        </div>

        {/* Similarity Threshold Slider */}
        <div className="control-row">
          <div className="slider-info">
            <div className="slider-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={15} />
              <span>Similarity Routing Threshold</span>
              <span title="If complaint is not very negative and not an anomaly: similarity >= threshold routes to AI; else routes to Human agent.">
                <HelpCircle size={13} style={{ color: 'var(--text-muted)', cursor: 'help' }} />
              </span>
            </div>
            <div className="slider-hint">
              Minimum cluster similarity required for automated AI reply
            </div>
          </div>
          <div className="slider-control">
            <input
              type="range"
              min="0.40"
              max="0.90"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="custom-range"
              id="threshold-slider"
            />
            <span className="slider-val">{(threshold * 100).toFixed(0)}%</span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          className="btn-primary"
          onClick={onAnalyze}
          disabled={!text.trim() || isLoading}
          id="btn-analyze-complaint"
        >
          {isLoading ? (
            <>
              <div className="spinner"></div>
              <span>Processing NLP Pipeline...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>Analyze & Decide Routing</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
