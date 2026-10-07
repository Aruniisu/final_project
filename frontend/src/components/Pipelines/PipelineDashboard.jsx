import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import '../../styles/main.css';
import './PipelineDashboard.css';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import {
  FiGitBranch, FiCheckCircle, FiXCircle, FiClock,
  FiRefreshCw, FiPlay, FiStopCircle, FiSearch,
  FiPlus, FiActivity, FiZap,
  FiLayers, FiExternalLink, FiTerminal, FiTrash2, FiDownload,
} from 'react-icons/fi';
import { FaGithub, FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';
import { pipelineAPI } from '../../api/assistant';

const STUCK_THRESHOLD_MS = 90 * 1000;

const inferPipelineStatus = (pipeline) => {
  if (!pipeline) return pipeline;
  const status = pipeline.status;
  const steps = pipeline.steps || [];
  const progress = pipeline.progress || 0;
  const startedAt = pipeline.startedAt || pipeline.createdAt;
  if (['success', 'failed', 'cancelled'].includes(status)) return pipeline;
  let isStuck = false;
  if (startedAt && status === 'running') {
    const elapsed = Date.now() - new Date(startedAt).getTime();
    if (elapsed > STUCK_THRESHOLD_MS) isStuck = true;
  }
  const allStepsDone = steps.length > 0 && steps.every(
    s => s.status === 'completed' || s.status === 'success'
  );
  const anyStepFailed = steps.some(s => s.status === 'failed');
  if (anyStepFailed) {
    return {
      ...pipeline,
      status: 'failed',
      progress: 100,
      duration: pipeline.duration === '—' ? '0s' : pipeline.duration,
    };
  }
  if (allStepsDone) {
    return { ...pipeline, status: 'success', progress: 100 };
  }
  if (isStuck && progress >= 50) {
    return { ...pipeline, status: pipeline.url ? 'success' : 'failed', progress: 100 };
  }
  return pipeline;
};

const downloadPipelineLogs = (pipeline) => {
  const now = new Date();
  const lines = [];
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('  Smart DevOps — Pipeline Logs');
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push(`  Pipeline: ${pipeline.name || 'Unnamed'}`);
  lines.push(`  Repo: ${pipeline.repo || 'N/A'}`);
  lines.push(`  Status: ${(pipeline.status || 'unknown').toUpperCase()}`);
  lines.push(`  Progress: ${pipeline.progress || 0}%`);
  lines.push(`  Duration: ${pipeline.duration || 'N/A'}`);
  lines.push(`  URL: ${pipeline.url || 'N/A'}`);
  lines.push(`  Deploy Type: ${pipeline.deployType || 'auto'}`);
  lines.push(`  Exported: ${now.toLocaleString()}`);
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('');
  lines.push('─── STEPS ───');
  lines.push('');
  const steps = pipeline.steps || [];
  if (steps.length === 0) {
    lines.push('  (no steps recorded)');
  } else {
    steps.forEach((s, i) => {
      const emoji = {
        completed: '✅', success: '✅', running: '⏳',
        failed: '❌', pending: '⏸️', stopped: '⏹️',
      }[s.status] || '•';
      lines.push(`  ${emoji} [${i + 1}/${steps.length}] ${s.name || 'step'} — ${s.status || 'unknown'}`);
      if (s.duration) lines.push(`        Duration: ${s.duration}`);
      if (s.error) lines.push(`        Error: ${s.error}`);
      if (s.output) {
        lines.push('        Output:');
        String(s.output).split('\n').slice(0, 30).forEach(ln => {
          lines.push(`          ${ln}`);
        });
      }
    });
  }
  if (pipeline.logs && Array.isArray(pipeline.logs)) {
    lines.push('');
    lines.push('─── LOGS ───');
    lines.push('');
    pipeline.logs.forEach(l => {
      const ts = l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : '';
      const level = (l.level || 'info').toUpperCase().padEnd(8);
      lines.push(`  [${ts}] [${level}] ${l.message || l.log || ''}`);
    });
  }
  lines.push('');
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push(`  End of pipeline log (${steps.length} steps)`);
  lines.push('═══════════════════════════════════════════════════════════');
  const filename = `pipeline-${(pipeline.name || 'logs').replace(/[^a-z0-9]/gi, '-')}-${now.toISOString().slice(0, 19).replace(/[:.]/g, '-')}.txt`;
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  toast.success('Pipeline logs downloaded');
};

const CreatePipelineModal = ({ isOpen, onClose, onCreate }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [maxAttempts, setMaxAttempts] = useState(50);
  const [autoDeploy, setAutoDeploy] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRepoUrl('');
      setMaxAttempts(50);
      setAutoDeploy(true);
      setCreating(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreate = async () => {
    if (!repoUrl.trim()) return toast.error('Please enter a GitHub repo URL');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs are supported');
    setCreating(true);
    try {
      await onCreate({
        repoUrl: repoUrl.trim(),
        deployMethod: 'self-host',
        maxAttempts,
        autoDeploy,
      });
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
        <div className="modal-header">
          <div className="modal-header-left">
            <div className="modal-header-icon"><FiZap /></div>
            <div>
              <h2 className="modal-title">Create CI/CD Pipeline</h2>
              <p className="modal-subtitle">Generate + auto-fix + auto-deploy</p>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}><FiXCircle /></button>
        </div>

        <div className="modal-body">
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
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
            </div>
            <p className="modal-hint">
              💡 Pipeline will be generated, committed, monitored, and auto-deployed
            </p>
          </div>

          <div className="modal-field">
            <label className="modal-label">🚀 Deploy Method</label>
            <div className="method-grid">
              <button className="method-card active" onClick={() => {}}>
                <div
                  className="method-card-icon"
                  style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)' }}
                >
                  <FaRobot />
                </div>
                <div className="method-card-info">
                  <div className="method-card-title-row">
                    <span className="method-card-title">Self-Host (Agent)</span>
                    <span className="method-badge">Recommended</span>
                  </div>
                  <p className="method-card-desc">
                    Full CI/CD + auto-deploy via Cloudflare Tunnel
                  </p>
                </div>
              </button>
            </div>
          </div>

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
            <p className="modal-hint">
              🩺 HealerAgent will retry this many times to fix errors
            </p>
          </div>

          <label className="checkbox-wrapper">
            <input
              type="checkbox"
              className="checkbox-input"
              checked={autoDeploy}
              onChange={e => setAutoDeploy(e.target.checked)}
            />
            <div className="checkbox-info">
              <div className="checkbox-title">🚀 Auto-deploy after pipeline passes</div>
              <div className="checkbox-desc">
                {autoDeploy
                  ? 'Pipeline + Deploy (standard CI/CD)'
                  : 'Pipeline only (no deploy)'}
              </div>
            </div>
          </label>

          <div className="modal-summary">
            <div className="modal-summary-label">Pipeline Summary</div>
            <div className="modal-summary-value">
              Self-Host • {maxAttempts} attempts • {autoDeploy ? 'CI/CD + Deploy' : 'CI/CD only'}
            </div>
          </div>
        </div>

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

const DeleteConfirmModal = ({ pipeline, onConfirm, onCancel }) => {
  const [deleting, setDeleting] = useState(false);

  useEffect(() => { if (!pipeline) setDeleting(false); }, [pipeline]);
  if (!pipeline) return null;

  const handleConfirm = async () => {
    setDeleting(true);
    try { await onConfirm(); } finally { setDeleting(false); }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" style={{ maxWidth: 440 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <div className="modal-header-left">
            <div className="modal-header-icon" style={{
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              boxShadow: '0 8px 20px rgba(239, 68, 68, 0.35)',
            }}><FiTrash2 /></div>
            <div>
              <h2 className="modal-title">Delete Pipeline?</h2>
              <p className="modal-subtitle">This action cannot be undone</p>
            </div>
          </div>
        </div>

        <div className="modal-body" style={{ paddingTop: 12 }}>
          <div style={{
            padding: 16, background: 'rgba(239, 68, 68, 0.05)',
            border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 12,
          }}>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>
              Pipeline to delete
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', marginBottom: 4 }}>{pipeline.name}</div>
            <div style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.5)' }}>
              <FaGithub style={{ marginRight: 6, display: 'inline' }} />{pipeline.repo}
            </div>
          </div>
          <div style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, marginTop: 12 }}>
            <strong style={{ color: '#f87171' }}>⚠️ Warning:</strong> This will:
            <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 18 }}>
              <li>Stop the running deployment</li>
              <li>Remove it from your dashboard</li>
              <li>Take the live URL offline</li>
            </ul>
          </div>
        </div>

        <div className="modal-footer">
          <button className="modal-btn cancel" onClick={onCancel} disabled={deleting}>Cancel</button>
          <button className="modal-btn" style={{
            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
            color: 'white', boxShadow: '0 4px 16px rgba(239, 68, 68, 0.35)',
          }} onClick={handleConfirm} disabled={deleting}>
            {deleting ? (<><FiRefreshCw style={{ animation: 'spin 1s linear infinite' }} /> Deleting...</>)
              : (<><FiTrash2 /> Delete Pipeline</>)}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

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

  const handleDownload = (e) => {
    e.stopPropagation();
    downloadPipelineLogs(pipeline);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      className={`pipeline-card ${pipeline.status}`}>
      <div className="pipeline-card-header">
        <div className="pipeline-card-left">
          <div className={`pipeline-status-icon ${pipeline.status}`}><StatusIcon /></div>
          <div className="pipeline-info">
            <div className="pipeline-name-row">
              <h3 className="pipeline-name">{pipeline.name}</h3>
              <div className="pipeline-status-badge"><StatusIcon />{sc.label}</div>
            </div>
            <div className="pipeline-meta">
              <span className="pipeline-meta-item"><FaGithub />{pipeline.repo}</span>
              {pipeline.deployType && <span className="pipeline-meta-item"><FiLayers />{pipeline.deployType}</span>}
              {pipeline.duration && pipeline.duration !== '—' && <span className="pipeline-meta-item"><FiClock />{pipeline.duration}</span>}
            </div>
          </div>
        </div>
        {pipeline.url && !pipeline.url.includes('localhost') && (
          <a href={pipeline.url} target="_blank" rel="noopener noreferrer" className="pipeline-live-link">
            <FiExternalLink /> Live
          </a>
        )}
      </div>

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

      <div className="pipeline-progress">
        <div className="pipeline-progress-track">
          <div className={`pipeline-progress-fill ${pipeline.status}`} style={{ width: `${pipeline.progress || 0}%` }} />
        </div>
        <span className="pipeline-progress-value">{pipeline.progress || 0}%</span>
      </div>

      <div className="pipeline-actions">
        {pipeline.status === 'failed' || pipeline.status === 'pending' ? (
          <button onClick={() => onTrigger(pipeline.id)} className="action-btn trigger"><FiPlay /> Trigger</button>
        ) : pipeline.status === 'running' ? (
          <button onClick={() => onCancel(pipeline.id)} className="action-btn stop"><FiStopCircle /> Stop</button>
        ) : pipeline.status === 'success' ? (
          <button onClick={() => onRetry(pipeline.id)} className="action-btn redeploy"><FiRefreshCw /> Redeploy</button>
        ) : null}
        <button onClick={() => onViewDetails(pipeline.id)} className="action-btn logs"><FiTerminal /> Logs</button>
        <button onClick={handleDownload} className="action-btn download" title="Download logs">
          <FiDownload />
        </button>
        <button onClick={() => onDelete(pipeline.id)} className="action-btn delete" title="Delete"><FiTrash2 /></button>
      </div>
    </motion.div>
  );
};

const PipelineDashboard = () => {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const navigate = useNavigate();

  const stuckTrackerRef = useRef({});

  const fetchPipelines = useCallback(async () => {
    try {
      const data = await pipelineAPI.getAll();
      const raw = data || [];
      const processed = raw.map(p => {
        const inferred = inferPipelineStatus(p);
        if (p.status === 'running') {
          stuckTrackerRef.current[p.id] = (stuckTrackerRef.current[p.id] || 0) + 1;
        } else {
          delete stuckTrackerRef.current[p.id];
        }
        return inferred;
      });
      setPipelines(processed);
    } catch (err) {
      console.error('Fetch pipelines error:', err);
      setPipelines([]);
    } finally {
      setLoading(false);
    }
  }, []);

  usePlatformEvents('pipeline', () => fetchPipelines());

  useEffect(() => {
    fetchPipelines();
    const interval = setInterval(fetchPipelines, 5000);
    return () => clearInterval(interval);
  }, [fetchPipelines]);

  const handleCreate = async ({ repoUrl, deployMethod, maxAttempts, autoDeploy }) => {
    toast.loading('Creating pipeline...', { id: 'create' });
    const mode = autoDeploy !== false ? 'ci-cd+deploy' : 'ci-cd-only';
    const result = await pipelineAPI.create({
      repo_url: repoUrl,
      repoUrl: repoUrl,
      mode: mode,
      deploy_method: deployMethod || 'self-host',
      deployMethod: deployMethod || 'self-host',
      max_fix_attempts: maxAttempts || 50,
      maxAttempts: maxAttempts || 50,
      auto_deploy: autoDeploy !== false,
      autoDeploy: autoDeploy !== false,
      run_pipeline: true,
    });
    if (result && result.success) {
      const url = result.live_url || result.url;
      if (url) {
        toast.success(`Pipeline + Deploy successful! Live: ${url}`, { id: 'create', duration: 6000 });
      } else {
        toast.success(
          mode === 'ci-cd-only'
            ? 'Pipeline created (CI/CD only)'
            : 'Pipeline created successfully!',
          { id: 'create' }
        );
      }
      setTimeout(fetchPipelines, 2000);
    } else {
      toast.error(
        (result && result.error) || 'Failed to create pipeline',
        { id: 'create' }
      );
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

  const handleDelete = (id) => {
    const pipeline = pipelines.find(p => p.id === id);
    if (pipeline) setDeleteConfirm(pipeline);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    const id = deleteConfirm.id;
    setDeleteConfirm(null);
    toast.loading('Deleting pipeline...', { id: 'delete' });
    const result = await pipelineAPI.delete(id);
    if (result.success) {
      toast.success('Pipeline deleted!', { id: 'delete' });
      fetchPipelines();
    } else {
      toast.error(result.error || 'Failed to delete', { id: 'delete' });
    }
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
      <div className="pipeline-header">
        <div className="pipeline-header-left">
          <h1 className="pipeline-title">
            <div className="pipeline-title-icon"><FiGitBranch /></div>
            CI/CD Pipelines
          </h1>
          <p className="pipeline-subtitle">Manage, monitor, and deploy your projects</p>
        </div>
        <div className="pipeline-header-actions">
          <button className="pipeline-refresh-btn" onClick={fetchPipelines} title="Refresh">
            <FiRefreshCw className={loading ? 'spinning' : ''} />
          </button>
          <button className="pipeline-new-btn" onClick={() => setShowCreateModal(true)}>
            <FiPlus /> New Pipeline
          </button>
        </div>
      </div>

      <div className="pipeline-stats">
        <div className="stat-card" style={{ '--stat-color': '#a855f7' }} onClick={() => setFilter('all')}>
          <div className="stat-card-header"><span className="stat-label">Total</span><div className="stat-icon"><FiGitBranch /></div></div>
          <div className="stat-value">{counts.all}</div><div className="stat-sub">All pipelines</div>
        </div>
        <div className="stat-card" style={{ '--stat-color': '#10b981' }} onClick={() => setFilter('success')}>
          <div className="stat-card-header"><span className="stat-label">Live</span><div className="stat-icon"><FiCheckCircle /></div></div>
          <div className="stat-value">{counts.success}</div><div className="stat-sub">Deployed & running</div>
        </div>
        <div className="stat-card" style={{ '--stat-color': '#ef4444' }} onClick={() => setFilter('failed')}>
          <div className="stat-card-header"><span className="stat-label">Failed</span><div className="stat-icon"><FiXCircle /></div></div>
          <div className="stat-value">{counts.failed}</div><div className="stat-sub">Need attention</div>
        </div>
        <div className="stat-card" style={{ '--stat-color': '#3b82f6' }} onClick={() => setFilter('running')}>
          <div className="stat-card-header"><span className="stat-label">Running</span><div className="stat-icon"><FiActivity /></div></div>
          <div className="stat-value">{counts.running}</div><div className="stat-sub">In progress</div>
        </div>
      </div>

      <div className="pipeline-filters">
        <div className="filter-pills">
          {['all', 'running', 'success', 'failed', 'pending'].map(status => (
            <button key={status} className={`filter-pill ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {counts[status] > 0 && <span className="filter-count">{counts[status]}</span>}
            </button>
          ))}
        </div>
        <div className="search-wrapper">
          <FiSearch className="search-icon" />
          <input type="text" className="search-input" value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)} placeholder="Search pipelines..." />
        </div>
      </div>

      {loading ? (
        <div className="pipeline-list">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="pipeline-skeleton">
              <div className="skeleton-row short" /><div className="skeleton-row medium" /><div className="skeleton-row full" />
            </div>
          ))}
        </div>
      ) : filteredPipelines.length === 0 ? (
        <div className="pipeline-empty">
          <div className="pipeline-empty-icon"><FiGitBranch /></div>
          <h3 className="pipeline-empty-title">
            {searchTerm || filter !== 'all' ? 'No pipelines match your filters' : 'No pipelines yet'}
          </h3>
          <p className="pipeline-empty-text">
            {searchTerm || filter !== 'all' ? 'Try adjusting your search or filter settings'
              : 'Create your first CI/CD pipeline to get started with automated deployments'}
          </p>
          {!searchTerm && filter === 'all' && (
            <button className="pipeline-empty-btn" onClick={() => setShowCreateModal(true)}>
              <FiPlus /> Create First Pipeline
            </button>
          )}
        </div>
      ) : (
        <div className="pipeline-list">
          <AnimatePresence>
            {filteredPipelines.map(p => (
              <PipelineCard key={p.id} pipeline={p}
                onTrigger={handleTrigger} onRetry={handleRetry} onCancel={handleCancel}
                onViewDetails={(id) => navigate(`/pipelines/${id}`)} onDelete={handleDelete} />
            ))}
          </AnimatePresence>
        </div>
      )}

      <div className="pipeline-footer">
        <span><span className="pipeline-footer-dot"></span>{filteredPipelines.length} of {pipelines.length} pipelines</span>
        <span>Auto-refresh: 5s</span>
      </div>

      <CreatePipelineModal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} onCreate={handleCreate} />
      <DeleteConfirmModal pipeline={deleteConfirm} onConfirm={confirmDelete} onCancel={() => setDeleteConfirm(null)} />
    </div>
  );
};

export default PipelineDashboard;