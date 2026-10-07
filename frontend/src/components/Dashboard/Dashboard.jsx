import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import '../../styles/main.css';
import './Dashboard.css';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import {
  FiCpu, FiGitBranch, FiServer, FiActivity,
  FiTrendingUp, FiTrendingDown, FiClock,
  FiAlertCircle, FiCheckCircle, FiRefreshCw,
  FiBarChart2, FiZap, FiUsers, FiDollarSign,
  FiSend, FiXCircle, FiHardDrive, FiWifi, FiTarget,
} from 'react-icons/fi';
import { FaRobot, FaMagic } from 'react-icons/fa';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import {
  pipelineAPI, monitoringAPI, infraAPI, actionAPI, trainingAPI,
} from '../../api/assistant';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, Title, Tooltip, Legend, Filler
);

// ============================================
// HELPERS
// ============================================
const timeAgo = (timestamp) => {
  if (!timestamp) return 'just now';
  let ms;
  if (typeof timestamp === 'number') {
    ms = timestamp < 1e12 ? timestamp * 1000 : timestamp;
  } else {
    ms = new Date(timestamp).getTime();
  }
  const diff = Math.floor((Date.now() - ms) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const safe = async (fn, fallback = null) => {
  try {
    if (typeof fn !== 'function') return fallback;
    const result = await fn();
    return result ?? fallback;
  } catch (e) {
    console.warn('API call failed:', e);
    return fallback;
  }
};

// ============================================
// STATS CARD
// ============================================
const StatsCard = ({ title, value, change, icon: Icon, color, subtitle, loading }) => {
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

  const isPositive = change > 0;
  const isNegative = change < 0;
  const hasChange = change !== undefined && change !== null && change !== 0;

  return (
    <div className="dashboard-stats-card">
      <div className="dashboard-stats-card-content">
        <p className="dashboard-stats-card-title">{title}</p>
        <h3 className="dashboard-stats-card-value">{value}</h3>
        {hasChange && (
          <div className="dashboard-stats-card-change">
            {isPositive && <FiTrendingUp className="dashboard-stats-card-change-icon dashboard-stats-card-change-icon-positive" />}
            {isNegative && <FiTrendingDown className="dashboard-stats-card-change-icon dashboard-stats-card-change-icon-negative" />}
            <span className={`dashboard-stats-card-change-text ${
              isPositive ? 'dashboard-stats-card-change-text-positive' :
              isNegative ? 'dashboard-stats-card-change-text-negative' :
              'dashboard-stats-card-change-text-neutral'
            }`}>
              {isPositive ? '+' : ''}{change}%
            </span>
            <span className="dashboard-stats-card-change-label">since last update</span>
          </div>
        )}
        {subtitle && <p className="dashboard-stats-card-subtitle">{subtitle}</p>}
      </div>
      <div className={`dashboard-stats-card-icon-wrapper ${color}`}>
        <Icon className="dashboard-stats-card-icon" />
      </div>
    </div>
  );
};

// ============================================
// LIVE INDICATOR
// ============================================
const LiveIndicator = ({ lastUpdate, refreshing, dataSource }) => {
  const [, setTick] = useState(0);

  useEffect(() => {
    const i = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(i);
  }, []);

  const secondsAgo = lastUpdate ? Math.floor((Date.now() - lastUpdate) / 1000) : 0;
  const isLive = dataSource === 'live';

  return (
    <div className="dashboard-status-badge">
      <span
        className="dashboard-status-dot"
        style={{
          background: refreshing ? '#f59e0b' : isLive ? '#10b981' : '#94a3b8',
          boxShadow: refreshing
            ? '0 0 12px rgba(245, 158, 11, 0.8)'
            : isLive
            ? '0 0 12px rgba(16, 185, 129, 0.8)'
            : 'none',
          animation: refreshing ? 'pulse 1s infinite' : isLive ? 'pulse 2s infinite' : 'none',
        }}
      ></span>
      <span style={{ fontVariantNumeric: 'tabular-nums' }}>
        {refreshing
          ? 'Syncing...'
          : isLive
          ? secondsAgo < 3
            ? 'LIVE'
            : `${secondsAgo}s ago`
          : 'No data'}
      </span>
    </div>
  );
};

// ============================================
// MAIN DASHBOARD
// ============================================
const Dashboard = () => {
  const { user } = useAuth();

  console.log('📊📊📊 DASHBOARD LOADED (REAL DATA) 📊📊📊');

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [dataSource, setDataSource] = useState('live');

  const [stats, setStats] = useState({
    deployments: { value: 0, change: 0 },
    pipelines: { value: 0, change: 0, running: 0 },
    services: { value: 0, change: 0, healthy: 0 },
    incidents: { value: 0, change: 0, critical: 0 },
    uptime: '—',
    activeUsers: 0,
    cost: '$0',
  });

  const [deploymentLabels, setDeploymentLabels] = useState(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
  const [deploymentSeries, setDeploymentSeries] = useState([0, 0, 0, 0, 0, 0, 0]);
  const [incidentData, setIncidentData] = useState([0, 0, 0, 0]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [aiInsights, setAiInsights] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({ cpu: 0, memory: 0, disk: 0, network: 0 });

  const prevStatsRef = useRef(null);

  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your DevOps AI. Ask me about deployments, incidents, or performance.",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // ============================================
  // FETCH REAL DATA
  // ============================================
  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [
        pipelines,
        alerts,
        unified,
        insights,
        actions,
        metrics,
        monitors,
        models,
      ] = await Promise.all([
        safe(() => pipelineAPI.getAll(), []),
        safe(() => monitoringAPI.getAlerts('all'), []),
        safe(() => infraAPI.getUnified(), null),
        safe(() => infraAPI.getInsights(), []),
        safe(() => actionAPI.getAll(), []),
        safe(() => monitoringAPI.getMetrics('1h'), null),
        safe(() => monitoringAPI.getMonitors(), []),
        safe(() => trainingAPI.getModels(), []),
      ]);

      const pipelinesArr = Array.isArray(pipelines) ? pipelines : [];
      const alertsArr = Array.isArray(alerts) ? alerts : [];
      const insightsArr = Array.isArray(insights) ? insights : [];
      const actionsArr = Array.isArray(actions) ? actions : [];
      const monitorsArr = Array.isArray(monitors) ? monitors : [];
      const modelsArr = Array.isArray(models) ? models : [];
      const servicesArr = unified?.services || monitorsArr || [];

      const deploymentsCount = pipelinesArr.length;
      const runningPipelines = pipelinesArr.filter(p => p.status === 'running').length;
      const servicesCount = unified?.stats?.total_services || servicesArr.length || 0;
      const healthyServices = servicesArr.filter(
        s => s.status === 'running' || s.status === 'monitored'
      ).length;
      const incidentsCount = alertsArr.length;
      const criticalIncidents = alertsArr.filter(a => a.severity === 'critical').length;

      const prev = prevStatsRef.current;
      const change = (curr, prevVal) => {
        if (!prevVal || prevVal === 0) return 0;
        return +(((curr - prevVal) / prevVal) * 100).toFixed(1);
      };

      const newStats = {
        deployments: { value: deploymentsCount, change: change(deploymentsCount, prev?.deployments?.value) },
        pipelines: { value: pipelinesArr.length, change: change(pipelinesArr.length, prev?.pipelines?.value), running: runningPipelines },
        services: { value: servicesCount, change: change(servicesCount, prev?.services?.value), healthy: healthyServices },
        incidents: { value: incidentsCount, change: change(incidentsCount, prev?.incidents?.value), critical: criticalIncidents },
        uptime: unified?.health?.status === 'excellent' ? '99.99%'
              : unified?.health?.status === 'good' ? '99.9%'
              : unified?.health?.score ? `${(unified.health.score / 100 * 99.9).toFixed(2)}%` : '—',
        activeUsers: metrics?.active_users || monitorsArr.length || 0,
        cost: metrics?.cost ? `$${metrics.cost}` : '$0',
      };
      setStats(newStats);
      prevStatsRef.current = newStats;

      const dayLabels = [];
      const dayCounts = [0, 0, 0, 0, 0, 0, 0];
      for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        dayLabels.push(d.toLocaleDateString('en', { weekday: 'short' }));
      }
      const now = Date.now();
      pipelinesArr.forEach(p => {
        if (!p.createdAt) return;
        const ts = new Date(p.createdAt).getTime();
        const daysAgo = Math.floor((now - ts) / 86400000);
        if (daysAgo >= 0 && daysAgo < 7) {
          dayCounts[6 - daysAgo]++;
        }
      });
      setDeploymentLabels(dayLabels);
      setDeploymentSeries(dayCounts);

      setIncidentData([
        alertsArr.filter(a => a.severity === 'critical').length,
        alertsArr.filter(a => a.severity === 'high').length,
        alertsArr.filter(a => a.severity === 'medium').length,
        alertsArr.filter(a => a.severity === 'low' || !a.severity).length,
      ]);

      const combined = [
        ...pipelinesArr.slice(0, 6).map(p => ({
          id: `pipe-${p.id}`,
          type: 'deployment',
          title: `${p.name || p.repo} ${p.status === 'success' ? 'deployed' : p.status || 'updated'}`,
          status: p.status === 'success' ? 'success' : p.status === 'failed' ? 'failed' : 'warning',
          time: timeAgo(p.createdAt),
          user: p.owner || 'System',
          _ts: new Date(p.createdAt).getTime() || 0,
        })),
        ...actionsArr.slice(0, 6).map(a => ({
          id: `action-${a.id}`,
          type: a.type || 'action',
          title: a.description || a.title || a.type || 'AI Action',
          status: a.status === 'completed' || a.status === 'success' ? 'success'
                : a.status === 'failed' ? 'failed' : 'warning',
          time: timeAgo(a.created_at || a.timestamp),
          user: a.user || 'AI',
          _ts: new Date(a.created_at || a.timestamp || 0).getTime(),
        })),
      ].sort((a, b) => b._ts - a._ts).slice(0, 6);
      setRecentActivities(combined);

      const merged = [
        ...insightsArr.slice(0, 4).map(i => ({
          id: `ins-${i.id}`,
          severity: i.severity || 'info',
          title: i.title || 'AI Insight',
          message: i.message || '',
        })),
        ...alertsArr.filter(a => a.severity === 'critical' || a.severity === 'high').slice(0, 2).map(a => ({
          id: `alert-${a.id}`,
          severity: a.severity === 'critical' ? 'error' : 'warning',
          title: a.title || 'Alert',
          message: a.message || a.description || '',
        })),
      ].slice(0, 5);
      setAiInsights(merged);

      const hp = unified?.high_performance || {};
      setSystemMetrics({
        cpu: hp.cpu_percent ?? metrics?.cpu ?? 0,
        memory: hp.memory_percent ?? metrics?.memory ?? 0,
        disk: hp.disk_percent ?? metrics?.disk ?? 0,
        network: hp.network_in_mbps ?? metrics?.network ?? 0,
      });

      const hasData = (
        pipelinesArr.length +
        servicesArr.length +
        alertsArr.length +
        actionsArr.length +
        monitorsArr.length +
        modelsArr.length
      ) > 0;
      setDataSource(hasData ? 'live' : 'empty');

      setLastUpdate(Date.now());
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      if (!silent) toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // ⭐ Real-time cross-page events (NEW)
  usePlatformEvents('dashboard', () => fetchAll(true));

  useEffect(() => {
    fetchAll();
    const i = setInterval(() => fetchAll(true), 10000);
    return () => clearInterval(i);
  }, [fetchAll]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAll(true);
    toast.success('Dashboard refreshed');
  };

  const handleChatSend = async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;

    setChatMessages(prev => [
      ...prev,
      { role: 'user', content: msg, timestamp: new Date().toLocaleTimeString() },
    ]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await safe(() => infraAPI.chat(msg), null);
      setChatMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: res?.message || res?.response || "⚠️ AI service not available",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch {
      setChatMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: "⚠️ AI service not available",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleChatKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSend();
    }
  };

  const hasDeployments = deploymentSeries.some(v => v > 0);

  const deploymentChartData = {
    labels: deploymentLabels,
    datasets: [
      {
        label: 'Deployments',
        data: deploymentSeries,
        borderColor: '#3b82f6',
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return 'rgba(59, 130, 246, 0.1)';
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
          gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const deploymentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(59, 130, 246, 0.2)',
        borderWidth: 1,
        borderRadius: 8,
        padding: 12,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(148, 163, 184, 0.1)', drawBorder: false },
        ticks: { color: '#94a3b8', font: { size: 11 }, precision: 0 },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 11 } },
      },
    },
    interaction: { intersect: false, mode: 'index' },
  };

  const hasIncidents = incidentData.some(v => v > 0);

  const incidentChartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [
      {
        data: hasIncidents ? incidentData : [1, 0, 0, 0],
        backgroundColor: hasIncidents
          ? ['#ef4444', '#f59e0b', '#3b82f6', '#10b981']
          : ['rgba(148, 163, 184, 0.2)', 'rgba(148, 163, 184, 0.2)', 'rgba(148, 163, 184, 0.2)', 'rgba(148, 163, 184, 0.2)'],
        borderWidth: 0,
        hoverOffset: hasIncidents ? 8 : 0,
      },
    ],
  };

  const incidentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    plugins: {
      legend: {
        display: hasIncidents,
        position: 'bottom',
        labels: {
          padding: 16,
          usePointStyle: true,
          pointStyle: 'circle',
          font: { size: 11 },
          color: '#94a3b8',
        },
      },
      tooltip: {
        enabled: hasIncidents,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        borderRadius: 8,
        padding: 12,
      },
    },
    cutout: '70%',
  };

  const statsCards = [
    {
      title: 'Total Deployments',
      value: stats.deployments.value.toLocaleString(),
      change: stats.deployments.change,
      icon: FiGitBranch,
      color: 'color-primary',
      subtitle: `${stats.uptime} uptime`,
    },
    {
      title: 'Active Pipelines',
      value: stats.pipelines.value,
      change: stats.pipelines.change,
      icon: FiActivity,
      color: 'color-accent',
      subtitle: `${stats.pipelines.running} running now`,
    },
    {
      title: 'Services',
      value: stats.services.value,
      change: stats.services.change,
      icon: FiServer,
      color: 'color-success',
      subtitle: `${stats.services.healthy} healthy`,
    },
    {
      title: 'Incidents',
      value: stats.incidents.value,
      change: stats.incidents.change,
      icon: FiAlertCircle,
      color: 'color-error',
      subtitle: `${stats.incidents.critical} critical`,
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'status-success';
      case 'failed': return 'status-error';
      case 'warning': return 'status-warning';
      default: return 'status-info';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <FiCheckCircle className="dashboard-status-icon" />;
      case 'failed': return <FiAlertCircle className="dashboard-status-icon" />;
      case 'warning': return <FiAlertCircle className="dashboard-status-icon" />;
      default: return <FiActivity className="dashboard-status-icon" />;
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">
            Welcome back, {user?.name || 'User'}! 👋
          </h2>
          <p className="dashboard-subtitle">
            Real-time view of your DevOps infrastructure • Auto-refresh every 10s
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="dashboard-refresh-btn"
          >
            <FiRefreshCw
              className={`dashboard-refresh-icon ${refreshing ? 'dashboard-refresh-icon-spinning' : ''}`}
            />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          <LiveIndicator
            lastUpdate={lastUpdate}
            refreshing={refreshing}
            dataSource={dataSource}
          />
        </div>
      </div>

      <div className="dashboard-stats-grid">
        {statsCards.map((stat, i) => (
          <StatsCard key={i} {...stat} loading={loading} />
        ))}
      </div>

      <div className="dashboard-charts-grid">
        <div className="dashboard-chart-card dashboard-chart-card-large">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Deployment Activity</h3>
              <p className="dashboard-chart-subtitle">
                {hasDeployments ? 'Last 7 days • live' : 'Last 7 days'}
              </p>
            </div>
            <div className="dashboard-chart-legend">
              <span className="dashboard-chart-legend-item">
                <span className="dashboard-chart-legend-color"></span>
                Deployments
              </span>
            </div>
          </div>
          <div className="dashboard-chart-wrapper">
            {hasDeployments ? (
              <Line data={deploymentChartData} options={deploymentChartOptions} />
            ) : (
              <div className="dashboard-empty-chart">
                <FiGitBranch size={32} />
                <p>No deployment history yet</p>
                <span>Deploy an app to see activity here</span>
              </div>
            )}
          </div>
        </div>

        <div className="dashboard-chart-card">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Incident Distribution</h3>
              <p className="dashboard-chart-subtitle">
                {hasIncidents ? 'By severity • live' : 'No active incidents'}
              </p>
            </div>
          </div>
          <div className="dashboard-chart-wrapper dashboard-chart-doughnut-wrapper" style={{ position: 'relative' }}>
            <Doughnut data={incidentChartData} options={incidentChartOptions} />
            {hasIncidents && (
              <div style={{
                position: 'absolute', top: '50%', left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center', pointerEvents: 'none',
              }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#fff' }}>
                  {stats.incidents.value}
                </div>
                <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1 }}>
                  Alerts
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-two-column-grid">
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">
              <FaMagic style={{ color: '#a855f7', marginRight: 8, display: 'inline' }} />
              AI Insights
            </h3>
            <button className="dashboard-card-view-all">
              {aiInsights.length} {aiInsights.length === 1 ? 'item' : 'items'}
            </button>
          </div>
          <div className="dashboard-activity-list">
            {aiInsights.length === 0 ? (
              <div className="dashboard-activity-item status-success">
                <div className="dashboard-activity-icon">
                  <FiCheckCircle className="dashboard-status-icon" />
                </div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">All systems optimal</p>
                  <div className="dashboard-activity-meta">
                    <span>AI</span>
                    <span className="dashboard-activity-dot"></span>
                    <span>no recommendations</span>
                  </div>
                </div>
              </div>
            ) : (
              <AnimatePresence>
                {aiInsights.map((ins) => (
                  <motion.div
                    key={ins.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className={`dashboard-activity-item ${
                      ins.severity === 'critical' || ins.severity === 'error' ? 'status-error' :
                      ins.severity === 'warning' ? 'status-warning' :
                      ins.severity === 'success' ? 'status-success' :
                      'status-info'
                    }`}
                  >
                    <div className="dashboard-activity-icon">
                      {ins.severity === 'critical' || ins.severity === 'error' ? (
                        <FiAlertCircle className="dashboard-status-icon" />
                      ) : ins.severity === 'success' ? (
                        <FiCheckCircle className="dashboard-status-icon" />
                      ) : (
                        <FiZap className="dashboard-status-icon" />
                      )}
                    </div>
                    <div className="dashboard-activity-content">
                      <p className="dashboard-activity-title">{ins.title}</p>
                      <div className="dashboard-activity-meta">
                        <span>{ins.message}</span>
                      </div>
                    </div>
                    <span className="dashboard-activity-status">AI</span>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">Recent Activity</h3>
            <button className="dashboard-card-view-all">View All</button>
          </div>
          <div className="dashboard-activity-list">
            {recentActivities.length === 0 ? (
              <div className="dashboard-activity-item status-info">
                <div className="dashboard-activity-icon">
                  <FiActivity className="dashboard-status-icon" />
                </div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">No activity yet</p>
                  <div className="dashboard-activity-meta">
                    <span>Deploy or run actions to see history</span>
                  </div>
                </div>
              </div>
            ) : (
              recentActivities.map((activity) => (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`dashboard-activity-item ${getStatusColor(activity.status)}`}
                >
                  <div className="dashboard-activity-icon">
                    {getStatusIcon(activity.status)}
                  </div>
                  <div className="dashboard-activity-content">
                    <p className="dashboard-activity-title">{activity.title}</p>
                    <div className="dashboard-activity-meta">
                      <span>{activity.user}</span>
                      <span className="dashboard-activity-dot"></span>
                      <span>{activity.time}</span>
                    </div>
                  </div>
                  <span className="dashboard-activity-status">{activity.status}</span>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title">
            <FiHardDrive style={{ color: '#3b82f6', marginRight: 8, display: 'inline' }} />
            System Overview
          </h3>
          <span
            className="dashboard-card-view-all"
            style={{ color: dataSource === 'live' ? '#10b981' : '#64748b' }}
          >
            {dataSource === 'live' ? '● Live' : '○ Offline'}
          </span>
        </div>
        <div className="dashboard-system-stats-grid">
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">CPU Usage</p>
            <p className="dashboard-system-stat-value">{systemMetrics.cpu.toFixed(0)}%</p>
            <div className="dashboard-system-stat-bar">
              <div
                className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-primary"
                style={{ width: `${Math.min(100, systemMetrics.cpu)}%`, transition: 'width 0.8s ease' }}
              ></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Memory Usage</p>
            <p className="dashboard-system-stat-value">{systemMetrics.memory.toFixed(0)}%</p>
            <div className="dashboard-system-stat-bar">
              <div
                className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-warning"
                style={{ width: `${Math.min(100, systemMetrics.memory)}%`, transition: 'width 0.8s ease' }}
              ></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Disk Usage</p>
            <p className="dashboard-system-stat-value">{systemMetrics.disk.toFixed(0)}%</p>
            <div className="dashboard-system-stat-bar">
              <div
                className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-info"
                style={{ width: `${Math.min(100, systemMetrics.disk)}%`, transition: 'width 0.8s ease' }}
              ></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Network</p>
            <p className="dashboard-system-stat-value">{systemMetrics.network.toFixed(1)} MB/s</p>
            <div className="dashboard-system-stat-bar">
              <div
                className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-success"
                style={{ width: `${Math.min(100, systemMetrics.network * 5)}%`, transition: 'width 0.8s ease' }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-version-info">
        Smart DevOps Assistant v2.3.1 • Real-time mode •{' '}
        Last sync: {new Date(lastUpdate).toLocaleTimeString()}
      </div>

      <button
        onClick={() => setChatOpen(!chatOpen)}
        title="Ask Dashboard AI"
        className="dashboard-chat-fab"
      >
        <FaRobot />
      </button>

      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="dashboard-chat-panel"
          >
            <div className="dashboard-chat-header">
              <div className="dashboard-chat-title">
                <FaRobot /> Dashboard AI
              </div>
              <button className="dashboard-chat-close" onClick={() => setChatOpen(false)}>
                <FiXCircle />
              </button>
            </div>
            <div className="dashboard-chat-messages">
              {chatMessages.map((m, i) => (
                <div key={i} className={`dashboard-chat-msg ${m.role}`}>
                  <div className="dashboard-chat-bubble">{m.content}</div>
                  <div className="dashboard-chat-time">{m.timestamp}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="dashboard-chat-msg assistant">
                  <div className="dashboard-chat-bubble">thinking...</div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="dashboard-chat-input-area">
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={handleChatKey}
                placeholder="Ask about deployments, incidents..."
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

export default Dashboard;