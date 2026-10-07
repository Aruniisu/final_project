import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './MonitoringDashboard.css';
import {
  FiActivity,
  FiBell,
  FiClock,
  FiTrendingUp,
  FiTrendingDown,
  FiRefreshCw,
  FiFilter,
  FiSearch,
  FiCalendar,
  FiDownload,
  FiZap,
  FiAlertCircle,
  FiCheckCircle,
  FiXCircle,
} from 'react-icons/fi';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import AlertPanel from './AlertPanel';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ============================================
// TIME RANGE SELECTOR COMPONENT
// ============================================
const TimeRangeSelector = ({ selected, onChange }) => {
  const ranges = [
    { id: '1h', label: '1h' },
    { id: '6h', label: '6h' },
    { id: '24h', label: '24h' },
    { id: '7d', label: '7d' },
    { id: '30d', label: '30d' },
  ];

  return (
    <div className="monitoring-time-range">
      {ranges.map((range) => (
        <button
          key={range.id}
          onClick={() => onChange(range.id)}
          className={`monitoring-time-btn ${selected === range.id ? 'monitoring-time-btn-active' : ''}`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};

// ============================================
// METRIC CARD COMPONENT
// ============================================
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
                  isNegative ? 'monitoring-metric-change-text-negative' : 
                  'monitoring-metric-change-text-neutral'
                }`}>
                  {isPositive ? '+' : ''}{change}%
                </span>
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

// ============================================
// MAIN MONITORING DASHBOARD COMPONENT
// ============================================
const MonitoringDashboard = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [loading, setLoading] = useState(true);
  const [showAlerts, setShowAlerts] = useState(false);
  const [metrics, setMetrics] = useState({
    uptime: '99.92%',
    requests: '12.4k',
    errors: '47',
    latency: '234ms',
  });
  const [chartData, setChartData] = useState(null);
  const [statusData, setStatusData] = useState({
    services: { total: 12, active: 12 },
    endpoints: { total: 48, active: 45 },
    warnings: 3,
    critical: 1,
  });

  // ============================================
  // FETCH DATA
  // ============================================
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const labels = Array.from({ length: 20 }, (_, i) => {
        const now = Date.now();
        return new Date(now - (20 - i) * 60000).toLocaleTimeString();
      });

      setChartData({
        labels,
        datasets: [
          {
            label: 'Response Time (ms)',
            data: labels.map(() => 50 + Math.random() * 250),
            borderColor: '#3b82f6',
            backgroundColor: (context) => {
              const chart = context.chart;
              const { ctx, chartArea } = chart;
              if (!chartArea) return null;
              const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
              gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
              gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');
              return gradient;
            },
            fill: true,
            tension: 0.4,
            pointRadius: 2,
          },
          {
            label: 'Error Rate (%)',
            data: labels.map(() => Math.random() * 5),
            borderColor: '#ef4444',
            backgroundColor: (context) => {
              const chart = context.chart;
              const { ctx, chartArea } = chart;
              if (!chartArea) return null;
              const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
              gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
              gradient.addColorStop(1, 'rgba(239, 68, 68, 0.02)');
              return gradient;
            },
            fill: true,
            tension: 0.4,
            pointRadius: 2,
          },
        ],
      });

      setMetrics({
        uptime: '99.92%',
        requests: (12 + Math.random() * 2).toFixed(1) + 'k',
        errors: Math.floor(30 + Math.random() * 40).toString(),
        latency: Math.floor(150 + Math.random() * 150) + 'ms',
      });

      setStatusData({
        services: { total: 12, active: 12 },
        endpoints: { total: 48, active: 45 },
        warnings: Math.floor(Math.random() * 5),
        critical: Math.floor(Math.random() * 2),
      });

      setLoading(false);
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      toast.error('Failed to load monitoring data');
      setLoading(false);
    }
  };

  // ============================================
  // HANDLERS
  // ============================================
  const handleRefresh = () => {
    fetchData();
    toast.success('Dashboard refreshed');
  };

  // ============================================
  // CHART OPTIONS
  // ============================================
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'line',
          padding: 20,
          font: { size: 11 },
          color: '#94a3b8',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        borderRadius: 8,
        padding: 12,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}`;
          }
        }
      },
    },
    scales: {
      y: {
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
          drawBorder: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 10 },
        },
      },
      x: {
        grid: { display: false },
        ticks: {
          color: '#94a3b8',
          font: { size: 10 },
          maxTicksLimit: 10,
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  // ============================================
  // LOADING STATE
  // ============================================
  if (loading && !chartData) {
    return (
      <div className="monitoring-loading">
        <div className="monitoring-loading-header">
          <div className="monitoring-loading-title"></div>
          <div className="monitoring-loading-btn"></div>
        </div>
        <div className="monitoring-loading-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="monitoring-loading-card">
              <div className="monitoring-loading-card-line monitoring-loading-card-line-short"></div>
              <div className="monitoring-loading-card-line" style={{ width: '75%' }}></div>
              <div className="monitoring-loading-card-line" style={{ width: '50%' }}></div>
            </div>
          ))}
        </div>
        <div className="monitoring-loading-chart">
          <div className="monitoring-loading-chart-inner"></div>
        </div>
      </div>
    );
  }

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="monitoring-dashboard">
      {/* Header */}
      <div className="monitoring-header">
        <div>
          <h2 className="monitoring-header-title">
            <FiActivity className="monitoring-header-title-icon" />
            Monitoring Dashboard
          </h2>
          <p className="monitoring-header-subtitle">
            Real-time system monitoring and metrics
          </p>
        </div>
        <div className="monitoring-header-actions">
          <TimeRangeSelector selected={timeRange} onChange={setTimeRange} />
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="monitoring-header-btn"
            title="View Alerts"
          >
            <FiBell />
            {statusData.critical > 0 && (
              <span className="monitoring-header-btn-badge">{statusData.critical}</span>
            )}
          </button>
          <button onClick={handleRefresh} className="monitoring-header-btn" title="Refresh">
            <FiRefreshCw />
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="monitoring-metrics-grid">
        <MetricCard
          title="Uptime"
          value={metrics.uptime}
          icon={FiCheckCircle}
          color="monitoring-metric-icon-wrapper-text-success"
          subtitle="Last 24h"
        />
        <MetricCard
          title="Total Requests"
          value={metrics.requests}
          change={8.2}
          icon={FiActivity}
          color="monitoring-metric-icon-wrapper-text-primary"
          subtitle="Last hour"
        />
        <MetricCard
          title="Errors"
          value={metrics.errors}
          change={-12.5}
          icon={FiAlertCircle}
          color="monitoring-metric-icon-wrapper-text-error"
          subtitle="Last hour"
        />
        <MetricCard
          title="Avg Latency"
          value={metrics.latency}
          change={-3.1}
          icon={FiClock}
          color="monitoring-metric-icon-wrapper-text-warning"
          subtitle="P95: 432ms"
        />
      </div>

      {/* Charts Section */}
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
                <span className="monitoring-status-dot monitoring-status-dot-success"></span>
                Services
              </span>
              <span className="monitoring-status-value">
                {statusData.services.active}/{statusData.services.total}
              </span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-success"></span>
                Endpoints
              </span>
              <span className="monitoring-status-value">
                {statusData.endpoints.active}/{statusData.endpoints.total}
              </span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-warning"></span>
                Warnings
              </span>
              <span className="monitoring-status-value monitoring-status-value-warning">
                {statusData.warnings}
              </span>
            </div>
            <div className="monitoring-status-item">
              <span className="monitoring-status-left">
                <span className="monitoring-status-dot monitoring-status-dot-error"></span>
                Critical
              </span>
              <span className="monitoring-status-value monitoring-status-value-error">
                {statusData.critical}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Panel */}
      <AnimatePresence>
        {showAlerts && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="monitoring-alerts-panel"
          >
            <AlertPanel onClose={() => setShowAlerts(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Version Info - Same as Dashboard */}
      <div className="monitoring-version-info">
        Smart DevOps Assistant v2.3.1 • Auto-upgrade enabled • {new Date().getFullYear()}
      </div>
    </div>
  );
};

export default MonitoringDashboard;