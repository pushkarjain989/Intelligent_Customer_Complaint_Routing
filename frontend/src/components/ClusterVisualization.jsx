import React, { useRef, useEffect, useState, useMemo } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Layers, 
  AlertTriangle, 
  Compass, 
  Info,
  Maximize2,
  GitBranch,
  Network,
  Activity,
  Layers2,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

const CLUSTER_COLORS = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#a855f7', // Purple
  '#06b6d4', // Cyan
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#3b82f6', // Blue
  '#14b8a6', // Teal
];

export default function ClusterVisualization({ visData, hierarchyData, activePoint, isLoading, isCompact = false }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // View Mode: 'pca', 'dendrogram', 'hdbscan'
  const [viewMode, setViewMode] = useState('pca');

  // Viewport transformation state for PCA
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Filter toggles
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);
  const [showCentroids, setShowCentroids] = useState(true);

  // Compute bounding box of PCA points
  const bounds = useMemo(() => {
    if (!visData?.points || visData.points.length === 0) {
      return { minX: -5, maxX: 5, minY: -5, maxY: 5 };
    }
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    visData.points.forEach((p) => {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    });
    const padX = (maxX - minX) * 0.1 || 1;
    const padY = (maxY - minY) * 0.1 || 1;
    return {
      minX: minX - padX,
      maxX: maxX + padX,
      minY: minY - padY,
      maxY: maxY + padY,
    };
  }, [visData]);

  // Coordinate mapping function
  const mapCoords = (x, y, width, height) => {
    const scaleX = width / (bounds.maxX - bounds.minX);
    const scaleY = height / (bounds.maxY - bounds.minY);
    const scale = Math.min(scaleX, scaleY) * zoom;
    const centerX = width / 2;
    const centerY = height / 2;
    const dataMidX = (bounds.minX + bounds.maxX) / 2;
    const dataMidY = (bounds.minY + bounds.maxY) / 2;

    const px = centerX + (x - dataMidX) * scale + offset.x;
    const py = centerY - (y - dataMidY) * scale + offset.y;
    return { px, py };
  };

  const invMapCoords = (px, py, width, height) => {
    const scaleX = width / (bounds.maxX - bounds.minX);
    const scaleY = height / (bounds.maxY - bounds.minY);
    const scale = Math.min(scaleX, scaleY) * zoom;
    const centerX = width / 2;
    const centerY = height / 2;
    const dataMidX = (bounds.minX + bounds.maxX) / 2;
    const dataMidY = (bounds.minY + bounds.maxY) / 2;

    const x = (px - centerX - offset.x) / scale + dataMidX;
    const y = -(py - centerY - offset.y) / scale + dataMidY;
    return { x, y };
  };

  // Canvas render loop
  useEffect(() => {
    if (viewMode !== 'pca') return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    let animationId;
    let pulseAngle = 0;

    const render = () => {
      pulseAngle += 0.05;
      ctx.clearRect(0, 0, width, height);

      // Grid background
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const step = 40 * zoom;
      const offsetX = offset.x % step;
      const offsetY = offset.y % step;

      ctx.beginPath();
      for (let x = offsetX; x < width; x += step) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
      }
      for (let y = offsetY; y < height; y += step) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();

      // Axis lines
      const origin = mapCoords(0, 0, width, height);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.beginPath();
      ctx.moveTo(origin.px, 0);
      ctx.lineTo(origin.px, height);
      ctx.moveTo(0, origin.py);
      ctx.lineTo(width, origin.py);
      ctx.stroke();

      // Draw cluster points
      if (visData?.points) {
        visData.points.forEach((p) => {
          if (showAnomaliesOnly && !p.is_anomaly) return;

          const { px, py } = mapCoords(p.x, p.y, width, height);
          if (px < -20 || px > width + 20 || py < -20 || py > height + 20) return;

          const color = CLUSTER_COLORS[p.cluster_id % CLUSTER_COLORS.length];

          if (p.is_anomaly) {
            ctx.fillStyle = '#f59e0b';
            ctx.strokeStyle = '#d97706';
            ctx.lineWidth = 1.2;
            const s = 4.5 * Math.min(1.5, Math.max(0.7, zoom));
            ctx.beginPath();
            ctx.moveTo(px, py - s);
            ctx.lineTo(px + s, py);
            ctx.lineTo(px, py + s);
            ctx.lineTo(px - s, py);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
          } else {
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.65;
            const r = 3 * Math.min(1.4, Math.max(0.8, zoom));
            ctx.beginPath();
            ctx.arc(px, py, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
          }
        });
      }

      // Draw centroids
      if (showCentroids && visData?.centroids) {
        visData.centroids.forEach((c) => {
          const { px, py } = mapCoords(c.x, c.y, width, height);
          const color = CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length];

          ctx.fillStyle = color;
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(px, py, 7, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();

          if (zoom >= 0.8 && !isCompact) {
            ctx.font = '600 10px Inter, sans-serif';
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.shadowColor = 'rgba(0,0,0,0.8)';
            ctx.shadowBlur = 4;
            ctx.fillText(`C${c.cluster_id + 1}`, px, py - 11);
            ctx.shadowBlur = 0;
          }
        });
      }

      // Draw Active Query Point
      if (activePoint?.pca_coordinates) {
        const [qx, qy] = activePoint.pca_coordinates;
        const { px, py } = mapCoords(qx, qy, width, height);

        const pulse = 10 + Math.sin(pulseAngle) * 4;
        ctx.fillStyle = 'rgba(99, 102, 241, 0.25)';
        ctx.beginPath();
        ctx.arc(px, py, pulse, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = activePoint.decision === 'AI' ? '#10b981' : '#f43f5e';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(px, py, 6.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.font = '700 11px Inter, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText('★ Active Query', px, py - 13);
      }

      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [visData, zoom, offset, showAnomaliesOnly, showCentroids, activePoint, viewMode, isCompact]);

  // Mouse handlers for PCA canvas
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e) => {
    const rect = containerRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
      return;
    }

    if (!visData?.points) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    let closest = null;
    let minDist = 15;

    if (activePoint?.pca_coordinates) {
      const { px, py } = mapCoords(activePoint.pca_coordinates[0], activePoint.pca_coordinates[1], width, height);
      const d = Math.hypot(px - mx, py - my);
      if (d < minDist) {
        closest = {
          ...activePoint,
          snippet: activePoint.text,
          is_query: true,
        };
        minDist = d;
      }
    }

    if (!closest) {
      for (const p of visData.points) {
        if (showAnomaliesOnly && !p.is_anomaly) continue;
        const { px, py } = mapCoords(p.x, p.y, width, height);
        const d = Math.hypot(px - mx, py - my);
        if (d < minDist) {
          closest = p;
          minDist = d;
        }
      }
    }

    setHoveredPoint(closest);
    setTooltipPos({ x: mx + 15, y: my + 15 });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1.15 : 0.88;
    setZoom((z) => Math.min(6, Math.max(0.4, z * delta)));
  };

  const resetView = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  const dendro = hierarchyData?.dendrogram;
  const hdbscanSummary = hierarchyData?.hdbscan_summary || [];

  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      {/* HEADER WITH VIEW MODE TABS */}
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div className="card-title">
            <Compass size={18} className="text-accent" />
            <span>
              {viewMode === 'pca' && '2D PCA Dimensionality Reduction Scatter Space'}
              {viewMode === 'dendrogram' && 'Hierarchical Agglomerative Clustering (Dendrogram)'}
              {viewMode === 'hdbscan' && 'HDBSCAN Density-Based Cluster Architecture'}
            </span>
          </div>
          <div className="card-subtitle">
            {viewMode === 'pca' && 'Dense 384D transformer embeddings projected into 2D orthogonal coordinates.'}
            {viewMode === 'dendrogram' && 'Bottom-up cluster merges showing how sub-topics unite into parent service divisions.'}
            {viewMode === 'hdbscan' && 'Hierarchical scale-free density clustering without a fixed global epsilon distance.'}
          </div>
        </div>

        {!isCompact && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setViewMode('pca')}
              style={{
                background: viewMode === 'pca' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.06)',
                color: viewMode === 'pca' ? '#fff' : 'var(--text-secondary)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <Compass size={13} />
              <span>2D PCA Map</span>
            </button>

            <button
              onClick={() => setViewMode('dendrogram')}
              style={{
                background: viewMode === 'dendrogram' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.06)',
                color: viewMode === 'dendrogram' ? '#fff' : 'var(--text-secondary)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <GitBranch size={13} />
              <span>Hierarchical Dendrogram</span>
            </button>

            <button
              onClick={() => setViewMode('hdbscan')}
              style={{
                background: viewMode === 'hdbscan' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.06)',
                color: viewMode === 'hdbscan' ? '#fff' : 'var(--text-secondary)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <Layers2 size={13} />
              <span>HDBSCAN Clusters</span>
            </button>

            {viewMode === 'pca' && (
              <button
                className={`btn-secondary ${showAnomaliesOnly ? 'active' : ''}`}
                onClick={() => setShowAnomaliesOnly(!showAnomaliesOnly)}
                style={{ 
                  background: showAnomaliesOnly ? 'var(--color-anomaly-bg)' : 'var(--bg-elevated)',
                  color: showAnomaliesOnly ? 'var(--color-anomaly)' : 'var(--text-secondary)',
                  borderColor: showAnomaliesOnly ? 'var(--color-anomaly)' : 'var(--border-subtle)',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.75rem'
                }}
              >
                <AlertTriangle size={12} />
                <span>{showAnomaliesOnly ? 'Anomalies Only' : 'Filter Anomalies'}</span>
              </button>
            )}
          </div>
        )}
      </div>

      <div className="card-body" style={{ padding: viewMode === 'pca' ? '1rem' : '1.25rem' }}>
        {/* VIEW 1: 2D PCA CANVAS */}
        {viewMode === 'pca' && (
          <div 
            className="canvas-wrapper" 
            ref={containerRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            style={{ height: isCompact ? '220px' : '480px' }}
          >
            <canvas ref={canvasRef} className="pca-canvas" />

            <div className="canvas-toolbar">
              <button className="canvas-tool-btn" onClick={() => setZoom((z) => Math.min(6, z * 1.25))} title="Zoom In">
                <ZoomIn size={16} />
              </button>
              <button className="canvas-tool-btn" onClick={() => setZoom((z) => Math.max(0.4, z * 0.8))} title="Zoom Out">
                <ZoomOut size={16} />
              </button>
              <button className="canvas-tool-btn" onClick={resetView} title="Reset View">
                <RotateCcw size={16} />
              </button>
            </div>

            {hoveredPoint && (
              <div 
                className="canvas-tooltip"
                style={{ 
                  left: Math.min(tooltipPos.x, (containerRef.current?.clientWidth || 300) - 280),
                  top: Math.min(tooltipPos.y, (containerRef.current?.clientHeight || 200) - 130)
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ 
                    fontWeight: 700, 
                    color: hoveredPoint.is_query ? (hoveredPoint.decision === 'AI' ? '#10b981' : '#f43f5e') : 'var(--accent-primary)',
                    fontSize: '0.75rem' 
                  }}>
                    {hoveredPoint.is_query ? '★ Input Complaint' : hoveredPoint.cluster_name}
                  </span>
                  {hoveredPoint.is_anomaly && (
                    <span style={{ color: '#f59e0b', fontWeight: 700, fontSize: '0.7rem' }}>
                      [Anomaly]
                    </span>
                  )}
                </div>
                <div style={{ color: 'var(--text-secondary)', marginBottom: '0.35rem', lineHeight: 1.4 }}>
                  "{hoveredPoint.snippet}"
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  Sentiment: <strong style={{ color: '#ffffff' }}>{hoveredPoint.sentiment}</strong>
                </div>
              </div>
            )}

            {!isCompact && (
              <div className="canvas-legend">
                {visData?.clusters_summary?.map((c) => (
                  <div key={c.id} className="legend-item" title={c.keywords.join(', ')}>
                    <span className="legend-dot" style={{ backgroundColor: CLUSTER_COLORS[c.id % CLUSTER_COLORS.length] }}></span>
                    <span>C{c.id + 1}: {c.name.split('&')[0].trim()}</span>
                  </div>
                ))}
                <div className="legend-item">
                  <span className="legend-dot diamond" style={{ backgroundColor: '#f59e0b' }}></span>
                  <span style={{ color: '#f59e0b' }}>Dual Outlier</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* VIEW 2: HIERARCHICAL AGGLOMERATIVE DENDROGRAM */}
        {viewMode === 'dendrogram' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Academic explainer card */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.45)',
              padding: '0.85rem 1.15rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(255,255,255,0.06)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem'
            }}>
              <div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Ward's Minimum Variance Hierarchical Tree
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                  Bottom-up agglomeration links closest complaint sub-spaces until all merge into enterprise root.
                </div>
              </div>
              <span style={{ fontSize: '0.72rem', background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', padding: '0.25rem 0.6rem', borderRadius: '4px' }}>
                Distance Metric: Ward Cosine Variance
              </span>
            </div>

            {/* Hierarchical Merges Timeline & Tree */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              {dendro?.merges && dendro.merges.length > 0 ? (
                dendro.merges.map((merge) => (
                  <div key={merge.step} style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.85rem 1rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
                        Merge Step #{merge.step}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                        Ward Dist: {merge.distance}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.5rem' }}>
                      <span style={{ color: '#93c5fd' }}>{merge.source_a.split('&')[0]}</span>
                      <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                      <span style={{ color: '#a7f3d0' }}>{merge.source_b.split('&')[0]}</span>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.25)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                      <strong>Result:</strong> {merge.merged_label}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: '1rem' }}>
                  Hierarchy tree computed upon model training.
                </div>
              )}
            </div>

            {/* Base Leaf Clusters */}
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.65rem' }}>
                Base Leaf Clusters (Level 0 Inputs):
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.65rem' }}>
                {visData?.clusters_summary?.map((c, i) => (
                  <div key={c.id} style={{
                    background: 'rgba(30, 41, 59, 0.4)',
                    borderLeft: `3px solid ${CLUSTER_COLORS[c.id % CLUSTER_COLORS.length]}`,
                    padding: '0.65rem 0.85rem',
                    borderRadius: '0 4px 4px 0'
                  }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      C{c.id + 1}: {c.name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Keywords: {c.keywords?.slice(0, 3).join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: HDBSCAN DENSITY ARCHITECTURE */}
        {viewMode === 'hdbscan' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{
              background: 'rgba(30, 41, 59, 0.45)',
              padding: '0.85rem 1.15rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(255,255,255,0.06)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem'
            }}>
              <div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  HDBSCAN Scale-Free Density Architecture
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                  Constructs cluster tree across variable epsilon distances; persistent peaks form stable clusters.
                </div>
              </div>
              <span style={{ fontSize: '0.72rem', background: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', padding: '0.25rem 0.6rem', borderRadius: '4px' }}>
                min_cluster_size=12 • metric=cosine
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
              {hdbscanSummary.length > 0 ? (
                hdbscanSummary.map((hdb, idx) => (
                  <div key={hdb.id} style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.85rem 1rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: CLUSTER_COLORS[idx % CLUSTER_COLORS.length] }}>
                        HDBSCAN Component #{hdb.id + 1}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                        {hdb.percentage}% ({hdb.size} msgs)
                      </span>
                    </div>

                    <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.4, fontStyle: 'italic' }}>
                      "{hdb.sample || 'Standard cluster representative sample.'}"
                    </div>
                  </div>
                ))
              ) : (
                visData?.clusters_summary?.map((c) => (
                  <div key={c.id} style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.85rem 1rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: CLUSTER_COLORS[c.id % CLUSTER_COLORS.length] }}>
                        HDBSCAN Core: {c.name.split('&')[0]}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                        Persistent Inlier
                      </span>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                      Keywords: {c.keywords?.slice(0, 4).join(', ')}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
