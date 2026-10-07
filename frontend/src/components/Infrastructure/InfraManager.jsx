import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import '../../styles/main.css';
import '../Dashboard/Dashboard.css';
import './InfraManager.css';
import { APP_VERSION } from '../../config/version';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import {
  FiCpu, FiServer, FiActivity, FiTrendingUp, FiAlertCircle,
  FiCheckCircle, FiRefreshCw, FiDollarSign, FiSend, FiXCircle,
  FiPower, FiTool,
} from 'react-icons/fi';
import { FaBrain, FaHandPaper } from 'react-icons/fa';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import { infraAPI } from '../../api/assistant';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, Title, Tooltip, Legend, Filler
);

const safe = async (fn, fallback = null) => {
  try {
    if (typeof fn !== 'function') return fallback;
    return (await fn()) ?? fallback;
  } catch { return fallback; }
};

// ============================================
// STATS CARD
// ============================================
const StatsCard = ({ title, value, icon: Icon, color, subtitle, loading }) => {
  if (loading) {
    return (
      <div className="dashboard-stats-card dashboard-stats-card-loading">
        <div className="dashboard-stats-card-loading-inner">
          <div className="dashboard-stats-card-loading-title"></div>
          <div className="dashboard-stats-card-loading-value"></div>
        </div>
        <div className="dashboard-stats-card-loading-icon"></div>
      </div>
    );
  }
  return (
    <div className="dashboard-stats-card">
      <div className="dashboard-stats-card-content">
        <p className="dashboard-stats-card-title">{title}</p>
        <h3 className="dashboard-stats-card-value">{value}</h3>
        {subtitle && <p className="dashboard-stats-card-subtitle">{subtitle}</p>}
      </div>
      <div className={`dashboard-stats-card-icon-wrapper ${color}`}>
        <Icon className="dashboard-stats-card-icon" />
      </div>
    </div>
  );
};

// ============================================
// AGENT CONTROL BAR
// ============================================
const AgentControlBar = ({ agent, onModeChange, onConfidenceChange }) => {
  const modes = [
    { id: 'off', label: 'Off', icon: FiPower, color: '#64748b' },
    { id: 'assistive', label: 'Assistive', icon: FaHandPaper, color: '#f59e0b' },
    { id: 'autonomous', label: 'Autonomous', icon: FaBrain, color: '#10b981' },
  ];

  return (
    <div className="infra-agent-bar">
      <div className="infra-agent-status">
        <div className="infra-agent-avatar">
          <FaBrain />
          <span className="infra-agent-pulse" style={{
            background: agent.mode === 'autonomous' ? '#10b981' :
                        agent.mode === 'assistive' ? '#f59e0b' : '#64748b',
          }}></span>
        </div>
        <div className="infra-agent-info">
          <div className="infra-agent-title">
            Infra AI Agent
            <span className="infra-agent-badge">{agent.tools_count || 6} tools</span>
          </div>
          <div className="infra-agent-subtitle">
            {agent.mode === 'autonomous' && `● Autonomous · ${agent.total_actions || 0} actions executed`}
            {agent.mode === 'assistive' && `● Assistive · ${agent.pending_count || 0} pending approvals`}
            {agent.mode === 'off' && '● Agent is paused'}
          </div>
        </div>
      </div>

      <div className="infra-agent-controls">
        <div className="infra-mode-switch">
          {modes.map(m => (
            <button
              key={m.id}
              className={`infra-mode-btn ${agent.mode === m.id ? 'active' : ''}`}
              onClick={() => onModeChange(m.id)}
              style={{ '--mode-color': m.color }}
            >
              <m.icon />
              <span>{m.label}</span>
            </button>
          ))}
        </div>

        <div className="infra-confidence-slider">
          <label>Confidence ≥ <b>{(agent.confidence_threshold * 100).toFixed(0)}%</b></label>
          <input
            type="range" min="0.5" max="0.95" step="0.05"
            value={agent.confidence_threshold || 0.75}
            onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
          />
        </div>
      </div>
    </div>
  );
};

// ============================================
// DECISION CARD
// ============================================
const DecisionCard = ({ decision, onApprove, onReject }) => {
  const severityColor = {
    critical: '#ef4444', warning: '#f59e0b', info: '#3b82f6',
  }[decision.severity] || '#64748b';

  const statusLabel = {
    pending: 'Awaiting approval',
    suggested: 'Suggestion',
    executed: 'Executed',
    rejected: 'Rejected',
    failed: 'Failed',
  }[decision.status] || decision.status;

  const confidencePct = Math.round((decision.confidence || 0) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`infra-decision ${decision.severity} ${decision.status}`}
    >
      <div className="infra-decision-header">
        <div className="infra-decision-tool">
          <FiTool style={{ color: severityColor }} />
          <span>{decision.tool.replace(/_/g, ' ')}</span>
          <span className="infra-decision-confidence" style={{
            background: confidencePct >= 80 ? 'rgba(16,185,129,0.15)' :
                        confidencePct >= 60 ? 'rgba(245,158,11,0.15)' : 'rgba(100,116,139,0.15)',
            color: confidencePct >= 80 ? '#10b981' :
                   confidencePct >= 60 ? '#f59e0b' : '#94a3b8',
          }}>{confidencePct}%</span>
        </div>
        <span className={`infra-decision-status ${decision.status}`}>{statusLabel}</span>
      </div>

      <p className="infra-decision-reason">{decision.reason}</p>

      {decision.args && Object.keys(decision.args).length > 0 && (
        <div className="infra-decision-args">
          {Object.entries(decision.args).map(([k, v]) => (
            <span key={k} className="infra-arg-chip">
              <b>{k}</b>={String(v).substring(0, 40)}
            </span>
          ))}
        </div>
      )}

      {decision.status === 'pending' && (
        <div className="infra-decision-actions">
          <button className="infra-btn-approve" onClick={() => onApprove(decision)}>
            <FiCheckCircle /> Approve & Execute
          </button>
          <button className="infra-btn-reject" onClick={() => onReject(decision)}>
            <FiXCircle /> Dismiss
          </button>
        </div>
      )}

      {decision.status === 'executed' && decision.result && (
        <div className="infra-decision-result">
          <FiCheckCircle style={{ color: '#10b981' }} />
          <span>{decision.result.message || 'Executed'}</span>
        </div>
      )}

      {decision.status === 'failed' && decision.result && (
        <div className="infra-decision-result error">
          <FiAlertCircle style={{ color: '#ef4444' }} />
          <span>{decision.result.error || 'Failed'}</span>
        </div>
      )}
    </motion.div>
  );
};

// ============================================
// AGENT LOG
// ============================================
const AgentLog = ({ decisions }) => {
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [decisions]);

  return (
    <div className="infra-agent-log">
      {decisions.length === 0 ? (
        <div className="infra-empty-state">
          <FaBrain size={22} style={{ opacity: 0.4 }} />
          <p>Agent is thinking...</p>
          <p style={{ fontSize: 11, opacity: 0.5 }}>Decisions will appear here</p>
        </div>
      ) : (
        decisions.map((d, i) => (
          <div key={`${d.id || 'dec'}-${i}`} className={`infra-log-item ${d.severity} ${d.status}`}>
            <span className="infra-log-dot" style={{
              background: d.severity === 'critical' ? '#ef4444' :
                          d.severity === 'warning' ? '#f59e0b' : '#3b82f6',
            }}></span>
            <div className="infra-log-content">
              <div className="infra-log-tool">{d.tool.replace(/_/g, ' ')}</div>
              <div className="infra-log-reason">{d.reason}</div>
            </div>
            <div className="infra-log-meta">
              <span className="infra-log-confidence">
                {Math.round((d.confidence || 0) * 100)}%
              </span>
              <span className="infra-log-time">
                {new Date((d.timestamp || 0) * 1000).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================
const InfraManager = () => {
  const { user } = useAuth();

  // Dev-only log (no noise)
  if (process.env.NODE_ENV === 'development') {
    console.log('🤖 INFRA AGENTIC UI LOADED');
  }

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');

  const [services, setServices] = useState([]);
  const [health, setHealth] = useState({ score: 100, status: 'excellent' });
  const [highPerf, setHighPerf] = useState({});
  const [predictions, setPredictions] = useState([]);
  const [costSavings, setCostSavings] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [tools, setTools] = useState([]);

  const [agent, setAgent] = useState({
    mode: 'assistive', running: true, total_decisions: 0,
    total_actions: 0, success_rate: 1.0, confidence_threshold: 0.75,
    pending_count: 0, tools_count: 6,
  });

  const [chatMessages, setChatMessages] = useState([{
    role: 'assistant',
    content: "👋 Hi! I'm your **Infra AI Agent**. Try:\n- `launch https://github.com/user/repo`\n- `restart <app>`\n- `status`\n- `autonomous`",
    timestamp: new Date().toLocaleTimeString(),
  }]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [unified, agentState, decisionsData, preds, costs, toolsData] = await Promise.all([
        safe(() => infraAPI.getUnified(), null),
        safe(() => infraAPI.getAgentState(), null),
        safe(() => infraAPI.getDecisions(30), []),
        safe(() => infraAPI.getPredictions(), []),
        safe(() => infraAPI.getCostSavings(), []),
        safe(() => infraAPI.getTools(), []),
      ]);

      if (unified) {
        setServices(unified.services || []);
        setHealth(unified.health || {});
        setHighPerf(unified.high_performance || {});
      }
      if (agentState) setAgent(prev => ({ ...prev, ...agentState }));
      setDecisions(Array.isArray(decisionsData) ? decisionsData : []);
      setPredictions(Array.isArray(preds) ? preds : []);
      setCostSavings(Array.isArray(costs) ? costs : []);
      setTools(Array.isArray(toolsData) ? toolsData : []);
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // ⭐ Cross-page real-time events
  usePlatformEvents('infrastructure', (evt) => {
    console.log('📡 Infra received:', evt.type);
    fetchAll(true);
  });

  useEffect(() => {
    fetchAll();
    const i = setInterval(() => fetchAll(true), 8000);
    return () => clearInterval(i);
  }, [fetchAll]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAll(true);
    toast.success('Refreshed');
    setTimeout(() => setRefreshing(false), 400);
  };

  const handleModeChange = async (mode) => {
    setAgent(prev => ({ ...prev, mode }));
    const res = await safe(() => infraAPI.setAgentMode(mode), null);
    if (res?.success) {
      const labels = { off: '⏸️ Paused', assistive: '🤝 Assistive', autonomous: '🧠 Autonomous' };
      toast.success(labels[mode]);
    }
  };

  const handleConfidenceChange = async (threshold) => {
    setAgent(prev => ({ ...prev, confidence_threshold: threshold }));
    await safe(() => infraAPI.setConfidenceThreshold(threshold), null);
  };

  const handleApprove = async (decision) => {
    toast.loading('Executing...', { id: 'exec' });
    const res = await safe(() => infraAPI.executeDecision(decision.id), null);
    if (res?.success) {
      toast.success('✅ Executed', { id: 'exec' });
      fetchAll(true);
    } else {
      toast.error('Failed', { id: 'exec' });
    }
  };

  const handleReject = async (decision) => {
    setDecisions(prev => prev.map(d => d.id === decision.id ? { ...d, status: 'rejected' } : d));
    await safe(() => infraAPI.dismissInsight(decision.id), null);
    toast.success('Dismissed');
  };

  const handleChatSend = async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatMessages(prev => [...prev, { role: 'user', content: msg, timestamp: new Date().toLocaleTimeString() }]);
    setChatInput('');
    setChatLoading(true);
    const res = await safe(() => infraAPI.chat(msg), null);
    setChatMessages(prev => [...prev, {
      role: 'assistant',
      content: res?.message || '⚠️ AI offline',
      timestamp: new Date().toLocaleTimeString(),
    }]);
    setChatLoading(false);
    if (res?.decision) fetchAll(true);
  };

  const handleChatKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChatSend(); }
  };

  const pending = decisions.filter(d => d.status === 'pending');
  const displayed = activeTab === 'pending' ? pending
                  : activeTab === 'log' ? decisions : [];

  // Charts
  const trendData = {
    labels: Array.from({ length: 20 }, (_, i) => `${20 - i}m`),
    datasets: [
      { label: 'CPU', data: Array.from({ length: 20 }, (_, i) =>
          Math.max(5, Math.min(98, (highPerf.cpu_percent || 30) + Math.sin(i / 3) * 10))),
        borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)',
        fill: true, tension: 0.4, pointRadius: 0 },
      { label: 'Memory', data: Array.from({ length: 20 }, (_, i) =>
          Math.max(5, Math.min(98, (highPerf.memory_percent || 50) + Math.cos(i / 4) * 8))),
        borderColor: '#d946ef', backgroundColor: 'rgba(217,70,239,0.05)',
        fill: true, tension: 0.4, pointRadius: 0 },
    ],
  };

  const trendOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'line', padding: 16, font: { size: 11 }, color: '#94a3b8' } },
      tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', titleColor: '#fff', bodyColor: '#94a3b8', borderRadius: 8, padding: 12 },
    },
    scales: {
      y: { beginAtZero: true, max: 100, grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v + '%' } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 6 } },
    },
    interaction: { intersect: false, mode: 'index' },
  };

  const running = services.filter(s => s.status === 'running').length;
  const crashed = services.filter(s => s.status === 'crashed' || s.status === 'failed').length;

  const containerData = {
    labels: ['Running', 'Crashed'],
    datasets: [{ data: [running, crashed], backgroundColor: ['#10b981', '#ef4444'], borderWidth: 0, hoverOffset: 6 }],
  };

  const containerOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 11 }, color: '#94a3b8' } },
      tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', titleColor: '#fff', bodyColor: '#94a3b8', borderRadius: 8, padding: 12 },
    },
    cutout: '70%',
  };

  const statsCards = [
    { title: 'Services', value: services.length, icon: FiServer, color: 'color-primary', subtitle: `${running} running · ${crashed} crashed` },
    { title: 'Avg CPU', value: `${(highPerf.cpu_percent || 0).toFixed(0)}%`, icon: FiCpu, color: 'color-accent', subtitle: health.status },
    { title: 'Agent Actions', value: agent.total_actions || 0, icon: FaBrain, color: 'color-success', subtitle: `${Math.round((agent.success_rate || 0) * 100)}% success` },
    { title: 'Pending', value: agent.pending_count || 0, icon: FiAlertCircle, color: 'color-error', subtitle: agent.mode },
  ];

  return (
    <div className="dashboard-container">

      {/* HEADER */}
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">Infrastructure · Agentic AI 🧠</h2>
          <p className="dashboard-subtitle">
            Welcome back, {user?.name || 'User'}! Autonomous infrastructure
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button onClick={handleRefresh} disabled={refreshing} className="dashboard-refresh-btn">
            <FiRefreshCw className={`dashboard-refresh-icon ${refreshing ? 'dashboard-refresh-icon-spinning' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          <div className="dashboard-status-badge">
            <span className="dashboard-status-dot" style={{
              background: agent.mode === 'autonomous' ? '#10b981' :
                          agent.mode === 'assistive' ? '#f59e0b' : '#64748b',
            }}></span>
            <span>{agent.mode.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* AGENT CONTROL BAR */}
      <AgentControlBar agent={agent} onModeChange={handleModeChange} onConfidenceChange={handleConfidenceChange} />

      {/* STATS */}
      <div className="dashboard-stats-grid">
        {statsCards.map((s, i) => <StatsCard key={i} {...s} loading={loading} />)}
      </div>

      {/* CHARTS */}
      <div className="dashboard-charts-grid">
        <div className="dashboard-chart-card dashboard-chart-card-large">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Resource Trends</h3>
              <p className="dashboard-chart-subtitle">Live · last 20 minutes</p>
            </div>
          </div>
          <div className="dashboard-chart-wrapper">
            <Line data={trendData} options={trendOptions} />
          </div>
        </div>

        <div className="dashboard-chart-card">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Service Status</h3>
              <p className="dashboard-chart-subtitle">Real-time</p>
            </div>
          </div>
          <div className="dashboard-chart-wrapper dashboard-chart-doughnut-wrapper" style={{ position: 'relative' }}>
            <Doughnut data={containerData} options={containerOptions} />
            <div style={{
              position: 'absolute', top: '45%', left: '50%',
              transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none',
            }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#fff' }}>{services.length}</div>
              <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase' }}>Total</div>
            </div>
          </div>
        </div>
      </div>

      {/* AGENT DECISIONS PANEL */}
      <div className="dashboard-card infra-agent-panel">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title">
            <FaBrain style={{ color: '#a855f7', marginRight: 8, display: 'inline' }} />
            AI Agent Decisions
            {agent.mode === 'autonomous' && <span className="infra-live-badge">● AUTONOMOUS</span>}
          </h3>
          <div className="infra-agent-tabs">
            <button className={activeTab === 'pending' ? 'active' : ''} onClick={() => setActiveTab('pending')}>
              Pending {pending.length > 0 && <span className="infra-tab-badge">{pending.length}</span>}
            </button>
            <button className={activeTab === 'log' ? 'active' : ''} onClick={() => setActiveTab('log')}>
              Decision Log
            </button>
            <button className={activeTab === 'tools' ? 'active' : ''} onClick={() => setActiveTab('tools')}>
              Tools ({tools.length})
            </button>
          </div>
        </div>

        {activeTab === 'tools' ? (
          <div className="infra-tools-grid">
            {tools.map((t, i) => (
              <div key={`${t.name}-${i}`} className="infra-tool-card">
                <div className={`infra-tool-risk ${t.risk}`}>{t.risk}</div>
                <div className="infra-tool-name"><FiTool /> {t.name.replace(/_/g, ' ')}</div>
                <div className="infra-tool-desc">{t.description}</div>
                <div className="infra-tool-args">
                  {t.args?.map(a => <span key={a}>{a}</span>)}
                  {(!t.args || t.args.length === 0) && <span className="empty">no args</span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="infra-decisions-list">
            {displayed.length === 0 ? (
              <div className="infra-empty-state">
                {activeTab === 'pending' ? (
                  <>
                    <FiCheckCircle size={22} style={{ color: '#10b981' }} />
                    <p>No pending decisions</p>
                    <p style={{ fontSize: 11, opacity: 0.5 }}>Agent is monitoring continuously</p>
                  </>
                ) : (
                  <>
                    <FaBrain size={22} style={{ opacity: 0.4 }} />
                    <p>No decisions logged yet</p>
                  </>
                )}
              </div>
            ) : (
              displayed.map((d, i) => (
                <DecisionCard key={`${d.id || 'dec'}-${i}`} decision={d} onApprove={handleApprove} onReject={handleReject} />
              ))
            )}
          </div>
        )}
      </div>

      {/* LIVE FEED + PREDICTIONS */}
      <div className="dashboard-two-column-grid">
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">
              <FiActivity style={{ color: '#3b82f6', marginRight: 8, display: 'inline' }} />
              Agent Live Feed
            </h3>
            <span className="dashboard-card-view-all" style={{ color: '#10b981' }}>● Live</span>
          </div>
          <AgentLog decisions={decisions.slice(-10).reverse()} />
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">
              <FiTrendingUp style={{ color: '#f59e0b', marginRight: 8, display: 'inline' }} />
              Predictions
            </h3>
          </div>
          <div className="dashboard-activity-list">
            {predictions.length === 0 ? (
              <div className="dashboard-activity-item status-success">
                <div className="dashboard-activity-icon"><FiCheckCircle className="dashboard-status-icon" /></div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">No issues predicted</p>
                  <div className="dashboard-activity-meta"><span>All clear</span></div>
                </div>
              </div>
            ) : (
              predictions.slice(0, 3).map((p, i) => (
                <div key={`${p.id || 'pred'}-${i}`} className={`dashboard-activity-item ${p.severity === 'critical' ? 'status-error' : 'status-warning'}`}>
                  <div className="dashboard-activity-icon"><FiAlertCircle className="dashboard-status-icon" /></div>
                  <div className="dashboard-activity-content">
                    <p className="dashboard-activity-title">{p.service}</p>
                    <div className="dashboard-activity-meta">
                      <span>{p.prediction}</span>
                      <span className="dashboard-activity-dot"></span>
                      <span>{p.timeframe}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* COST + METRICS */}
      <div className="dashboard-two-column-grid">
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">
              <FiDollarSign style={{ color: '#10b981', marginRight: 8, display: 'inline' }} />
              Cost Optimizer
            </h3>
          </div>
          <div className="dashboard-activity-list">
            {costSavings.length === 0 ? (
              <div className="dashboard-activity-item status-success">
                <div className="dashboard-activity-icon"><FiCheckCircle className="dashboard-status-icon" /></div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">No waste detected</p>
                  <div className="dashboard-activity-meta"><span>All resources efficient</span></div>
                </div>
              </div>
            ) : (
              costSavings.slice(0, 4).map((c, i) => (
                <div key={`${c.id || 'cost'}-${i}`} className="dashboard-activity-item status-success">
                  <div className="dashboard-activity-icon"><FiDollarSign className="dashboard-status-icon" /></div>
                  <div className="dashboard-activity-content">
                    <p className="dashboard-activity-title">{c.service}</p>
                    <div className="dashboard-activity-meta"><span>{c.suggestion}</span></div>
                  </div>
                  <span className="dashboard-activity-status">{c.estimated_savings}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="dashboard-card">
          <h3 className="dashboard-card-title">System Metrics</h3>
          <div className="dashboard-system-stats-grid">
            {[
              { label: 'CPU', value: highPerf.cpu_percent, fill: 'primary' },
              { label: 'Memory', value: highPerf.memory_percent, fill: 'warning' },
              { label: 'Disk', value: highPerf.disk_percent, fill: 'info' },
            ].map((m, i) => (
              <div key={i} className="dashboard-system-stat">
                <p className="dashboard-system-stat-label">{m.label}</p>
                <p className="dashboard-system-stat-value">{(m.value || 0).toFixed(0)}%</p>
                <div className="dashboard-system-stat-bar">
                  <div className={`dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-${m.fill}`}
                       style={{ width: `${Math.min(100, m.value || 0)}%` }}></div>
                </div>
              </div>
            ))}
            <div className="dashboard-system-stat">
              <p className="dashboard-system-stat-label">Network</p>
              <p className="dashboard-system-stat-value">{(highPerf.network_in_mbps || 0).toFixed(1)} MB/s</p>
              <div className="dashboard-system-stat-bar">
                <div className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-success"
                     style={{ width: `${Math.min(100, (highPerf.network_in_mbps || 0) * 5)}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SERVICES */}
      <div className="dashboard-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title">Services ({services.length})</h3>
          <span className="dashboard-card-view-all">Auto-refresh 8s</span>
        </div>
        <div className="dashboard-activity-list">
          {services.length === 0 ? (
            <div className="dashboard-activity-item status-info">
              <div className="dashboard-activity-icon"><FiServer className="dashboard-status-icon" /></div>
              <div className="dashboard-activity-content">
                <p className="dashboard-activity-title">No services running</p>
                <div className="dashboard-activity-meta"><span>Try: "launch https://github.com/user/repo" in chat</span></div>
              </div>
            </div>
          ) : (
            services.slice(0, 8).map((svc, i) => (
              <div key={`${svc.service_name}-${svc.port || i}-${i}`} className={`dashboard-activity-item ${svc.status === 'running' ? 'status-success' : 'status-error'}`}>
                <div className="dashboard-activity-icon"><FiServer className="dashboard-status-icon" /></div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">{svc.display_name || svc.service_name}</p>
                  <div className="dashboard-activity-meta">
                    <span>Port {svc.port}</span>
                    <span className="dashboard-activity-dot"></span>
                    <span>CPU {svc.cpu_percent || 0}%</span>
                    <span className="dashboard-activity-dot"></span>
                    <span>PID {svc.pid || '—'}</span>
                  </div>
                </div>
                <span className="dashboard-activity-status">{svc.status}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* VERSION */}
      <div className="dashboard-version-info">
        Smart DevOps {APP_VERSION} • Agentic Infrastructure • {new Date().toLocaleTimeString()}
      </div>

      {/* CHAT FAB */}
      <button className="infra-chat-fab" onClick={() => setChatOpen(!chatOpen)} title="Ask Infra Agent">
        <FaBrain />
      </button>

      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="infra-chat-panel"
          >
            <div className="infra-chat-header">
              <div className="infra-chat-title">
                <FaBrain /> Infra AI Agent
                <span className="infra-chat-mode">{agent.mode}</span>
              </div>
              <button className="infra-chat-close" onClick={() => setChatOpen(false)}>
                <FiXCircle />
              </button>
            </div>
            <div className="infra-chat-messages">
              {chatMessages.map((m, i) => (
                <div key={i} className={`infra-chat-msg ${m.role}`}>
                  <div className="infra-chat-bubble">{m.content}</div>
                  <div className="infra-chat-time">{m.timestamp}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="infra-chat-msg assistant">
                  <div className="infra-chat-bubble"><span className="dots"><span /><span /><span /></span></div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="infra-chat-input-area">
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={handleChatKey}
                placeholder="Try: launch <github-url>, restart <app>, status"
                disabled={chatLoading}
              />
              <button onClick={handleChatSend} disabled={!chatInput.trim() || chatLoading}>
                <FiSend />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default InfraManager;