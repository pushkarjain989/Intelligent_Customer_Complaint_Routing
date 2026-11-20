import React, { useState } from 'react';
import { 
  Bot, 
  UserCheck, 
  AlertTriangle, 
  Smile, 
  Meh, 
  Frown, 
  Copy, 
  Check, 
  Layers, 
  Activity, 
  Code2, 
  Flame,
  ShieldAlert,
  Sparkles,
  Cpu,
  FileText,
  Mail,
  Plane,
  Tag,
  DollarSign,
  Clock,
  MapPin,
  ShieldCheck,
  GitBranch
} from 'lucide-react';
import confetti from 'canvas-confetti';

export default function DecisionCard({ result, threshold }) {
  const [copied, setCopied] = useState(false);
  const [copiedSubject, setCopiedSubject] = useState(false);
  const [showTokens, setShowTokens] = useState(false);
  const [activeReplyTab, setActiveReplyTab] = useState('rag'); // 'rag' or 'template'

  if (!result) return null;

  const isAi = result.decision === 'AI';

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopySubject = (subject) => {
    navigator.clipboard.writeText(subject);
    setCopiedSubject(true);
    setTimeout(() => setCopiedSubject(false), 2000);
  };

  // Sentiment Icon & Color
  const getSentimentDetails = (sentiment, compound) => {
    if (sentiment === 'Positive') {
      return { icon: Smile, color: 'var(--color-pos)', label: `Positive (${compound > 0 ? '+' : ''}${compound})` };
    } else if (sentiment === 'Negative') {
      return { icon: Frown, color: 'var(--color-neg)', label: `Negative (${compound})` };
    }
    return { icon: Meh, color: 'var(--color-neu)', label: `Neutral (${compound})` };
  };

  const sentDetails = getSentimentDetails(result.sentiment, result.sentiment_scores?.compound);
  const SentIcon = sentDetails.icon;

  const rag = result.rag_reply;
  const entities = rag?.extracted_entities || {};

  return (
    <div className={`glass-panel decision-card ${isAi ? 'ai' : 'human'}`} id="decision-result-panel">
      <div className="card-header">
        <div className="card-title">
          {isAi ? <Bot size={20} className="text-ai" /> : <ShieldAlert size={20} className="text-human" />}
          <span>Decision Engine Outcome</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="pill-expected" style={{ 
            background: isAi ? 'var(--color-ai-bg)' : 'var(--color-human-bg)',
            color: isAi ? 'var(--color-ai)' : 'var(--color-human)',
            fontSize: '0.75rem',
            padding: '0.2rem 0.6rem'
          }}>
            {isAi ? 'AUTOMATED FLOW' : 'PRIORITY QUEUE'}
          </span>
        </div>
      </div>

      <div className="card-body">
        {/* HERO BANNER */}
        <div className={`decision-hero ${isAi ? 'ai' : 'human'}`}>
          <div className="decision-badge-wrap">
            <div className="decision-icon-box">
              {isAi ? <Bot size={28} /> : <UserCheck size={28} />}
            </div>
            <div className="decision-title-group">
              <h2>{isAi ? 'RESOLVE VIA AI REPLY' : 'ESCALATE TO HUMAN AGENT'}</h2>
              <p>
                {isAi 
                  ? 'Safe for autonomous customer resolution based on high confidence and compliant sentiment.'
                  : 'Automated response withheld. Case routed to priority specialist desk.'}
              </p>
            </div>
          </div>
        </div>

        {/* REASON CALLOUT */}
        <div className={`reason-box ${result.is_anomaly ? 'anomaly' : isAi ? 'ai' : 'human'}`}>
          <div className="reason-title">Routing Decision Rationale</div>
          <div className="reason-text">{result.reason}</div>
        </div>

        {/* FEATURE 1: DUAL ANOMALY DETECTION (DBSCAN + ISOLATION FOREST) */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.65)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.85rem 1rem',
          marginBottom: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              <ShieldCheck size={16} style={{ color: result.ensemble_anomaly ? 'var(--color-neg)' : 'var(--color-pos)' }} />
              <span>Dual Anomaly Detection (DBSCAN + Isolation Forest)</span>
            </div>
            <span style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '0.2rem 0.55rem',
              borderRadius: '999px',
              background: result.ensemble_anomaly ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              color: result.ensemble_anomaly ? '#f43f5e' : '#10b981',
              border: `1px solid ${result.ensemble_anomaly ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
            }}>
              {result.anomaly_consensus || (result.is_anomaly ? 'Outlier Flagged' : 'In-Distribution')}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
            {/* DBSCAN Metric */}
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>1. DBSCAN Density</span>
                <span style={{ fontWeight: 600, color: result.dbscan_anomaly ? 'var(--color-neg)' : 'var(--color-pos)' }}>
                  {result.dbscan_anomaly ? 'Anomaly' : 'Inlier'}
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                {result.dbscan_score !== undefined ? `${result.dbscan_score.toFixed(3)} cos dist` : `${result.anomaly_score.toFixed(2)}x eps`}
              </div>
              <div className="metric-bar-bg" style={{ marginTop: '0.35rem' }}>
                <div 
                  className="metric-bar-fill" 
                  style={{ 
                    width: `${Math.min(100, Math.max(8, (result.dbscan_score || result.anomaly_score || 0) * 100))}%`,
                    backgroundColor: result.dbscan_anomaly ? 'var(--color-neg)' : 'var(--color-pos)'
                  }}
                />
              </div>
            </div>

            {/* Isolation Forest Metric */}
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>2. Isolation Forest</span>
                <span style={{ fontWeight: 600, color: result.isolation_forest_anomaly ? 'var(--color-neg)' : 'var(--color-pos)' }}>
                  {result.isolation_forest_anomaly ? 'Anomaly' : 'Inlier'}
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                {result.isolation_forest_score !== undefined ? `${(result.isolation_forest_score * 100).toFixed(1)}% score` : 'Ensemble OK'}
              </div>
              <div className="metric-bar-bg" style={{ marginTop: '0.35rem' }}>
                <div 
                  className="metric-bar-fill" 
                  style={{ 
                    width: `${Math.min(100, Math.max(8, (result.isolation_forest_score || 0.1) * 100))}%`,
                    backgroundColor: result.isolation_forest_anomaly ? 'var(--color-neg)' : 'var(--color-pos)'
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* METRICS GRID */}
        <div className="metrics-grid" style={{ marginBottom: '1rem' }}>
          {/* Sentiment Metric */}
          <div className="metric-card">
            <div className="metric-header">
              <span>Sentiment Analysis</span>
              <SentIcon size={14} style={{ color: sentDetails.color }} />
            </div>
            <div className="metric-val" style={{ color: sentDetails.color, fontSize: '1rem' }}>
              {result.sentiment}
            </div>
            <div className="metric-bar-bg">
              <div 
                className="metric-bar-fill" 
                style={{ 
                  width: `${Math.min(100, Math.max(10, Math.abs(result.sentiment_scores?.compound || 0) * 100))}%`,
                  backgroundColor: sentDetails.color
                }}
              />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Compound: {result.sentiment_scores?.compound} | Neg: {(result.sentiment_scores?.neg * 100).toFixed(0)}%
            </div>
          </div>

          {/* Similarity Metric */}
          <div className="metric-card">
            <div className="metric-header">
              <span>Cluster Similarity</span>
              <Activity size={14} style={{ color: result.similarity >= threshold ? 'var(--color-ai)' : 'var(--color-human)' }} />
            </div>
            <div className="metric-val" style={{ 
              color: result.similarity >= threshold ? 'var(--color-ai)' : 'var(--color-human)',
              fontSize: '1rem'
            }}>
              {(result.similarity * 100).toFixed(1)}%
            </div>
            <div className="metric-bar-bg">
              <div 
                className="metric-bar-fill" 
                style={{ 
                  width: `${Math.min(100, result.similarity * 100)}%`,
                  backgroundColor: result.similarity >= threshold ? 'var(--color-ai)' : 'var(--color-human)'
                }}
              />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Threshold: {(threshold * 100).toFixed(0)}% ({result.similarity >= threshold ? 'Pass' : 'Below'})
            </div>
          </div>

          {/* HDBSCAN / Hierarchical Status */}
          <div className="metric-card">
            <div className="metric-header">
              <span>HDBSCAN Membership</span>
              <GitBranch size={14} style={{ color: 'var(--accent-primary)' }} />
            </div>
            <div className="metric-val" style={{ color: 'var(--accent-primary)', fontSize: '0.92rem' }}>
              Density Inlier
            </div>
            <div className="metric-bar-bg">
              <div 
                className="metric-bar-fill" 
                style={{ 
                  width: `${Math.min(100, (result.hdbscan_probability || 0.85) * 100)}%`,
                  backgroundColor: 'var(--accent-primary)'
                }}
              />
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Prob: {((result.hdbscan_probability || 0.85) * 100).toFixed(0)}% | Scale-Free
            </div>
          </div>
        </div>

        {/* CLUSTER ASSIGNMENT */}
        <div style={{ 
          background: 'var(--bg-elevated)', 
          padding: '0.85rem 1rem', 
          borderRadius: 'var(--radius-sm)', 
          border: '1px solid var(--border-subtle)',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Matched Complaint Cluster & HDBSCAN Hierarchy
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
              Cluster #{result.cluster_id + 1}: {result.cluster_name}
            </div>
          </div>
          <div className="keywords-wrap">
            {result.cluster_keywords?.slice(0, 4).map((kw, i) => (
              <span key={i} className="keyword-tag">{kw}</span>
            ))}
          </div>
        </div>

        {/* FEATURE 2: DYNAMIC LLM / RAG RESPONSE GENERATION */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          overflow: 'hidden',
          marginBottom: '1.25rem'
        }}>
          {/* Tab Selector: RAG vs Standard */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(30, 41, 59, 0.7)',
            padding: '0.5rem 0.85rem',
            borderBottom: '1px solid rgba(255,255,255,0.06)'
          }}>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                onClick={() => setActiveReplyTab('rag')}
                style={{
                  background: activeReplyTab === 'rag' ? 'var(--accent-primary)' : 'transparent',
                  color: activeReplyTab === 'rag' ? '#fff' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  transition: 'all 0.2s'
                }}
              >
                <Sparkles size={13} />
                <span>Dynamic LLM / RAG Reply</span>
              </button>

              <button
                onClick={() => setActiveReplyTab('template')}
                style={{
                  background: activeReplyTab === 'template' ? 'rgba(255,255,255,0.1)' : 'transparent',
                  color: activeReplyTab === 'template' ? '#fff' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  transition: 'all 0.2s'
                }}
              >
                <FileText size={13} />
                <span>Standard Template</span>
              </button>
            </div>

            <span style={{ fontSize: '0.7rem', color: '#818cf8', fontWeight: 600 }}>
              {rag?.engine_used || 'RAG Policy Engine'}
            </span>
          </div>

          {/* RAG RESPONSE VIEW */}
          {activeReplyTab === 'rag' && rag ? (
            <div style={{ padding: '1rem' }}>
              {/* EXTRACTED ENTITIES BADGES */}
              <div style={{ marginBottom: '0.85rem' }}>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.4rem' }}>
                  Extracted Operational Entities:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {entities.flight_number && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.74rem', background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', padding: '0.2rem 0.55rem', borderRadius: '4px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                      <Plane size={12} /> {entities.flight_number}
                    </span>
                  )}
                  {entities.booking_reference && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.74rem', background: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', padding: '0.2rem 0.55rem', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      <Tag size={12} /> PNR: {entities.booking_reference}
                    </span>
                  )}
                  {entities.monetary_amount && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.74rem', background: 'rgba(245, 158, 11, 0.15)', color: '#fcd34d', padding: '0.2rem 0.55rem', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      <DollarSign size={12} /> {entities.monetary_amount}
                    </span>
                  )}
                  {entities.duration && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.74rem', background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6', padding: '0.2rem 0.55rem', borderRadius: '4px', border: '1px solid rgba(236, 72, 153, 0.3)' }}>
                      <Clock size={12} /> {entities.duration}
                    </span>
                  )}
                  {entities.locations?.length > 0 && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.74rem', background: 'rgba(6, 182, 212, 0.15)', color: '#67e8f9', padding: '0.2rem 0.55rem', borderRadius: '4px', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
                      <MapPin size={12} /> {entities.locations.join(' • ')}
                    </span>
                  )}
                  {!entities.flight_number && !entities.monetary_amount && !entities.duration && entities.locations?.length === 0 && (
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      General operational inquiry (no specific flight or monetary tags identified)
                    </span>
                  )}
                </div>
              </div>

              {/* RETRIEVED POLICY CITATION */}
              {rag.retrieved_policy && (
                <div style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.6rem 0.85rem',
                  marginBottom: '0.85rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontSize: '0.74rem', fontWeight: 700, color: '#c7d2fe', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <FileText size={13} />
                      <span>Retrieved Policy: {rag.retrieved_policy.title}</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      {rag.retrieved_policy.citation}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.3rem', lineHeight: 1.4 }}>
                    {rag.retrieved_policy.summary}
                  </div>
                </div>
              )}

              {/* GENERATED EMAIL PREVIEW */}
              <div style={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.85rem 1rem'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  paddingBottom: '0.5rem',
                  marginBottom: '0.65rem'
                }}>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    <span style={{ color: 'var(--text-muted)' }}>Subject: </span>
                    {rag.email_subject}
                  </div>
                  <button 
                    onClick={() => handleCopy(`${rag.email_subject}\n\n${rag.email_body}`)}
                    style={{
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: copied ? 'var(--color-pos)' : 'var(--text-muted)',
                      borderRadius: '4px',
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.7rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      cursor: 'pointer'
                    }}
                  >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copied ? 'Copied' : 'Copy Email'}</span>
                  </button>
                </div>

                <div style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-line'
                }}>
                  {rag.email_body}
                </div>
              </div>
            </div>
          ) : (
            /* STANDARD TEMPLATE VIEW */
            <div style={{ padding: '1rem' }}>
              <div className="reply-container" style={{ margin: 0 }}>
                <div className="reply-header">
                  <div className="reply-badge">
                    <Bot size={14} />
                    <span>{isAi ? 'Suggested AI Reply to Customer' : 'Customer Escalation & Agent Handoff Ticket'}</span>
                  </div>
                  <button 
                    className="copy-btn" 
                    onClick={() => handleCopy(result.suggested_reply)}
                    title="Copy message to clipboard"
                  >
                    {copied ? <Check size={15} style={{ color: 'var(--color-ai)' }} /> : <Copy size={15} />}
                  </button>
                </div>
                <div className="reply-body">
                  {result.suggested_reply}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* NLP PREPROCESSING INSPECTOR */}
        <div className="nlp-inspector">
          <div 
            className="nlp-inspector-summary"
            onClick={() => setShowTokens(!showTokens)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Code2 size={14} />
              <span>spaCy NLP & Dual Anomaly Details</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--accent-primary)' }}>
              {showTokens ? 'Hide' : 'Inspect Lemmatized Tokens'}
            </span>
          </div>

          {showTokens && (
            <div style={{ marginTop: '0.75rem' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Cleaned text (lowercased, stopwords removed, lemmatized):
              </div>
              <div className="nlp-tokens">
                {result.cleaned_text ? (
                  result.cleaned_text.split(' ').map((token, i) => (
                    <span key={i} className="nlp-token">{token}</span>
                  ))
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>No content after stopword filtering</span>
                )}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.5 }}>
                • <strong>Transformer:</strong> <code>all-MiniLM-L6-v2</code> (384-dimensional dense vector)<br />
                • <strong>Dual Anomaly:</strong> DBSCAN: {result.dbscan_anomaly ? 'Outlier' : 'Normal'} | IsoForest: {result.isolation_forest_anomaly ? 'Outlier' : 'Normal'}<br />
                • <strong>HDBSCAN Group:</strong> {result.hdbscan_cluster_name} (Prob: {((result.hdbscan_probability || 0.85) * 100).toFixed(0)}%)<br />
                • <strong>2D PCA Point:</strong> [{result.pca_coordinates?.[0]}, {result.pca_coordinates?.[1]}]
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
