import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './TrainingDashboard.css';
import {
  FiCpu,
  FiTrendingUp,
  FiBarChart2,
  FiClock,
  FiPlus,
  FiRefreshCw,
  FiDownload,
  FiPlay,
  FiPause,
  FiStopCircle,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
  FiCalendar,
  FiUser,
  FiZap,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import ModelVersions from './ModelVersions';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ============================================
// TRAINING STATUS CARD COMPONENT
// ============================================
const TrainingStatusCard = ({ training }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'running':
        return { icon: FiPlay, className: 'training-card-icon-wrapper-running', label: 'Running', statusClass: 'training-card-status-running' };
      case 'completed':
        return { icon: FiCheckCircle, className: 'training-card-icon-wrapper-completed', label: 'Completed', statusClass: 'training-card-status-completed' };
      case 'failed':
        return { icon: FiXCircle, className: 'training-card-icon-wrapper-failed', label: 'Failed', statusClass: 'training-card-status-failed' };
      case 'paused':
        return { icon: FiPause, className: 'training-card-icon-wrapper-paused', label: 'Paused', statusClass: 'training-card-status-paused' };
      default:
        return { icon: FiClock, className: 'training-card-icon-wrapper-pending', label: 'Pending', statusClass: 'training-card-status-pending' };
    }
  };

  const config = getStatusConfig(training.status);
  const StatusIcon = config.icon;

  const getProgressClass = (status) => {
    switch (status) {
      case 'completed': return 'training-progress-fill-completed';
      case 'failed': return 'training-progress-fill-failed';
      case 'running': return 'training-progress-fill-running';
      case 'paused': return 'training-progress-fill-paused';
      default: return 'training-progress-fill-running';
    }
  };

  return (
    <div className="training-card">
      <div className="training-card-header">
        <div className="training-card-left">
          <div className={`training-card-icon-wrapper ${config.className}`}>
            <FaRobot className="training-card-icon" />
          </div>
          <div>
            <h4 className="training-card-name">{training.name}</h4>
            <div className="training-card-meta">
              <span>Model: {training.model}</span>
              <span>•</span>
              <span>Epoch: {training.currentEpoch}/{training.totalEpochs}</span>
              <span>•</span>
              <span>Batch: {training.batchSize}</span>
            </div>
          </div>
        </div>
        <div className={`training-card-status ${config.statusClass}`}>
          <StatusIcon className="training-card-icon" style={{ width: '0.75rem', height: '0.75rem' }} />
          <span>{config.label}</span>
        </div>
      </div>

      {/* Progress */}
      <div className="training-progress">
        <div className="training-progress-header">
          <span>Progress</span>
          <span>{training.progress}%</span>
        </div>
        <div className="training-progress-bar">
          <div
            className={`training-progress-fill ${getProgressClass(training.status)}`}
            style={{ width: `${training.progress}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="training-metrics-grid">
        <div className="training-metric">
          <p className="training-metric-label">Loss</p>
          <p className="training-metric-value">{training.loss?.toFixed(4) || '—'}</p>
        </div>
        <div className="training-metric">
          <p className="training-metric-label">Accuracy</p>
          <p className="training-metric-value">{training.accuracy ? `${(training.accuracy * 100).toFixed(1)}%` : '—'}</p>
        </div>
        <div className="training-metric">
          <p className="training-metric-label">F1 Score</p>
          <p className="training-metric-value">{training.f1 ? training.f1.toFixed(3) : '—'}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="training-actions">
        {training.status === 'running' && (
          <>
            <button
              onClick={() => toast.info('Pausing training...')}
              className="training-action-btn training-action-btn-warning"
            >
              <FiPause /> Pause
            </button>
            <button
              onClick={() => toast.info('Stopping training...')}
              className="training-action-btn training-action-btn-danger"
            >
              <FiStopCircle /> Stop
            </button>
          </>
        )}
        {training.status === 'paused' && (
          <button
            onClick={() => toast.info('Resuming training...')}
            className="training-action-btn training-action-btn-primary"
          >
            <FiPlay /> Resume
          </button>
        )}
        {training.status === 'completed' && (
          <button
            onClick={() => toast.success('Model deployed!')}
            className="training-action-btn training-action-btn-success"
          >
            <FiZap /> Deploy
          </button>
        )}
        <button
          onClick={() => toast.info('Viewing details...')}
          className="training-action-btn training-action-btn-secondary"
        >
          Details
        </button>
      </div>
    </div>
  );
};

// ============================================
// MAIN TRAINING DASHBOARD COMPONENT
// ============================================
const TrainingDashboard = () => {
  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showVersions, setShowVersions] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    running: 0,
    completed: 0,
    failed: 0,
    avgAccuracy: 0,
  });

  // ============================================
  // FETCH DATA
  // ============================================
  useEffect(() => {
    fetchTrainings();
    const interval = setInterval(fetchTrainings, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchTrainings = async () => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      setTrainings(mockTrainings);
      setStats({
        total: mockTrainings.length,
        running: mockTrainings.filter(t => t.status === 'running').length,
        completed: mockTrainings.filter(t => t.status === 'completed').length,
        failed: mockTrainings.filter(t => t.status === 'failed').length,
        avgAccuracy: mockTrainings.reduce((acc, t) => acc + (t.accuracy || 0), 0) / mockTrainings.length,
      });
    } catch (error) {
      console.error('Error fetching trainings:', error);
      toast.error('Failed to load trainings');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchTrainings();
    toast.success('Dashboard refreshed');
  };

  // ============================================
  // CHART CONFIGURATIONS
  // ============================================
  const chartData = {
    labels: ['Epoch 1', 'Epoch 2', 'Epoch 3', 'Epoch 4', 'Epoch 5', 'Epoch 6', 'Epoch 7'],
    datasets: [
      {
        label: 'Training Accuracy',
        data: [65, 72, 78, 82, 87, 90, 93],
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
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
      {
        label: 'Validation Accuracy',
        data: [62, 70, 75, 80, 84, 88, 91],
        borderColor: '#d946ef',
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return null;
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(217, 70, 239, 0.3)');
          gradient.addColorStop(1, 'rgba(217, 70, 239, 0.02)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#d946ef',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
      {
        label: 'Loss',
        data: [0.8, 0.6, 0.45, 0.32, 0.25, 0.18, 0.12],
        borderColor: '#ef4444',
        borderDash: [5, 5],
        fill: false,
        tension: 0.4,
        pointBackgroundColor: '#ef4444',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        yAxisID: 'y1',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'line',
          padding: 16,
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
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
          drawBorder: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 10 },
          callback: function(value) { return value + '%'; },
        },
      },
      y1: {
        position: 'right',
        min: 0,
        max: 1,
        grid: { display: false },
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
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  const doughnutData = {
    labels: ['Running', 'Completed', 'Failed', 'Pending'],
    datasets: [
      {
        data: [stats.running, stats.completed, stats.failed, stats.total - stats.running - stats.completed - stats.failed],
        backgroundColor: ['#3b82f6', '#10b981', '#ef4444', '#94a3b8'],
        borderWidth: 0,
        hoverOffset: 8,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 12,
          usePointStyle: true,
          pointStyle: 'circle',
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
      },
    },
    cutout: '65%',
  };

  // ============================================
  // LOADING STATE
  // ============================================
  if (loading) {
    return (
      <div className="training-loading">
        <div className="training-loading-header">
          <div className="training-loading-title"></div>
          <div className="training-loading-btn"></div>
        </div>
        <div className="training-loading-grid">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="training-loading-card">
              <div className="training-loading-card-line training-loading-card-line-short"></div>
              <div className="training-loading-card-line" style={{ width: '75%' }}></div>
            </div>
          ))}
        </div>
        <div className="training-loading-chart">
          <div className="training-loading-chart-inner"></div>
        </div>
      </div>
    );
  }

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="training-dashboard">
      {/* Header */}
      <div className="training-header">
        <div>
          <h2 className="training-header-title">
            <FiCpu className="training-header-title-icon" />
            Model Training
          </h2>
          <p className="training-header-subtitle">
            Train and manage your AI models
          </p>
        </div>
        <div className="training-header-actions">
          <button
            onClick={() => setShowVersions(!showVersions)}
            className="training-header-btn"
          >
            <FiBarChart2 className="training-header-btn-icon" />
            Models
          </button>
          <button
            onClick={handleRefresh}
            className="training-header-btn training-header-btn-icon-only"
          >
            <FiRefreshCw className="training-header-btn-icon" />
          </button>
          <button
            onClick={() => toast.info('Starting new training...')}
            className="training-header-btn training-header-btn-primary"
          >
            <FiPlus className="training-header-btn-icon" />
            New Training
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="training-stats-grid">
        <div className="training-stat-card">
          <p className="training-stat-label">Total Trainings</p>
          <p className="training-stat-value">{stats.total}</p>
        </div>
        <div className="training-stat-card">
          <p className="training-stat-label">Running</p>
          <p className="training-stat-value training-stat-value-primary">{stats.running}</p>
        </div>
        <div className="training-stat-card">
          <p className="training-stat-label">Completed</p>
          <p className="training-stat-value training-stat-value-success">{stats.completed}</p>
        </div>
        <div className="training-stat-card">
          <p className="training-stat-label">Avg Accuracy</p>
          <p className="training-stat-value training-stat-value-accent">
            {stats.avgAccuracy ? `${(stats.avgAccuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="training-charts-grid">
        <div className="training-chart-card training-chart-card-large">
          <div className="training-chart-header">
            <h4 className="training-chart-title">Training Progress</h4>
            <span className="training-chart-subtitle">Last 7 epochs</span>
          </div>
          <div className="training-chart-wrapper">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

        <div className="training-chart-card">
          <div className="training-chart-header">
            <h4 className="training-chart-title">Status Distribution</h4>
          </div>
          <div className="training-chart-doughnut-wrapper">
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
        </div>
      </div>

      {/* Training List */}
      <div className="training-list-section">
        <div className="training-list-header">
          <h3 className="training-list-title">Active Trainings</h3>
          <span className="training-list-count">
            {trainings.filter(t => t.status === 'running' || t.status === 'paused').length} running
          </span>
        </div>
        <div className="training-list">
          {trainings.map((training) => (
            <TrainingStatusCard key={training.id} training={training} />
          ))}
        </div>
      </div>

      {/* Model Versions */}
      <AnimatePresence>
        {showVersions && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="training-versions-panel"
          >
            <ModelVersions onClose={() => setShowVersions(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Version Info - Same as Dashboard */}
      <div className="training-version-info">
        Smart DevOps Assistant v2.3.1 • Auto-upgrade enabled • {new Date().getFullYear()}
      </div>
    </div>
  );
};

// Mock data
const mockTrainings = [
  {
    id: '1',
    name: 'DevOps Model v2.3.1',
    model: 'GPT-3.5-Turbo',
    status: 'running',
    progress: 68,
    currentEpoch: 7,
    totalEpochs: 10,
    batchSize: 32,
    loss: 0.023,
    accuracy: 0.947,
    f1: 0.945,
    startedAt: new Date().toISOString(),
  },
  {
    id: '2',
    name: 'Log Analyzer Model',
    model: 'BERT-base',
    status: 'completed',
    progress: 100,
    currentEpoch: 10,
    totalEpochs: 10,
    batchSize: 16,
    loss: 0.015,
    accuracy: 0.978,
    f1: 0.972,
    startedAt: new Date().toISOString(),
  },
  {
    id: '3',
    name: 'Security Scanner Model',
    model: 'CodeBERT',
    status: 'failed',
    progress: 45,
    currentEpoch: 4,
    totalEpochs: 8,
    batchSize: 24,
    loss: 0.456,
    accuracy: 0.782,
    f1: 0.765,
    startedAt: new Date().toISOString(),
  },
  {
    id: '4',
    name: 'Incident Predictor Model',
    model: 'LSTM',
    status: 'paused',
    progress: 32,
    currentEpoch: 3,
    totalEpochs: 12,
    batchSize: 64,
    loss: 0.089,
    accuracy: 0.856,
    f1: 0.842,
    startedAt: new Date().toISOString(),
  },
];

export default TrainingDashboard;