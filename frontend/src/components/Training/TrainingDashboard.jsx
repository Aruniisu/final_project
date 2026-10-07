import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './TrainingDashboard.css';
import { APP_VERSION } from '../../config/version';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import {
  FiCpu, FiBarChart2, FiClock, FiPlus, FiRefreshCw,
  FiPlay, FiPause, FiStopCircle, FiCheckCircle, FiXCircle, FiZap,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import ModelVersions from './ModelVersions';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, Title, Tooltip, Legend, Filler
);

const API = process.env.REACT_APP_WS_URL || 'http://localhost:5000';

// ============================================
// TRAINING STATUS CARD
// ============================================
const TrainingStatusCard = ({ training }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'running': return { icon: FiPlay, className: 'running', label: 'Running', statusClass: 'running' };
      case 'completed': return { icon: FiCheckCircle, className: 'completed', label: 'Completed', statusClass: 'completed' };
      case 'failed': return { icon: FiXCircle, className: 'failed', label: 'Failed', statusClass: 'failed' };
      case 'paused': return { icon: FiPause, className: 'paused', label: 'Paused', statusClass: 'paused' };
      case 'auto': return { icon: FaRobot, className: 'completed', label: 'Auto-trained', statusClass: 'completed' };
      default: return { icon: FiClock, className: 'pending', label: 'Pending', statusClass: 'pending' };
    }
  };

  const config = getStatusConfig(training.status);
  const StatusIcon = config.icon;
  const isAutoTrained = training.auto_trained;
  const isRunning = training.status === 'running';

  return (
    <div className="training-card">
      <div className="training-card-header">
        <div className="training-card-left">
          <div className={`training-card-icon-wrapper training-card-icon-wrapper-${config.className}`}>
            <FaRobot className="training-card-icon" />
          </div>
          <div>
            <h4 className="training-card-name">
              {training.name}
              {isAutoTrained && (
                <span style={{
                  marginLeft: 8, fontSize: 9, padding: '2px 6px',
                  borderRadius: 4, background: 'rgba(168,85,247,0.2)',
                  color: '#c4b5fd', textTransform: 'uppercase',
                  fontWeight: 700, letterSpacing: 0.5,
                }}>AUTO</span>
              )}
            </h4>
            <div className="training-card-meta">
              <span>Model: {training.model || training.model_type}</span>
              <span>•</span>
              <span>Epoch: {training.currentEpoch || 0}/{training.totalEpochs || 0}</span>
              {training.samples && (<><span>•</span><span>Samples: {training.samples}</span></>)}
            </div>
          </div>
        </div>
        <div className={`training-card-status training-card-status-${config.statusClass}`}>
          <StatusIcon className="training-card-icon" style={{ width: '0.75rem', height: '0.75rem' }} />
          <span>{config.label}</span>
        </div>
      </div>

      <div className="training-progress">
        <div className="training-progress-header">
          <span>Progress</span>
          <span>{training.progress || 0}%</span>
        </div>
        <div className="training-progress-bar">
          <div className={`training-progress-fill training-progress-fill-${config.className}`}
            style={{ width: `${training.progress || 0}%` }} />
        </div>
      </div>

      <div className="training-metrics-grid">
        <div className="training-metric">
          <p className="training-metric-label">Loss</p>
          <p className="training-metric-value">{training.loss?.toFixed(4) || '—'}</p>
        </div>
        <div className="training-metric">
          <p className="training-metric-label">Accuracy</p>
          <p className="training-metric-value">
            {training.accuracy ? `${(training.accuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
        <div className="training-metric">
          <p className="training-metric-label">F1 Score</p>
          <p className="training-metric-value">{training.f1 ? training.f1.toFixed(3) : '—'}</p>
        </div>
      </div>

      <div className="training-actions">
        {isRunning && (
          <>
            <button onClick={() => toast.info('Pause coming soon...')}
              className="training-action-btn training-action-btn-warning">
              <FiPause /> Pause
            </button>
            <button onClick={async () => {
              const res = await fetch(`${API}/api/training/${training.id}/stop`, { method: 'POST' });
              if (res.ok) toast.success('Stopped');
            }} className="training-action-btn training-action-btn-danger">
              <FiStopCircle /> Stop
            </button>
          </>
        )}
        {training.status === 'completed' && (
          <button onClick={async () => {
            const res = await fetch(`${API}/api/training/deploy`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ model_id: training.id }),
            });
            if (res.ok) toast.success('Model deployed!');
          }} className="training-action-btn training-action-btn-success">
            <FiZap /> Deploy
          </button>
        )}
        <button onClick={() => toast.info('Details coming soon')}
          className="training-action-btn training-action-btn-secondary">
          Details
        </button>
      </div>
    </div>
  );
};

// ============================================
// MAIN
// ============================================
const TrainingDashboard = () => {
  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showVersions, setShowVersions] = useState(false);
  const [learning, setLearning] = useState(null);
  const [stats, setStats] = useState({
    total: 0, running: 0, completed: 0, failed: 0, avgAccuracy: 0,
  });

  const fetchTrainings = useCallback(async () => {
    try {
      // Fetch real data from backend
      const [jobsRes, modelsRes, learningRes] = await Promise.all([
        fetch(`${API}/api/training/jobs`).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/training/models`).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/training/learning`).then(r => r.json()).catch(() => null),
      ]);

      const jobsArr = Array.isArray(jobsRes) ? jobsRes : [];
      const modelsArr = Array.isArray(modelsRes) ? modelsRes : [];

      // Combine running jobs + completed models
      const combined = [
        // Running/pending jobs
        ...jobsArr
          .filter(j => j.status === 'running' || j.status === 'pending')
          .map(j => ({
            id: j.id,
            name: j.name,
            model: j.config?.model_type || 'log_classifier',
            model_type: j.config?.model_type,
            status: j.status,
            progress: j.progress || 0,
            currentEpoch: j.current_epoch || 0,
            totalEpochs: j.total_epochs || 10,
            loss: j.loss || 0,
            accuracy: j.accuracy || 0,
            f1: j.f1 || 0,
          })),
        // Completed models (from metadata)
        ...modelsArr.map(m => ({
          id: m.id,
          name: m.name,
          model: m.model_type,
          model_type: m.model_type,
          status: 'completed',
          progress: 100,
          currentEpoch: m.total_epochs || 1,
          totalEpochs: m.total_epochs || 1,
          loss: m.loss || 0,
          accuracy: m.accuracy || 0,
          f1: m.f1 || 0,
          samples: m.samples,
          auto_trained: m.auto_trained || false,
          deployed: m.deployed || false,
        })),
      ];

      setTrainings(combined);

      const completed = combined.filter(t => t.status === 'completed');
      setStats({
        total: combined.length,
        running: combined.filter(t => t.status === 'running').length,
        completed: completed.length,
        failed: combined.filter(t => t.status === 'failed').length,
        avgAccuracy: completed.length > 0
          ? completed.reduce((acc, t) => acc + (t.accuracy || 0), 0) / completed.length
          : 0,
      });

      if (learningRes) setLearning(learningRes);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Live updates
  usePlatformEvents('training', () => {
    console.log('📡 Training page update');
    fetchTrainings();
  });

  useEffect(() => {
    fetchTrainings();
    const interval = setInterval(fetchTrainings, 5000);
    return () => clearInterval(interval);
  }, [fetchTrainings]);

  const handleRefresh = () => { fetchTrainings(); toast.success('Refreshed'); };

  const handleStartTraining = async () => {
    const modelType = window.prompt(
      'Model type?\n\nlog_classifier / anomaly_detector / deploy_predictor',
      'log_classifier'
    );
    if (!modelType) return;

    const valid = ['log_classifier', 'anomaly_detector', 'deploy_predictor'];
    if (!valid.includes(modelType)) {
      toast.error('Invalid model type');
      return;
    }

    toast.loading('Starting...', { id: 'train' });
    try {
      const res = await fetch(`${API}/api/training/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: modelType,
          dataset: modelType,
          epochs: 10,
          n_samples: 1000,
          name: `${modelType} ${new Date().toLocaleTimeString()}`,
        }),
      });
      const data = await res.json();
      if (data.success) {
        toast.success('Started!', { id: 'train' });
        fetchTrainings();
      } else {
        toast.error(data.error || 'Failed', { id: 'train' });
      }
    } catch (e) {
      toast.error('Error', { id: 'train' });
    }
  };

  // Charts (learning curve)
  const history = learning?.progress?.history || [];

  const chartData = {
    labels: history.length > 0
      ? history.map(h => `Gen ${h.gen}`)
      : ['Gen 1', 'Gen 2', 'Gen 3'],
    datasets: [{
      label: 'Accuracy',
      data: history.length > 0
        ? history.map(h => (h.accuracy * 100).toFixed(1))
        : [0, 0, 0],
      borderColor: '#a855f7',
      backgroundColor: (context) => {
        const chart = context.chart;
        const { ctx, chartArea } = chart;
        if (!chartArea) return 'rgba(168,85,247,0.1)';
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, 'rgba(168,85,247,0.3)');
        gradient.addColorStop(1, 'rgba(168,85,247,0.02)');
        return gradient;
      },
      fill: true, tension: 0.4,
      pointBackgroundColor: '#a855f7',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
    }],
  };

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', titleColor: '#fff', bodyColor: '#94a3b8', borderRadius: 8, padding: 12 },
    },
    scales: {
      y: { min: 0, max: 100, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v + '%' } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
    },
  };

  const doughnutData = {
    labels: ['Running', 'Completed', 'Failed', 'Pending'],
    datasets: [{
      data: [
        stats.running,
        stats.completed,
        stats.failed,
        Math.max(0, stats.total - stats.running - stats.completed - stats.failed),
      ],
      backgroundColor: ['#3b82f6', '#10b981', '#ef4444', '#94a3b8'],
      borderWidth: 0, hoverOffset: 8,
    }],
  };

  const doughnutOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true, pointStyle: 'circle', font: { size: 11 }, color: '#94a3b8' } },
      tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', titleColor: '#fff', bodyColor: '#94a3b8', borderRadius: 8, padding: 12 },
    },
    cutout: '65%',
  };

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
      </div>
    );
  }

  return (
    <div className="training-dashboard">
      <div className="training-header">
        <div>
          <h2 className="training-header-title">
            <FiCpu className="training-header-title-icon" />
            Model Training
          </h2>
          <p className="training-header-subtitle">
            Train and manage your AI models • Level 3 Self-Learning
          </p>
        </div>
        <div className="training-header-actions">
          <button onClick={() => setShowVersions(!showVersions)} className="training-header-btn">
            <FiBarChart2 className="training-header-btn-icon" /> Models
          </button>
          <button onClick={handleRefresh} className="training-header-btn training-header-btn-icon-only">
            <FiRefreshCw className="training-header-btn-icon" />
          </button>
          <button onClick={handleStartTraining} className="training-header-btn training-header-btn-primary">
            <FiPlus className="training-header-btn-icon" /> New Training
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="training-stats-grid">
        <div className="training-stat-card">
          <p className="training-stat-label">Total Models</p>
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
            {stats.avgAccuracy > 0 ? `${(stats.avgAccuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
      </div>

      {/* ⭐ Learning Progress Panel — Level 3 */}
      {learning && (
        <div className="training-chart-card" style={{
          marginTop: '1.5rem',
          border: '1px solid rgba(168,85,247,0.3)',
          background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(99,102,241,0.03))',
        }}>
          <div className="training-chart-header">
            <div>
              <h4 className="training-chart-title">🧠 Agent Self-Learning (Level 3)</h4>
              <p className="training-chart-subtitle">
                Auto-retrain every 60s on real agent feedback
              </p>
            </div>
            <span style={{ color: '#10b981', fontSize: 11, fontWeight: 700 }}>
              ● Auto
            </span>
          </div>

          <div className="training-stats-grid" style={{ marginTop: '1rem' }}>
            <div className="training-stat-card">
              <p className="training-stat-label">Feedback Samples</p>
              <p className="training-stat-value">{learning.feedback?.total || 0}</p>
              <p style={{ fontSize: '11px', opacity: 0.5 }}>
                {learning.samples_needed > 0 ? `I need ${learning.samples_needed} ` : 'Ready'}
              </p>
            </div>
            <div className="training-stat-card">
              <p className="training-stat-label">Success Rate</p>
              <p className="training-stat-value training-stat-value-success">
                {((learning.feedback?.success_rate || 0) * 100).toFixed(1)}%
              </p>
              <p style={{ fontSize: '11px', opacity: 0.5 }}>Agent actions</p>
            </div>
            <div className="training-stat-card">
              <p className="training-stat-label">Generations</p>
              <p className="training-stat-value training-stat-value-primary">
                {learning.progress?.generations || 0}
              </p>
              <p style={{ fontSize: '11px', opacity: 0.5 }}>Auto-retrains</p>
            </div>
            <div className="training-stat-card">
              <p className="training-stat-label">Latest Accuracy</p>
              <p className="training-stat-value training-stat-value-accent">
                {((learning.progress?.current_accuracy || 0) * 100).toFixed(1)}%
              </p>
              <p style={{ fontSize: '11px', opacity: 0.5 }}>Current model</p>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="training-charts-grid" style={{ marginTop: '1.5rem' }}>
        <div className="training-chart-card training-chart-card-large">
          <div className="training-chart-header">
            <h4 className="training-chart-title">Learning Curve</h4>
            <span className="training-chart-subtitle">Accuracy per generation</span>
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
          <h3 className="training-list-title">All Models ({trainings.length})</h3>
          <span className="training-list-count">
            {trainings.filter(t => t.auto_trained).length} auto-trained
          </span>
        </div>
        <div className="training-list">
          {trainings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', opacity: 0.5 }}>
              <FiCpu style={{ fontSize: 40, marginBottom: 12 }} />
              <p>No models yet</p>
              <p style={{ fontSize: 12 }}>
                Click "New Training" or generate agent actions to auto-train
              </p>
            </div>
          ) : (
            trainings.map((training) => (
              <TrainingStatusCard key={training.id} training={training} />
            ))
          )}
        </div>
      </div>

      <AnimatePresence>
        {showVersions && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }} className="training-versions-panel">
            <ModelVersions onClose={() => setShowVersions(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="training-version-info">
        Smart DevOps Assistant {APP_VERSION} • Level 3 Auto-Learning • {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default TrainingDashboard;