import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import '../../styles/main.css';
import './PipelineDashboard.css';
import {
  FiGitBranch, FiCheckCircle, FiXCircle, FiClock,
  FiRefreshCw, FiPlay, FiStopCircle, FiSearch,
  FiPlus, FiActivity, FiZap, FiGlobe, FiServer,
  FiLayers, FiExternalLink, FiTerminal, FiTrash2,
} from 'react-icons/fi';
import { FaGithub, FaRobot, FaCloud } from 'react-icons/fa';
import toast from 'react-hot-toast';
import { pipelineAPI } from '../../api/assistant';

// ============================================
// Create Pipeline Modal
// ============================================
const CreatePipelineModal = ({ isOpen, onClose, onCreate }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [deployMethod, setDeployMethod] = useState('self-host');
  const [maxAttempts, setMaxAttempts] = useState(50);
  const [autoDeploy, setAutoDeploy] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRepoUrl('');
      setDeployMethod('self-host');
      setMaxAttempts(50);
      setAutoDeploy(true);
      setCreating(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const methods = [
    {
      value: 'self-host',
      label: 'Self-Host (Agent)',
      icon: FaRobot,
      desc: 'Full CI/CD + auto-deploy',
      badge: 'Recommended',
      gradient: 'linear-gradient(135deg, #a855f7, #6366f1)',
    },
    {
      value: 'vercel',
      label: 'Vercel',
      icon: FiGlobe,
      desc: 'Frontend + CI/CD',
      gradient: 'linear-gradient(135deg, #1e293b, #0f172a)',
    },
    {
      value: 'netlify',
      label: 'Netlify',
      icon: FaCloud,
      desc: 'Static sites + CI/CD',
      gradient: 'linear-gradient(135deg, #14b8a6, #06b6d4)',
    },
    {
      value: 'render',
      label: 'Render',
      icon: FiServer,
      desc: 'Backend + CI/CD',
      gradient: 'linear-gradient(135deg, #a855f7, #ec4899)',
    },
  ];

  const handleCreate = async () => {
    if (!repoUrl.trim()) return toast.error('Please enter a GitHub repo URL');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs are supported');

    setCreating(true);
    try {
      await onCreate({ repoUrl: repoUrl.trim(), deployMethod, maxAttempts, autoDeploy });
      onClose();
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="modal-content"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-left">
            <div className="modal-header-icon">
              <FiZap />
            </div>
            <div>
              <h2 className="modal-title">Create CI/CD Pipeline</h2>
              <p className="modal-subtitle">Generate + auto-fix + auto-deploy</p>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>
            <FiXCircle />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Repo URL */}
          <div className="modal-field">
            <label className="modal-label">📦 GitHub Repository</label>
            <div className="modal-input-wrapper">
              <FaGithub className="modal-input-icon" />
              <input
                type="text"
                value={repoUrl}
                onChange={e => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                className="modal-input"
                autoFocus
              />
            </div>
            <p className="modal-hint">💡 Pipeline will be generated, committed, and monitored automatically</p>
          </div>

          {/* Deploy Method */}
          <div className="modal-field">
            <label className="modal-label">🚀 Deploy Method</label>
            <div className="method-grid">
              {methods.map(({ value, label, icon: Icon, desc, badge, gradient }) => (
                <button
                  key={value}
                  className={`method-card ${deployMethod === value ? 'active' : ''}`}
                  onClick={() => setDeployMethod(value)}
                >
                  <div className="method-card-icon" style={{ background: gradient }}>
                    <Icon />
                  </div>
                  <div className="method-card-info">
                    <div className="method-card-title-row">
                      <span className="method-card-title">{label}</span>
                      {badge && <span className="method-badge">{badge}</span>}
                    </div>
                    <p className="method-card-desc">{desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Max Attempts */}
          <div className="modal-field">
            <label className="modal-label">🔁 Max Auto-Fix Attempts</label>
            <div className="range-wrapper">
              <input
                type="range"
                min="5"
                max="100"
                step="5"
                value={maxAttempts}
                onChange={e => setMaxAttempts(parseInt(e.target.value))}
                className="range-slider"
              />
              <div className="range-value">{maxAttempts}</div>
            </div>
            <p className="modal-hint">🩺 HealerAgent will retry this many times to fix errors</p>
          </div>

          {/* Auto Deploy */}
          <label className="checkbox-wrapper">
            <input
              type="checkbox"
              className="checkbox-input"
              checked={autoDeploy}
              onChange={e => setAutoDeploy(e.target.checked)}
            />
            <div className="checkbox-info">
              <div className="checkbox-title">🚀 Auto-deploy after pipeline passes</div>
              <div className="checkbox-desc">If disabled, deploy manually later</div>
            </div>
          </label>

          {/* Summary */}
          <div className="modal-summary">
            <div className="modal-summary-label">Pipeline Summary</div>
            <div className="modal-summary-value">
              {deployMethod === 'self-host' ? 'Self-Host' : deployMethod.charAt(0).toUpperCase() + deployMethod.slice(1)} • {maxAttempts} attempts • {autoDeploy ? 'Auto-deploy' : 'Manual'}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="modal-btn cancel" onClick={onClose} disabled={creating}>
            Cancel
          </button>
          <button
            className="modal-btn primary"
            onClick={handleCreate}
            disabled={creating || !repoUrl.trim()}
          >
            {creating ? (
              <>
                <FiRefreshCw style={{ animation: 'spin 1s linear infinite' }} />
                Creating...
              </>
            ) : (
              <>
                <FiZap />
                Create Pipeline
              </>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ============================================
// Pipeline Card
// ============================================
const PipelineCard = ({ pipeline, onTrigger, onRetry, onCancel, onViewDetails, onDelete }) => {
  const statusConfig = {
    running: { icon: FiActivity, label: 'Running' },
    success: { icon: FiCheckCircle, label: 'Live' },
    failed: { icon: FiXCircle, label: 'Failed' },
    pending: { icon: FiClock, label: 'Pending' },
    cancelled: { icon: FiStopCircle, label: 'Stopped' },
  };
  const sc = statusConfig[pipeline.status] || statusConfig.pending;
  const StatusIcon = sc.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`pipeline-card ${pipeline.status}`}
    >
      <div className="pipeline-card-header">
        <div className="pipeline-card-left">
          <div className={`pipeline-status-icon ${pipeline.status}`}>
            <StatusIcon />
          </div>
          <div className="pipeline-info">
            <div className="pipeline-name-row">
              <h3 className="pipeline-name">{pipeline.name}</h3>
              <div className="pipeline-status-badge">
                <StatusIcon />
                {sc.label}
              </div>
            </div>
            <div className="pipeline-meta">
              <span className="pipeline-meta-item">
                <FaGithub />
                {pipeline.repo}
              </span>
              {pipeline.deployType && (
                <span className="pipeline-meta-item">
                  <FiLayers />
                  {pipeline.deployType}
                </span>
              )}
              {pipeline.duration && pipeline.duration !== '—' && (
                <span className="pipeline-meta-item">
                  <FiClock />
                  {pipeline.duration}
                </span>
              )}
            </div>
          </div>
        </div>

        {pipeline.url && (
          <a
            href={pipeline.url}
            target="_blank"
            rel="noopener noreferrer"
            className="pipeline-live-link"
          >
            <FiExternalLink />
            Live
          </a>
        )}
      </div>

      {/* Steps */}
      <div className="pipeline-steps">
        {(pipeline.steps || []).map((step, i) => (
          <React.Fragment key={i}>
            <div className={`pipeline-step ${step.status}`}>
              <div className={`pipeline-step-dot ${step.status}`} />
              <span className="pipeline-step-label">{step.name}</span>
            </div>
            {i < pipeline.steps.length - 1 && (
              <div className={`pipeline-step-line ${step.status === 'completed' ? 'completed' : ''}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Progress */}
      <div className="pipeline-progress">
        <div className="pipeline-progress-track">
          <div
            className={`pipeline-progress-fill ${pipeline.status}`}
            style={{ width: `${pipeline.progress || 0}%` }}
          />
        </div>
        <span className="pipeline-progress-value">{pipeline.progress || 0}%</span>
      </div>

      {/* Actions */}
      <div className="pipeline-actions">
        {pipeline.status === 'failed' || pipeline.status === 'pending' ? (
          <button onClick={() => onTrigger(pipeline.id)} className="action-btn trigger">
            <FiPlay />
            Trigger
          </button>
        ) : pipeline.status === 'running' ? (
          <button onClick={() => onCancel(pipeline.id)} className="action-btn stop">
            <FiStopCircle />
            Stop
          </button>
        ) : pipeline.status === 'success' ? (
          <button onClick={() => onRetry(pipeline.id)} className="action-btn redeploy">
            <FiRefreshCw />
            Redeploy
          </button>
        ) : null}

        <button onClick={() => onViewDetails(pipeline.id)} className="action-btn logs">
          <FiTerminal />
          Logs
        </button>

        <button onClick={() => onDelete(pipeline.id)} className="action-btn delete" title="Delete">
          <FiTrash2 />
        </button>
      </div>
    </motion.div>
  );
};

// ============================================
// Main Dashboard
// ============================================
const PipelineDashboard = () => {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const navigate = useNavigate();

  const fetchPipelines = useCallback(async () => {
    try {
      const data = await pipelineAPI.getAll();
      setPipelines(data || []);
    } catch (err) {
      console.error('Fetch pipelines error:', err);
      setPipelines([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPipelines();
    const interval = setInterval(fetchPipelines, 10000);
    return () => clearInterval(interval);
  }, [fetchPipelines]);

  const handleCreate = async (config) => {
    toast.loading('Creating pipeline...', { id: 'create' });
    const result = await pipelineAPI.create(config);
    if (result.success) {
      toast.success('Pipeline created successfully!', { id: 'create' });
      fetchPipelines();
    } else {
      toast.error(result.error || 'Failed to create pipeline', { id: 'create' });
    }
  };

  const handleTrigger = async (id) => {
    toast.loading('Triggering pipeline...', { id: 'trigger' });
    const result = await pipelineAPI.trigger(id);
    if (result.success) {
      toast.success('Pipeline triggered!', { id: 'trigger' });
      fetchPipelines();
    } else {
      toast.error(result.error || 'Failed to trigger', { id: 'trigger' });
    }
  };

  const handleRetry = async (id) => {
    toast.loading('Redeploying...', { id: 'retry' });
    const result = await pipelineAPI.retry(id);
    if (result.success) {
      toast.success('Redeployed successfully!', { id: 'retry' });
      fetchPipelines();
    } else {
      toast.error(result.error || 'Failed to redeploy', { id: 'retry' });
    }
  };

  const handleCancel = async (id) => {
    toast.loading('Stopping...', { id: 'cancel' });
    const result = await pipelineAPI.cancel(id);
    if (result.success) {
      toast.success('Pipeline stopped!', { id: 'cancel' });
      fetchPipelines();
    } else {
      toast.error(result.error || 'Failed to stop', { id: 'cancel' });
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this pipeline?')) return;
    await handleCancel(id);
  };

  const handleStatClick = (status) => {
    setFilter(status);
  };

  const filteredPipelines = pipelines.filter(p => {
    const matchesFilter = filter === 'all' || p.status === filter;
    const matchesSearch = !searchTerm ||
      p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.repo?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const counts = {
    all: pipelines.length,
    running: pipelines.filter(p => p.status === 'running').length,
    success: pipelines.filter(p => p.status === 'success').length,
    failed: pipelines.filter(p => p.status === 'failed').length,
    pending: pipelines.filter(p => p.status === 'pending').length,
    cancelled: pipelines.filter(p => p.status === 'cancelled').length,
  };

  return (
    <div className="pipeline-dashboard">
      {/* Header */}
      <div className="pipeline-header">
        <div className="pipeline-header-left">
          <h1 className="pipeline-title">
            <div className="pipeline-title-icon">
              <FiGitBranch />
            </div>
            CI/CD Pipelines
          </h1>
          <p className="pipeline-subtitle">Manage, monitor, and deploy your projects</p>
        </div>
        <div className="pipeline-header-actions">
          <button className="pipeline-refresh-btn" onClick={fetchPipelines} title="Refresh">
            <FiRefreshCw className={loading ? 'spinning' : ''} />
          </button>
          <button className="pipeline-new-btn" onClick={() => setShowCreateModal(true)}>
            <FiPlus />
            New Pipeline
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="pipeline-stats">
        <div className="stat-card" style={{ '--stat-color': '#a855f7' }} onClick={() => handleStatClick('all')}>
          <div className="stat-card-header">
            <span className="stat-label">Total</span>
            <div className="stat-icon"><FiGitBranch /></div>
          </div>
          <div className="stat-value">{counts.all}</div>
          <div className="stat-sub">All pipelines</div>
        </div>

        <div className="stat-card" style={{ '--stat-color': '#10b981' }} onClick={() => handleStatClick('success')}>
          <div className="stat-card-header">
            <span className="stat-label">Live</span>
            <div className="stat-icon"><FiCheckCircle /></div>
          </div>
          <div className="stat-value">{counts.success}</div>
          <div className="stat-sub">Deployed & running</div>
        </div>

        <div className="stat-card" style={{ '--stat-color': '#ef4444' }} onClick={() => handleStatClick('failed')}>
          <div className="stat-card-header">
            <span className="stat-label">Failed</span>
            <div className="stat-icon"><FiXCircle /></div>
          </div>
          <div className="stat-value">{counts.failed}</div>
          <div className="stat-sub">Need attention</div>
        </div>

        <div className="stat-card" style={{ '--stat-color': '#3b82f6' }} onClick={() => handleStatClick('running')}>
          <div className="stat-card-header">
            <span className="stat-label">Running</span>
            <div className="stat-icon"><FiActivity /></div>
          </div>
          <div className="stat-value">{counts.running}</div>
          <div className="stat-sub">In progress</div>
        </div>
      </div>

      {/* Filters */}
      <div className="pipeline-filters">
        <div className="filter-pills">
          {['all', 'running', 'success', 'failed', 'pending'].map(status => (
            <button
              key={status}
              className={`filter-pill ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {counts[status] > 0 && <span className="filter-count">{counts[status]}</span>}
            </button>
          ))}
        </div>
        <div className="search-wrapper">
          <FiSearch className="search-icon" />
          <input
            type="text"
            className="search-input"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search pipelines..."
          />
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="pipeline-list">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="pipeline-skeleton">
              <div className="skeleton-row short" />
              <div className="skeleton-row medium" />
              <div className="skeleton-row full" />
            </div>
          ))}
        </div>
      ) : filteredPipelines.length === 0 ? (
        <div className="pipeline-empty">
          <div className="pipeline-empty-icon">
            <FiGitBranch />
          </div>
          <h3 className="pipeline-empty-title">
            {searchTerm || filter !== 'all' ? 'No pipelines match your filters' : 'No pipelines yet'}
          </h3>
          <p className="pipeline-empty-text">
            {searchTerm || filter !== 'all'
              ? 'Try adjusting your search or filter settings'
              : 'Create your first CI/CD pipeline to get started with automated deployments'}
          </p>
          {!searchTerm && filter === 'all' && (
            <button className="pipeline-empty-btn" onClick={() => setShowCreateModal(true)}>
              <FiPlus />
              Create First Pipeline
            </button>
          )}
        </div>
      ) : (
        <div className="pipeline-list">
          <AnimatePresence>
            {filteredPipelines.map(p => (
              <PipelineCard
                key={p.id}
                pipeline={p}
                onTrigger={handleTrigger}
                onRetry={handleRetry}
                onCancel={handleCancel}
                onViewDetails={(id) => navigate(`/pipelines/${id}`)}
                onDelete={handleDelete}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Footer */}
      <div className="pipeline-footer">
        <span>
          <span className="pipeline-footer-dot"></span>
          {filteredPipelines.length} of {pipelines.length} pipelines
        </span>
        <span>Auto-refresh: 10s</span>
      </div>

      <CreatePipelineModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />
    </div>
  );
};

export default PipelineDashboard;