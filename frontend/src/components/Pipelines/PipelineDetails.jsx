import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiArrowLeft,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiRefreshCw,
  FiPlay,
  FiPause,
  FiStopCircle,
  FiDownload,
  FiCopy,
  FiShare2,
  FiAlertCircle,
  FiActivity,
  FiGitBranch,
  FiUser,
  FiCalendar,
  FiCode,
} from 'react-icons/fi';
import { FaGithub } from 'react-icons/fa';
import toast from 'react-hot-toast';
import { pipelineAPI } from '../../api/assistant';

const LogViewer = ({ logs, isLive }) => {
  const logEndRef = React.useRef(null);

  React.useEffect(() => {
    if (isLive) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isLive]);

  return (
    <div className="bg-slate-900 rounded-xl p-4 font-mono text-sm overflow-x-auto">
      <div className="space-y-0.5">
        {logs.map((log, index) => (
          <div key={index} className="flex items-start gap-3 text-xs">
            <span className="text-slate-500 whitespace-nowrap">
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>
            <span className={`${
              log.level === 'error' ? 'text-error-400' :
              log.level === 'warning' ? 'text-warning-400' :
              log.level === 'success' ? 'text-success-400' :
              'text-slate-300'
            }`}>
              {log.message}
            </span>
          </div>
        ))}
        {isLive && (
          <div className="flex items-center gap-2 text-xs text-primary-400">
            <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse" />
            Streaming logs...
          </div>
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};

const PipelineDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pipeline, setPipeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');

  useEffect(() => {
    fetchPipelineDetails();
    const interval = setInterval(() => {
      if (pipeline?.status === 'running') {
        fetchPipelineDetails();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [id]);

  const fetchPipelineDetails = async () => {
    try {
      setLoading(true);
      const response = await pipelineAPI.getDetails(id);
      setPipeline(response || mockPipelineDetails);
      setLogs(response?.logs || mockLogs);
    } catch (error) {
      console.error('Error fetching pipeline details:', error);
      setPipeline(mockPipelineDetails);
      setLogs(mockLogs);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await pipelineAPI.getLogs(id);
      setLogs(response || mockLogs);
      toast.success('Logs refreshed');
    } catch (error) {
      toast.error('Failed to fetch logs');
    }
  };

  const handleTrigger = async () => {
    try {
      await pipelineAPI.trigger(id);
      toast.success('Pipeline triggered');
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to trigger pipeline');
    }
  };

  const handleRetry = async () => {
    try {
      await pipelineAPI.retry(id);
      toast.success('Retry started');
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to retry');
    }
  };

  const handleCancel = async () => {
    try {
      await pipelineAPI.cancel(id);
      toast.success('Pipeline cancelled');
      fetchPipelineDetails();
    } catch (error) {
      toast.error('Failed to cancel');
    }
  };

  const handleCopyLogs = () => {
    const logText = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(logText);
    toast.success('Logs copied to clipboard');
  };

  const handleDownloadLogs = () => {
    const logText = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pipeline-${id}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Logs downloaded');
  };

  const getStatusConfig = (status) => {
    switch (status) {
      case 'running':
        return { icon: FiActivity, color: 'text-primary-500', bgColor: 'bg-primary-500/10', label: 'Running' };
      case 'success':
        return { icon: FiCheckCircle, color: 'text-success-500', bgColor: 'bg-success-500/10', label: 'Success' };
      case 'failed':
        return { icon: FiXCircle, color: 'text-error-500', bgColor: 'bg-error-500/10', label: 'Failed' };
      case 'pending':
        return { icon: FiClock, color: 'text-warning-500', bgColor: 'bg-warning-500/10', label: 'Pending' };
      case 'cancelled':
        return { icon: FiStopCircle, color: 'text-slate-500', bgColor: 'bg-slate-500/10', label: 'Cancelled' };
      default:
        return { icon: FiGitBranch, color: 'text-slate-500', bgColor: 'bg-slate-500/10', label: 'Unknown' };
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
          <div className="flex-1">
            <div className="h-6 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 w-64 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
          </div>
        </div>
        <div className="glass-card p-6">
          <div className="space-y-4">
            <div className="h-20 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
            <div className="h-40 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto">
          <FiAlertCircle className="w-8 h-8 text-slate-400" />
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">Pipeline not found</p>
        <button
          onClick={() => navigate('/pipelines')}
          className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-xl"
        >
          Back to Pipelines
        </button>
      </div>
    );
  }

  const statusConfig = getStatusConfig(pipeline.status);
  const StatusIcon = statusConfig.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/pipelines')}
            className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <FiArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                {pipeline.name || 'Pipeline Details'}
              </h2>
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                <StatusIcon className="w-3 h-3" />
                <span>{statusConfig.label}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              <FaGithub className="w-3 h-3" />
              <span>{pipeline.repo || 'repo/main'}</span>
              <span>•</span>
              <FiCode className="w-3 h-3" />
              <span>{pipeline.commit || 'abc1234'}</span>
              <span>•</span>
              <FiUser className="w-3 h-3" />
              <span>{pipeline.triggeredBy || 'User'}</span>
              <span>•</span>
              <FiCalendar className="w-3 h-3" />
              <span>{new Date(pipeline.createdAt).toLocaleString()}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchPipelineDetails}
            className="p-2 rounded-xl bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all"
          >
            <FiRefreshCw className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
          {pipeline.status === 'pending' || pipeline.status === 'failed' ? (
            <button
              onClick={handleTrigger}
              className="px-4 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors flex items-center gap-2"
            >
              <FiPlay className="w-4 h-4" />
              Trigger
            </button>
          ) : pipeline.status === 'running' ? (
            <button
              onClick={handleCancel}
              className="px-4 py-2 bg-error-500 text-white rounded-xl font-medium hover:bg-error-600 transition-colors flex items-center gap-2"
            >
              <FiStopCircle className="w-4 h-4" />
              Cancel
            </button>
          ) : pipeline.status === 'success' ? (
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors flex items-center gap-2"
            >
              <FiRefreshCw className="w-4 h-4" />
              Retry
            </button>
          ) : null}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        {['overview', 'logs', 'steps', 'metrics'].map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-all ${
              selectedTab === tab
                ? 'text-primary-500 border-b-2 border-primary-500'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
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
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {/* Progress */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-500 dark:text-slate-400">Progress</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">
                  {pipeline.progress || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    pipeline.status === 'success' ? 'bg-success-500' :
                    pipeline.status === 'failed' ? 'bg-error-500' :
                    pipeline.status === 'running' ? 'bg-primary-500' :
                    'bg-slate-400'
                  } transition-all duration-500`}
                  style={{ width: `${pipeline.progress || 0}%` }}
                />
              </div>
            </div>

            {/* Steps */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
                Pipeline Steps
              </h3>
              <div className="space-y-3">
                {(pipeline.steps || []).map((step, index) => {
                  const stepStatus = getStatusConfig(step.status);
                  const StepIcon = stepStatus.icon;
                  return (
                    <div key={index} className="flex items-center gap-4 p-3 bg-white/50 dark:bg-slate-800/50 rounded-xl">
                      <div className={`p-2 rounded-lg ${stepStatus.bgColor} ${stepStatus.color}`}>
                        <StepIcon className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-slate-900 dark:text-white">
                            {step.name}
                          </span>
                          <span className={`text-xs font-medium ${stepStatus.color}`}>
                            {stepStatus.label}
                          </span>
                        </div>
                        {step.duration && step.duration !== '—' && (
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            Duration: {step.duration}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-card p-4 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">Duration</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white">
                  {pipeline.duration || '—'}
                </p>
              </div>
              <div className="glass-card p-4 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">Triggered By</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white">
                  {pipeline.triggeredBy || '—'}
                </p>
              </div>
              <div className="glass-card p-4 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">Commit</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white">
                  {pipeline.commit?.slice(0, 7) || '—'}
                </p>
              </div>
              <div className="glass-card p-4 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">Branch</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white">
                  {pipeline.branch || 'main'}
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {selectedTab === 'logs' && (
          <motion.div
            key="logs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Logs</h3>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setIsLive(!isLive)}
                    className={`px-2 py-1 rounded-lg text-xs transition-colors ${
                      isLive
                        ? 'bg-primary-500 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {isLive ? '🔴 Live' : '⏸ Paused'}
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={fetchLogs}
                  className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <FiRefreshCw className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </button>
                <button
                  onClick={handleCopyLogs}
                  className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <FiCopy className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </button>
                <button
                  onClick={handleDownloadLogs}
                  className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <FiDownload className="w-4 h-4 text-slate-600 dark:text-slate-400" />
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
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Step Details
            </h3>
            {(pipeline.steps || []).map((step, index) => (
              <div key={index} className="glass-card p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getStatusConfig(step.status).bgColor} ${getStatusConfig(step.status).color}`}>
                        {React.createElement(getStatusConfig(step.status).icon, { className: "w-4 h-4" })}
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                        {step.name}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Duration: {step.duration || '—'}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium ${getStatusConfig(step.status).color}`}>
                    {getStatusConfig(step.status).label}
                  </span>
                </div>
                {step.error && (
                  <div className="mt-2 p-2 rounded-lg bg-error/10 text-error text-xs">
                    {step.error}
                  </div>
                )}
              </div>
            ))}
          </motion.div>
        )}

        {selectedTab === 'metrics' && (
          <motion.div
            key="metrics"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {['CPU Usage', 'Memory Usage', 'Build Time', 'Success Rate'].map((metric) => (
              <div key={metric} className="glass-card p-4 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">{metric}</p>
                <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {Math.floor(Math.random() * 100)}%
                </p>
                <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full mt-2 overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${Math.floor(Math.random() * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Mock data
const mockPipelineDetails = {
  id: '1',
  name: 'Frontend Deployment',
  repo: 'org/frontend-app',
  commit: 'abc1234',
  status: 'running',
  progress: 68,
  duration: '2m 34s',
  triggeredBy: 'John Doe',
  branch: 'main',
  steps: [
    { name: 'Build', status: 'completed', duration: '2m 34s' },
    { name: 'Test', status: 'completed', duration: '1m 12s' },
    { name: 'Deploy', status: 'running', duration: '—' },
    { name: 'Monitor', status: 'pending', duration: '—' },
  ],
  createdAt: new Date().toISOString(),
};

const mockLogs = [
  { timestamp: new Date(Date.now() - 60000).toISOString(), level: 'info', message: 'Starting build process...' },
  { timestamp: new Date(Date.now() - 45000).toISOString(), level: 'info', message: 'Installing dependencies...' },
  { timestamp: new Date(Date.now() - 30000).toISOString(), level: 'success', message: 'Dependencies installed successfully' },
  { timestamp: new Date(Date.now() - 15000).toISOString(), level: 'info', message: 'Running tests...' },
  { timestamp: new Date(Date.now() - 5000).toISOString(), level: 'success', message: 'All tests passed (42 tests)' },
  { timestamp: new Date().toISOString(), level: 'info', message: 'Starting deployment...' },
];

export default PipelineDetails;