import React from 'react';
import { Bot, Network, Layers, Database, ListChecks, Sparkles, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, status }) {
  const tabs = [
    { id: 'decision', label: 'AI Routing Decision', icon: Bot },
    { id: 'visualize', label: '2D PCA Cluster Map', icon: Network },
    { id: 'clusters', label: 'Cluster Taxonomy', icon: Layers },
    { id: 'train', label: 'Model & Dataset Studio', icon: Database },
    { id: 'batch', label: 'Batch Triage', icon: ListChecks },
  ];

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-group">
          <div className="logo-icon">
            <Sparkles size={22} />
          </div>
          <div className="logo-text">
            <h1>AutoRoute AI</h1>
            <span>Intelligent Customer Complaint Routing & Reply Decision System</span>
          </div>
        </div>

        <nav className="nav-tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${isActive ? 'active' : ''}`}
                id={`tab-${tab.id}`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="header-status">
          <div className="status-badge" title={`Dataset: ${status?.dataset_name || 'Loading...'}`}>
            <span className="status-dot"></span>
            <span>{status?.is_trained ? `${status.n_clusters} Clusters Ready` : 'Initializing...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
