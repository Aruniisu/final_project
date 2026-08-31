import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import '../../styles/main.css';
import './PipelineDashboard.css';
import {
  FiGitBranch,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiRefreshCw,
  FiPlay,
  FiPause,
  FiStopCircle,
  FiSearch,
  FiFilter,
  FiPlus,
  FiAlertCircle,
  FiActivity,
  FiZap,
} from 'react-icons/fi';
import { FaGithub } from 'react-icons/fa';
import toast from 'react-hot-toast';
import { pipelineAPI } from '../../api/assistant';

const PipelineCard = ({ pipeline, onTrigger, onRetry, onCancel }) => {
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

  const statusConfig = getStatusConfig(pipeline.status);
  const StatusIcon = statusConfig.icon;

  const steps = pipeline.steps || [
    { name: 'Build', status: 'completed', duration: '2m 34s' },
    { name: 'Test', status: 'completed', duration: '1m 12s' },
    { name: 'Deploy', status: 'running', duration: '—' },
    { name: 'Monitor', status: 'pending', duration: '—' },
  ];

  const getStepStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-success-500';
      case 'running': return 'bg-primary-500 animate-pulse';
      case 'failed': return 'bg-error-500';
      case 'pending': return 'bg-slate-300 dark:bg-slate-600';
      default: return 'bg-slate-300 dark:bg-slate-600';
    }
  };

  const getStepStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <FiCheckCircle className="w-3 h-3 text-success-500" />;
      case 'running': return <FiActivity className="w-3 h-3 text-primary-500 animate-spin" />;
      case 'failed': return <FiXCircle className="w-3 h-3 text-error-500" />;
      default: return <FiClock className="w-3 h-3 text-slate-400" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className="glass-card p-4 hover:shadow-xl transition-all"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl ${statusConfig.bgColor} ${statusConfig.color}`}>
            <StatusIcon className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
              {pipeline.name || 'Pipeline'}
            </h4>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <FaGithub className="w-3 h-3" />
              <span>{pipeline.repo || 'repo/main'}</span>
              <span>•</span>
              <span>{pipeline.commit || 'abc1234'}</span>
              <span>•</span>
              <span>{pipeline.duration || '2m 34s'}</span>
            </div>
          </div>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
          {statusConfig.icon && <statusConfig.icon className="w-3 h-3" />}
          <span>{statusConfig.label}</span>
        </div>
      </div>

      {/* Steps */}
      <div className="mt-4 flex items-center gap-2">
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${getStepStatusColor(step.status)}`} />
              <span className="text-xs text-slate-600 dark:text-slate-400">{step.name}</span>
              {step.duration && step.duration !== '—' && (
                <span className="text-xs text-slate-400">{step.duration}</span>
              )}
            </div>
            {index < steps.length - 1 && (
              <div className="w-4 h-px bg-slate-300 dark:bg-slate-600" />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Progress */}
      <div className="mt-3 flex items-center gap-3">
        <div className="flex-1">
          <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                pipeline.status === 'success' ? 'bg-success-500' :
                pipeline.status === 'failed' ? 'bg-error-500' :
                pipeline.status === 'running' ? 'bg-primary-500' :
                'bg-slate-400'
              }`}
              style={{ width: `${pipeline.progress || 0}%` }}
            />
          </div>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {pipeline.progress || 0}%
        </span>
      </div>

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2 border-t border-slate-200/50 dark:border-slate-700/50 pt-3">
        {pipeline.status === 'pending' || pipeline.status === 'failed' ? (
          <button
            onClick={() => onTrigger(pipeline.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-500 text-white text-xs font-medium hover:bg-primary-600 transition-colors"
          >
            <FiPlay className="w-3 h-3" />
            Trigger
          </button>
        ) : pipeline.status === 'running' ? (
          <button
            onClick={() => onCancel(pipeline.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-error-500 text-white text-xs font-medium hover:bg-error-600 transition-colors"
          >
            <FiStopCircle className="w-3 h-3" />
            Cancel
          </button>
        ) : pipeline.status === 'success' ? (
          <button
            onClick={() => onRetry(pipeline.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-500 text-white text-xs font-medium hover:bg-primary-600 transition-colors"
          >
            <FiRefreshCw className="w-3 h-3" />
            Retry
          </button>
        ) : null}
        <button
          onClick={() => onTrigger(pipeline.id)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <FiActivity className="w-3 h-3" />
          Logs
        </button>
      </div>
    </motion.div>
  );
};

const PipelineDashboard = () => {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPipelines();
    const interval = setInterval(fetchPipelines, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchPipelines = async () => {
    try {
      setLoading(true);
      const response = await pipelineAPI.getAll();
      setPipelines(response || mockPipelines);
    } catch (error) {
      console.error('Error fetching pipelines:', error);
      // Use mock data for demo
      setPipelines(mockPipelines);
    } finally {
      setLoading(false);
    }
  };

  const handleTrigger = async (pipelineId) => {
    try {
      toast.loading('Triggering pipeline...');
      await pipelineAPI.trigger(pipelineId);
      toast.success('Pipeline triggered successfully');
      fetchPipelines();
    } catch (error) {
      toast.error('Failed to trigger pipeline');
    }
  };

  const handleRetry = async (pipelineId) => {
    try {
      toast.loading('Retrying pipeline...');
      await pipelineAPI.retry(pipelineId);
      toast.success('Pipeline retry started');
      fetchPipelines();
    } catch (error) {
      toast.error('Failed to retry pipeline');
    }
  };

  const handleCancel = async (pipelineId) => {
    try {
      toast.loading('Cancelling pipeline...');
      await pipelineAPI.cancel(pipelineId);
      toast.success('Pipeline cancelled');
      fetchPipelines();
    } catch (error) {
      toast.error('Failed to cancel pipeline');
    }
  };

  const handleViewDetails = (pipelineId) => {
    navigate(`/pipelines/${pipelineId}`);
  };

  const filteredPipelines = pipelines.filter(pipeline => {
    const matchesFilter = filter === 'all' || pipeline.status === filter;
    const matchesSearch = searchTerm === '' ||
      pipeline.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pipeline.repo?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusCounts = () => {
    const counts = { all: pipelines.length };
    pipelines.forEach(p => {
      counts[p.status] = (counts[p.status] || 0) + 1;
    });
    return counts;
  };

  const statusCounts = getStatusCounts();

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-10 w-32 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="glass-card p-4 animate-pulse">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
                <div className="flex-1">
                  <div className="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  <div className="h-3 w-48 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
                </div>
                <div className="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FiGitBranch className="text-primary-500" />
            CI/CD Pipelines
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage and monitor your CI/CD pipelines
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchPipelines}
            className="p-2 rounded-xl bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all"
          >
            <FiRefreshCw className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            className="px-4 py-2 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
          >
            <FiPlus className="w-4 h-4" />
            New Pipeline
          </button>
        </div>
      </div>

      {/* Status Summary */}
      <div className="flex flex-wrap gap-3">
        {['all', 'running', 'success', 'failed', 'pending', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              filter === status
                ? 'bg-primary-500 text-white'
                : 'bg-white/50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            {statusCounts[status] > 0 && (
              <span className={`ml-1 ${filter === status ? 'text-white/70' : 'text-slate-400'}`}>
                ({statusCounts[status]})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search pipelines..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Pipeline List */}
      <div className="grid grid-cols-1 gap-4">
        <AnimatePresence>
          {filteredPipelines.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto">
                <FiGitBranch className="w-8 h-8 text-slate-400" />
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                No pipelines found
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500">
                Create a new pipeline or check your filters
              </p>
            </div>
          ) : (
            filteredPipelines.map((pipeline) => (
              <PipelineCard
                key={pipeline.id}
                pipeline={pipeline}
                onTrigger={handleTrigger}
                onRetry={handleRetry}
                onCancel={handleCancel}
                onViewDetails={handleViewDetails}
              />
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-200 dark:border-slate-700">
        <span>{filteredPipelines.length} of {pipelines.length} pipelines</span>
        <span>Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

// Mock data for demo
const mockPipelines = [
  {
    id: '1',
    name: 'Frontend Deployment',
    repo: 'org/frontend-app',
    commit: 'abc1234',
    status: 'running',
    progress: 68,
    duration: '2m 34s',
    steps: [
      { name: 'Build', status: 'completed', duration: '2m 34s' },
      { name: 'Test', status: 'completed', duration: '1m 12s' },
      { name: 'Deploy', status: 'running', duration: '—' },
      { name: 'Monitor', status: 'pending', duration: '—' },
    ],
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    name: 'Backend API Pipeline',
    repo: 'org/backend-api',
    commit: 'def5678',
    status: 'success',
    progress: 100,
    duration: '5m 12s',
    steps: [
      { name: 'Build', status: 'completed', duration: '1m 45s' },
      { name: 'Test', status: 'completed', duration: '2m 30s' },
      { name: 'Deploy', status: 'completed', duration: '45s' },
      { name: 'Monitor', status: 'completed', duration: '12s' },
    ],
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    name: 'Mobile App Build',
    repo: 'org/mobile-app',
    commit: 'ghi9012',
    status: 'failed',
    progress: 45,
    duration: '3m 20s',
    steps: [
      { name: 'Build', status: 'completed', duration: '2m 10s' },
      { name: 'Test', status: 'failed', duration: '1m 10s' },
      { name: 'Deploy', status: 'pending', duration: '—' },
      { name: 'Monitor', status: 'pending', duration: '—' },
    ],
    createdAt: new Date().toISOString(),
  },
  {
    id: '4',
    name: 'Database Migration',
    repo: 'org/database',
    commit: 'jkl3456',
    status: 'pending',
    progress: 0,
    duration: '—',
    steps: [
      { name: 'Build', status: 'pending', duration: '—' },
      { name: 'Test', status: 'pending', duration: '—' },
      { name: 'Deploy', status: 'pending', duration: '—' },
      { name: 'Monitor', status: 'pending', duration: '—' },
    ],
    createdAt: new Date().toISOString(),
  },
];

export default PipelineDashboard;