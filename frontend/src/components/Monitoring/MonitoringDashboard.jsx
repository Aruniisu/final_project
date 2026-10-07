import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './MonitoringDashboard.css';
import { APP_VERSION } from '../../config/version';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import {
  FiActivity, FiBell, FiClock, FiTrendingUp, FiTrendingDown,
  FiRefreshCw, FiAlertCircle, FiCheckCircle, FiGlobe, FiTrash2,
  FiPauseCircle,
} from 'react-icons/fi';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import { monitoringAPI } from '../../api/assistant';
import AlertPanel from './AlertPanel';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
);

const TimeRangeSelector = ({ selected, onChange }) => {
  const ranges = [
    { id: '1h', label: '1h' }, { id: '6h', label: '6h' },
    { id: '24h', label: '24h' }, { id: '7d', label: '7d' }, { id: '30d', label: '30d' },
  ];
  return (
    <div className="monitoring-time-range">
      {ranges.map((range) => (
        <button key={range.id} onClick={() => onChange(range.id)}
          className={`monitoring-time-btn ${selected === range.id ? 'monitoring-time-btn-active' : ''}`}>
          {range.label}
        </button>
      ))}
    </div>
  );
};

const MetricCard = ({ title, value, change, icon: Icon, color, subtitle }) => {
  const isPositive = change > 0;
  const isNegative = change < 0;
  return (
    <div className="monitoring-metric-card">
      <div className="monitoring-metric-content">
        <div className="monitoring-metric-left">
          <p className="monitoring-metric-label">{title}</p>
          <p className="monitoring-metric-value">{value}</p>
          <div className="monitoring-metric-change">
            {change !== undefined && change !== null && (
              <>
                {isPositive && <FiTrendingUp className="monitoring-metric-change-icon monitoring-metric-change-icon-positive" />}
                {isNegative && <FiTrendingDown className="monitoring-metric-change-icon monitoring-metric-change-icon-negative" />}
                <span className={`monitoring-metric-change-text ${
                  isPositive ? 'monitoring-metric-change-text-positive' :
                  isNegative ? 'monitoring-metric-change-text-negative' : ''
                }`}>{isPositive ? '+' : ''}{change}%</span>
              </>
            )}
            {subtitle && <span className="monitoring-metric-subtitle">{subtitle}</span>}
          </div>
        </div>
        <div className={`monitoring-metric-icon-wrapper ${color}`}>
          <Icon className="monitoring-metric-icon" />
        </div>
      </div>
    </div>
  );
};

const MonitoringDashboard = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);

  const [metrics, setMetrics] = useState({ uptime: '0%', requests: '0', errors: '0', latency: '0ms' });
  const [monitors, setMonitors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [statusData, setStatusData] = useState({
    services: { total: 0, active: 0 }, endpoints: { total: 0, active: 0 }, warnings: 0, critical: 0,
  });

  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [metricsRes, alertsRes, healthRes] = await Promise.all([
        monitoringAPI.getMetrics(), monitoringAPI.getAlerts(), monitoringAPI.getHealth(),
      ]);

      if (metricsRes?.success !== false && metricsRes?.metrics) {
        setMetrics({
          uptime: metricsRes.metrics.uptime || '0%',
          requests: metricsRes.metrics.requests || '0',
          errors: String(metricsRes.metrics.errors || 0),
          latency: metricsRes.metrics.latency || '0ms',
        });
        const monList = metricsRes.monitors || [];
        setMonitors(monList);
        buildChartData(monList);
      }
      setAlerts(alertsRes || []);
      if (healthRes?.success !== false) {
        setHealth(healthRes);
        setStatusData({
          services: { total: healthRes.services?.total || 0, active: healthRes.services?.healthy || 0 },
          endpoints: { total: 0, active: 0 },
          warnings: healthRes.services?.warning || 0,
          critical: healthRes.services?.critical || 0,
        });
      }
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false); setRefreshing(false);
    }
  }, []);

  // ⭐ Real-time cross-page events (NEW)
  usePlatformEvents('monitoring', () => fetchData(true));

  const buildChartData = (monList) => {
    const allChecks = [];
    monList.forEach(m => {
      (m.checks || []).forEach(c => {
        allChecks.push({
          time: c.time_str || new Date(c.timestamp * 1000).toISOString(),
          latency: c.latency_ms || 0,
          error: c.success ? 0 : 100,
        });
      });
    });
    allChecks.sort((a, b) => new Date(a.time) - new Date(b.time));
    const recent = allChecks.slice(-20);

    if (recent.length === 0) {
      const labels = Array.from({ length: 10 }, (_, i) => `-${9 - i}m`);
      setChartData({
        labels,
        datasets: [{ label: 'Response Time (ms)', data: labels.map(() => 0),
          borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true, tension: 0.4, pointRadius: 2 }],
      });
      return;
    }

    const labels = recent.map(c => {
      try { return new Date(c.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
      catch { return ''; }
    });

    setChartData({
      labels,
      datasets: [
        { label: 'Response Time (ms)', data: recent.map(c => c.latency),
          borderColor: '#3b82f6',
          backgroundColor: (context) => {
            const chart = context.chart; const { ctx, chartArea } = chart;
            if (!chartArea) return 'rgba(59, 130, 246, 0.1)';
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');
            return gradient;
          },
          fill: true, tension: 0.4, pointRadius: 2 },
        { label: 'Error Rate (%)', data: recent.map(c => c.error),
          borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true, tension: 0.4, pointRadius: 2 },
      ],
    });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData(true), 5000);
    return () => clearInterval(interval);
  }, [fetchData, timeRange]);

  const handleRefresh = () => { setRefreshing(true); fetchData(true); toast.success('Refreshed'); };

  const handleStopMonitor = async (id) => {
    const res = await monitoringAPI.stopMonitor(id);
    if (res.success) { toast.success('Monitor stopped'); fetchData(true); }
    else toast.error('Failed to stop');
  };

  const handleDeleteMonitor = async (id) => {
    if (!window.confirm('Delete this monitor?')) return;
    const res = await monitoringAPI.deleteMonitor(id);
    if (res.success) { toast.success('Deleted'); fetchData(true); }
    else toast.error('Failed to delete');
  };

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'line', padding: 20, font: { size: 11 }, color: '#94a3b8' } },
      tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#ffffff', bodyColor: '#94a3b8', borderRadius: 8, padding: 12 },
    },
    scales: {
      y: { grid: { color: 'rgba(148, 163, 184, 0.1)', drawBorder: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 10 } },
    },
    interaction: { intersect: false, mode: 'index' },
  };

  if (loading && !chartData) {
    return (
      <div className="monitoring-loading">
        <div className="monitoring-loading-header">
          <div className="monitoring-loading-title"></div><div className="monitoring-loading-btn"></div>
        </div>
        <div className="monitoring-loading-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="monitoring-loading-card">
              <div className="monitoring-loading-card-line monitoring-loading-card-line-short"></div>
              <div className="monitoring-loading-card-line" style={{ width: '75%' }}></div>
            </div>
          ))}
        </div>
        <div className="monitoring-loading-chart"><div className="monitoring-loading-chart-inner"></div></div>
      </div>
    );
  }

  return (
    <div className="monitoring-dashboard">
      <div className="monitoring-header">
        <div>
          <h2 className="monitoring-header-title">
            <FiActivity className="monitoring-header-title-icon" />Monitoring Dashboard
          </h2>
          <p className="monitoring-header-subtitle">Real-time system monitoring and metrics</p>
        </div>
        <div className="monitoring-header-actions">
          <TimeRangeSelector selected={timeRange} onChange={setTimeRange} />
          <button onClick={() => setShowAlerts(!showAlerts)} className="monitoring-header-btn" title="View Alerts">
            <FiBell />
            {alerts.length > 0 && <span className="monitoring-header-btn-badge">{alerts.length}</span>}
          </button>
          <button onClick={handleRefresh} className="monitoring-header-btn" title="Refresh">
            <FiRefreshCw className={refreshing ? 'spin' : ''} />
          </button>
        </div>
      </div>

      <div className="monitoring-metrics-grid">
        <MetricCard title="Uptime" value={metrics.uptime} icon={FiCheckCircle}
          color="monitoring-metric-icon-wrapper-text-success"
          subtitle={`${monitors.filter(m => m.status === 'running').length} active`} />
        <MetricCard title="Total Checks" value={metrics.requests} icon={FiActivity}
          color="monitoring-metric-icon-wrapper-text-primary" subtitle="HTTP checks" />
        <MetricCard title="Errors" value={metrics.errors} icon={FiAlertCircle}
          color="monitoring-metric-icon-wrapper-text-error" subtitle="Failed checks" />
        <MetricCard title="Avg Latency" value={metrics.latency} icon={FiClock}
          color="monitoring-metric-icon-wrapper-text-warning" subtitle="Response time" />
      </div>

      <div className="monitoring-charts-grid">
        <div className="monitoring-chart-card monitoring-chart-card-large">
          <div className="monitoring-chart-header">
            <div>
              <h4 className="monitoring-chart-title">Performance Metrics</h4>
              <p className="monitoring-chart-subtitle">Response time & error rate</p>
            </div>
            <span className="monitoring-chart-live">● Live</span>
          </div>
          <div className="monitoring-chart-wrapper">
            {chartData && <Line data={chartData} options={chartOptions} />}
          </div>
        </div>

        <div className="monitoring-chart-card">
          <div className="monitoring-chart-header">
            <h4 className="monitoring-chart-title">Status Overview</h4>
          </div>
          <div className="monitoring-status-list">
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-success"></span>Services
              </span>
              <span className="monitoring-status-value">{statusData.services.active}/{statusData.services.total}</span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-warning"></span>Warnings
              </span>
              <span className="monitoring-status-value monitoring-status-value-warning">{statusData.warnings}</span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-error"></span>Critical
              </span>
              <span className="monitoring-status-value monitoring-status-value-error">{statusData.critical}</span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-success"></span>Monitors
              </span>
              <span className="monitoring-status-value">{monitors.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="monitoring-chart-card" style={{ marginTop: '1.5rem' }}>
        <div className="monitoring-chart-header">
          <div>
            <h4 className="monitoring-chart-title">Active Monitors ({monitors.length})</h4>
            <p className="monitoring-chart-subtitle">Live URL monitoring</p>
          </div>
        </div>

        {monitors.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', opacity: 0.5 }}>
            <FiGlobe style={{ fontSize: '40px', marginBottom: '12px' }} />
            <p style={{ fontSize: '14px', margin: 0 }}>No monitors yet — use <b>Monitor</b> button in AI Assistant</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginTop: '8px' }}>
            {monitors.map((m) => (
              <div key={m.id} className="monitor-item-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <span className={`monitoring-status-dot ${m.status === 'running' ? 'monitoring-status-dot-success' : 'monitoring-status-dot-error'}`}></span>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.url}</div>
                    <div style={{ fontSize: '10px', opacity: 0.5 }}>{m.project_name || 'Unknown'} • every {m.interval}s</div>
                  </div>
                  <span style={{
                    fontSize: '10px', padding: '3px 8px', borderRadius: '6px',
                    background: m.status === 'running' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                    color: m.status === 'running' ? '#10b981' : '#ef4444',
                    fontWeight: 700, textTransform: 'uppercase',
                  }}>{m.status}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '11px' }}>
                  <div><div style={{ opacity: 0.5, fontSize: '10px' }}>UPTIME</div>
                    <div style={{ fontWeight: 700, color: m.uptime_percent >= 99 ? '#10b981' : m.uptime_percent >= 80 ? '#f59e0b' : '#ef4444' }}>
                      {m.uptime_percent?.toFixed(1) || 0}%</div></div>
                  <div><div style={{ opacity: 0.5, fontSize: '10px' }}>LATENCY</div>
                    <div style={{ fontWeight: 700 }}>{m.avg_latency_ms || 0}ms</div></div>
                  <div><div style={{ opacity: 0.5, fontSize: '10px' }}>CHECKS</div>
                    <div style={{ fontWeight: 700 }}>{m.total_checks || 0}</div></div>
                  <div><div style={{ opacity: 0.5, fontSize: '10px' }}>ERRORS</div>
                    <div style={{ fontWeight: 700, color: '#ef4444' }}>{m.error_count || 0}</div></div>
                </div>
                <div style={{ display: 'flex', gap: '6px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
                  {m.status === 'running' && (
                    <button onClick={() => handleStopMonitor(m.id)} style={{
                      flex: 1, padding: '6px', fontSize: '11px', background: 'rgba(148, 163, 184, 0.1)',
                      border: 'none', borderRadius: '6px', color: '#94a3b8', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px',
                    }}><FiPauseCircle /> Stop</button>
                  )}
                  <button onClick={() => handleDeleteMonitor(m.id)} style={{
                    flex: 1, padding: '6px', fontSize: '11px', background: 'rgba(239, 68, 68, 0.1)',
                    border: 'none', borderRadius: '6px', color: '#ef4444', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px',
                  }}><FiTrash2 /> Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {showAlerts && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className="monitoring-alerts-panel">
            <AlertPanel onClose={() => setShowAlerts(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="monitoring-version-info">
        Smart DevOps Assistant {APP_VERSION} • Auto-refresh: 5s • {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default MonitoringDashboard;