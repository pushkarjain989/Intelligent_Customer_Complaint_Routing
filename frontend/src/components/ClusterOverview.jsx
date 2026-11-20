import React from 'react';
import { Layers, Tag, Quote, ArrowRight, Smile, Meh, Frown } from 'lucide-react';

const CLUSTER_COLORS = [
  '#6366f1',
  '#10b981',
  '#a855f7',
  '#06b6d4',
  '#f59e0b',
  '#ec4899',
  '#3b82f6',
  '#14b8a6',
];

export default function ClusterOverview({ clusters, onSelectSample }) {
  if (!clusters || clusters.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
        <Layers size={32} style={{ color: 'var(--text-muted)', margin: '0 auto 1rem auto' }} />
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>No Cluster Data Available</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Please initialize or train the clustering pipeline to view the discovered topic clusters.
        </p>
      </div>
    );
  }

  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'Positive') return <Smile size={14} style={{ color: 'var(--color-pos)' }} />;
    if (sentiment === 'Negative') return <Frown size={14} style={{ color: 'var(--color-neg)' }} />;
    return <Meh size={14} style={{ color: 'var(--color-neu)' }} />;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.35rem' }}>
          Discovered Complaint Cluster Taxonomy
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Unsupervised KMeans clustering on SentenceTransformer embeddings with automated TF-IDF topic keyword extraction.
          Click any sample complaint to test it in the decision engine.
        </p>
      </div>

      <div className="clusters-grid">
        {clusters.map((cluster) => {
          const color = CLUSTER_COLORS[cluster.id % CLUSTER_COLORS.length];
          return (
            <div key={cluster.id} className="cluster-card" id={`cluster-card-${cluster.id}`}>
              <div className="cluster-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span 
                    className="cluster-pill"
                    style={{ backgroundColor: `${color}25`, color: color, border: `1px solid ${color}50` }}
                  >
                    Cluster #{cluster.id + 1}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {getSentimentIcon(cluster.sentiment)}
                    <span>{cluster.sentiment}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {cluster.name}
                </h3>
              </div>

              {/* TF-IDF Keywords */}
              <div>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Key Feature Terms
                </div>
                <div className="keywords-wrap">
                  {cluster.keywords?.map((kw, idx) => (
                    <span key={idx} className="keyword-tag">#{kw}</span>
                  ))}
                </div>
              </div>

              {/* Representative Examples */}
              {cluster.examples && cluster.examples.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.35rem' }}>
                    Representative Training Sample
                  </div>
                  <div 
                    className="cluster-sample-text"
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelectSample(cluster.examples[0])}
                    title="Click to load into decision engine"
                  >
                    "{cluster.examples[0]}"
                  </div>
                  <button
                    onClick={() => onSelectSample(cluster.examples[0])}
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.3rem', 
                      background: 'transparent', 
                      border: 'none', 
                      color: 'var(--accent-primary)', 
                      fontSize: '0.75rem', 
                      fontWeight: 600, 
                      cursor: 'pointer',
                      marginTop: '0.4rem',
                      padding: 0
                    }}
                  >
                    <span>Test This Sample in Routing</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
