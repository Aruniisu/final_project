import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import io from 'socket.io-client';
import {
  FiArrowLeft, FiCheckCircle, FiXCircle, FiClock, FiRefreshCw,
  FiPlay, FiStopCircle, FiDownload, FiCopy, FiAlertCircle,
  FiActivity, FiGitBranch, FiUser, FiCalendar, FiCode,
  FiExternalLink, FiTerminal,
} from 'react-icons/fi';
import { FaGithub, FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';
import { pipelineAPI, WS_URL } from '../../api/assistant';
import './PipelineDashboard.css';

// ============================================
// Log Viewer
// ============================================
const LogViewer = ({ logs, isLive }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (isLive) logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs, isLive]);

  return (
    <div style={{
      background: 'rgba(0, 0, 0, 0.4)',
      borderRadius: '12px',
      padding: '16px',
      fontFamily: 'JetBrains Mono, Monaco, monospace',
      fontSize: '12px',
      overflowX: 'auto',
      maxHeight: '500px',
      overflowY: 'auto',
    }}>
      {logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255, 255, 255, 0.3)' }}>
          <FiTerminal style={{ width: 24, height: 24, marginBottom: 8 }} />
          <p>Waiting for logs...</p>
        </div>
      ) : (
        logs.map((log, i) => (
          <div key={i} style={{
            display: 'flex',
            gap: '12px',
            padding: '2px 0',
            borderLeft: `2px solid ${
              log.level === 'error' ? '#f87171' :
              log.level === 'warning' ? '#fbbf24' :
              log.level === 'success' ? '#34d399' : '#475569'
            }`,
            paddingLeft: '10px',
            marginBottom: '2px',
          }}>
            <span style={{ color: 'rgba(255, 255, 255, 0.3)', flexShrink: 0 }}>
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>
            <span style={{
              color: log.level === 'error' ? '#f87171' :
                     log.level === 'warning' ? '#fbbf24' :
                     log.level === 'success' ? '#34d399' :
                     'rgba(255, 255, 255, 0.8)',
            }}>
              {log.message}
            </span>
          </div>
        ))
      )}
      {isLive && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#a855f7', marginTop: 8 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#a855f7',
            animation: 'pulse 2s infinite',
          }} />
          Streaming logs...
        </div>
      )}
      <div ref={logEndRef} />
    </div>
  );
};

// ============================================
// Main Details Component
// ============================================
const PipelineDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pipeline, setPipeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [isLive, setIsLive] = useState(true);
  const [selectedTab, setSelectedTab] = useState('overview');
  const socketRef = useRef(null);

  // Fetch pipeline details
  useEffect(() => {
    fetchPipelineDetails();
  }, [id]);

  // Setup Socket.IO for real-time logs
  useEffect(() => {
    const socket = io(WS_URL, {
      transports: ['polling', 'websocket'],
      reconnection: true,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('✅ Socket connected for logs');
    });

    socket.on('live_log', (data) => {
      const level = data.level || data.type || 'info';
      const message = data.message || data.log || '';
      if (message) {
        setLogs(prev => [...prev.slice(-500), {
          timestamp: data.timestamp || new Date().toISOString(),
          level,
          message,
        }]);
      }
    });

    socket.on('agent_log', (data) => {
      const level = data.level || 'info';
      const message = data.message || '';
      if (message) {
        setLogs(prev => [...prev.slice(-500), {
          timestamp: data.timestamp || new Date().toISOString(),
          level,
          message,
        }]);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const fetchPipelineDetails = async () => {
    try {
      setLoading(true);
      const data = await pipelineAPI.getDetails(id);
      setPipeline(data);
    } catch (error) {
      console.error('Error fetching pipeline:', error);
      toast.error('Failed to load pipeline');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await pipelineAPI.getLogs(id);
      setLogs(data || []);
      toast.success('Logs refreshed');
    } catch (error) {
      toast.error('Failed to fetch logs');
    }
  };

  const handleTrigger = async () => {
    try {
      toast.loading('Triggering...', { id: 'action' });
      await pipelineAPI.trigger(id);
      toast.success('Pipeline triggered', { id: 'action' });
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to trigger', { id: 'action' });
    }
  };

  const handleRetry = async () => {
    try {
      toast.loading('Retrying...', { id: 'action' });
      await pipelineAPI.retry(id);
      toast.success('Retry started', { id: 'action' });
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to retry', { id: 'action' });
    }
  };

  const handleCancel = async () => {
    try {
      toast.loading('Stopping...', { id: 'action' });
      await pipelineAPI.cancel(id);
      toast.success('Pipeline stopped', { id: 'action' });
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to cancel', { id: 'action' });
    }
  };

  const handleCopyLogs = () => {
    const text = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    toast.success('Logs copied!');
  };

  const handleDownloadLogs = () => {
    const text = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline-${id}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Logs downloaded');
  };

  if (loading) {
    return (
      <div className="pipeline-dashboard">
        <div className="pipeline-skeleton">
          <div className="skeleton-row short" />
          <div className="skeleton-row medium" />
          <div className="skeleton-row full" />
        </div>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="pipeline-dashboard">
        <div className="pipeline-empty">
          <div className="pipeline-empty-icon">
            <FiAlertCircle />
          </div>
          <h3 className="pipeline-empty-title">Pipeline not found</h3>
          <p className="pipeline-empty-text">The pipeline you're looking for doesn't exist</p>
          <button className="pipeline-empty-btn" onClick={() => navigate('/pipelines')}>
            <FiArrowLeft />
            Back to Pipelines
          </button>
        </div>
      </div>
    );
  }

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
    <div className="pipeline-dashboard">
      {/* Header */}
      <div className="pipeline-header">
        <div className="pipeline-header-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button
              onClick={() => navigate('/pipelines')}
              style={{
                width: 40, height: 40, borderRadius: 12,
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: 'rgba(255, 255, 255, 0.7)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <FiArrowLeft />
            </button>
            <h1 className="pipeline-title">
              <div className={`pipeline-status-icon ${pipeline.status}`}>
                <StatusIcon />
              </div>
              {pipeline.name}
            </h1>
          </div>
          <p className="pipeline-subtitle" style={{ marginLeft: 56 }}>
            {pipeline.repo} • {pipeline.deployType}
          </p>
        </div>
        <div className="pipeline-header-actions">
          <button className="pipeline-refresh-btn" onClick={fetchPipelineDetails} title="Refresh">
            <FiRefreshCw />
          </button>
          {pipeline.url && (
            <a
              href={pipeline.url}
              target="_blank"
              rel="noopener noreferrer"
              className="pipeline-live-link"
            >
              <FiExternalLink />
              Open Live
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: 4,
        padding: 4,
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: 14,
        width: 'fit-content',
      }}>
        {['overview', 'logs', 'steps'].map(tab => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`filter-pill ${selectedTab === tab ? 'active' : ''}`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {selectedTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="pipeline-stats"
            style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}
          >
            <div className="stat-card" style={{ '--stat-color': '#a855f7' }}>
              <div className="stat-card-header">
                <span className="stat-label">Progress</span>
              </div>
              <div className="stat-value">{pipeline.progress || 0}%</div>
              <div className="pipeline-progress-track" style={{ marginTop: 12 }}>
                <div
                  className={`pipeline-progress-fill ${pipeline.status}`}
                  style={{ width: `${pipeline.progress || 0}%` }}
                />
              </div>
            </div>

            <div className="stat-card" style={{ '--stat-color': '#10b981' }}>
              <div className="stat-card-header">
                <span className="stat-label">Status</span>
                <div className="stat-icon"><StatusIcon /></div>
              </div>
              <div className="stat-value" style={{ fontSize: 20 }}>{sc.label}</div>
              <div className="stat-sub">Current state</div>
            </div>

            <div className="stat-card" style={{ '--stat-color': '#3b82f6' }}>
              <div className="stat-card-header">
                <span className="stat-label">Duration</span>
                <div className="stat-icon"><FiClock /></div>
              </div>
              <div className="stat-value" style={{ fontSize: 20 }}>{pipeline.duration || '—'}</div>
              <div className="stat-sub">Total runtime</div>
            </div>

            <div className="stat-card" style={{ '--stat-color': '#f59e0b' }}>
              <div className="stat-card-header">
                <span className="stat-label">Type</span>
                <div className="stat-icon"><FiGitBranch /></div>
              </div>
              <div className="stat-value" style={{ fontSize: 20 }}>{pipeline.deployType || 'auto'}</div>
              <div className="stat-sub">Deploy method</div>
            </div>
          </motion.div>
        )}

        {selectedTab === 'logs' && (
          <motion.div
            key="logs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <button
                  onClick={() => setIsLive(!isLive)}
                  className={`filter-pill ${isLive ? 'active' : ''}`}
                >
                  {isLive ? '🔴 Live' : '⏸ Paused'}
                </button>
                <span style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.5)' }}>
                  {logs.length} logs
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="action-btn logs" onClick={fetchLogs}>
                  <FiRefreshCw /> Refresh
                </button>
                <button className="action-btn logs" onClick={handleCopyLogs}>
                  <FiCopy /> Copy
                </button>
                <button className="action-btn logs" onClick={handleDownloadLogs}>
                  <FiDownload /> Download
                </button>
              </div>
            </div>
            <LogViewer logs={logs} isLive={isLive} />
          </motion.div>
        )}

        {selectedTab === 'steps' && (
          <motion.div
            key="steps"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="pipeline-list"
          >
            {(pipeline.steps || []).map((step, i) => (
              <div key={i} className="pipeline-card">
                <div className="pipeline-card-header">
                  <div className="pipeline-card-left">
                    <div className={`pipeline-status-icon ${step.status}`}>
                      {step.status === 'completed' ? <FiCheckCircle /> :
                       step.status === 'running' ? <FiActivity /> :
                       step.status === 'failed' ? <FiXCircle /> : <FiClock />}
                    </div>
                    <div className="pipeline-info">
                      <h3 className="pipeline-name">{step.name}</h3>
                      <div className="pipeline-meta">
                        <span className="pipeline-meta-item">
                          <FiClock />
                          {step.duration || '—'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      <div className="pipeline-actions" style={{ marginTop: 16 }}>
        {pipeline.status === 'failed' || pipeline.status === 'pending' ? (
          <button className="action-btn trigger" onClick={handleTrigger}>
            <FiPlay /> Trigger
          </button>
        ) : pipeline.status === 'running' ? (
          <button className="action-btn stop" onClick={handleCancel}>
            <FiStopCircle /> Stop
          </button>
        ) : pipeline.status === 'success' ? (
          <button className="action-btn redeploy" onClick={handleRetry}>
            <FiRefreshCw /> Redeploy
          </button>
        ) : null}
      </div>
    </div>
  );
};

export default PipelineDetails;