import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiDownload,
  FiTrash2,
  FiZap,
  FiRefreshCw,
  FiBarChart2,
  FiChevronDown,
  FiChevronUp,
  FiStar,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';

const ModelVersionCard = ({ model, isCurrent, onDeploy, onDelete, onToggleFavorite }) => {
  const [expanded, setExpanded] = useState(false);

  const getStatusConfig = (status) => {
    switch (status) {
      case 'active':
        return { color: 'text-success-500', bgColor: 'bg-success-500/10', label: 'Active' };
      case 'deprecated':
        return { color: 'text-warning-500', bgColor: 'bg-warning-500/10', label: 'Deprecated' };
      case 'archived':
        return { color: 'text-slate-500', bgColor: 'bg-slate-500/10', label: 'Archived' };
      default:
        return { color: 'text-slate-500', bgColor: 'bg-slate-500/10', label: 'Unknown' };
    }
  };

  const config = getStatusConfig(model.status);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`glass-card p-4 ${isCurrent ? 'border-2 border-primary-500' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20">
            <FaRobot className="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                {model.name}
              </h4>
              <span className={`text-xs px-2 py-0.5 rounded-full ${config.bgColor} ${config.color}`}>
                {config.label}
              </span>
              {isCurrent && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500 text-white">
                  Current
                </span>
              )}
              {/* Fixed: Using FiStar with conditional styling instead of FiStarOff */}
              <button
                onClick={() => onToggleFavorite(model.id)}
                className="p-0.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <FiStar className={`w-4 h-4 ${model.favorite ? 'text-warning-500 fill-warning-500' : 'text-slate-400'}`} />
              </button>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              <span>v{model.version}</span>
              <span>•</span>
              <span>Created: {model.createdAt}</span>
              <span>•</span>
              <span>Size: {model.size}</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400"
        >
          {expanded ? <FiChevronUp className="w-4 h-4" /> : <FiChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 mt-3">
        <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-500 dark:text-slate-400">Accuracy</p>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
        <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-500 dark:text-slate-400">F1 Score</p>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {model.f1 ? model.f1.toFixed(3) : '—'}
          </p>
        </div>
        <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-500 dark:text-slate-400">Parameters</p>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {model.parameters || '—'}
          </p>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-3 pt-3 border-t border-slate-200/50 dark:border-slate-700/50"
        >
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <span className="font-medium text-slate-700 dark:text-slate-300">Description:</span>
              {model.description || 'No description available'}
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <span className="font-medium text-slate-700 dark:text-slate-300">Framework:</span>
              {model.framework || 'Unknown'}
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <span className="font-medium text-slate-700 dark:text-slate-300">Training Data:</span>
              {model.trainingData || 'Not specified'}
            </div>
            {model.notes && (
              <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 text-xs">
                📝 {model.notes}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-200/50 dark:border-slate-700/50">
        {!isCurrent && model.status === 'active' && (
          <button
            onClick={() => onDeploy(model.id)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary-500 text-white text-xs font-medium hover:bg-primary-600 transition-colors"
          >
            <FiZap className="w-3 h-3" />
            Deploy
          </button>
        )}
        <button
          onClick={() => toast.info('Downloading model...')}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <FiDownload className="w-3 h-3" />
          Download
        </button>
        <button
          onClick={() => toast.info('Viewing metrics...')}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <FiBarChart2 className="w-3 h-3" />
          Metrics
        </button>
        {model.status !== 'active' && (
          <button
            onClick={() => onDelete(model.id)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-error-500/10 text-error-500 text-xs font-medium hover:bg-error-500/20 transition-colors"
          >
            <FiTrash2 className="w-3 h-3" />
            Delete
          </button>
        )}
      </div>
    </motion.div>
  );
};

const ModelVersions = ({ onClose }) => {
  const [models, setModels] = useState(mockModels);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const handleDeploy = (id) => {
    setModels(models.map(m => ({
      ...m,
      status: m.id === id ? 'active' : m.status === 'active' ? 'deprecated' : m.status,
    })));
    toast.success('Model deployed successfully!');
  };

  const handleDelete = (id) => {
    if (!window.confirm('Are you sure you want to delete this model?')) return;
    setModels(models.filter(m => m.id !== id));
    toast.success('Model deleted');
  };

  const handleToggleFavorite = (id) => {
    setModels(models.map(m => 
      m.id === id ? { ...m, favorite: !m.favorite } : m
    ));
    toast.success('Favorite toggled');
  };

  const filteredModels = models.filter(model => {
    const matchesFilter = filter === 'all' || model.status === filter;
    const matchesSearch = searchTerm === '' ||
      model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      model.version.includes(searchTerm);
    return matchesFilter && matchesSearch;
  });

  const currentModel = models.find(m => m.status === 'active');

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FiBarChart2 className="text-primary-500" />
            Model Versions
            {currentModel && (
              <span className="px-2 py-0.5 rounded-full bg-primary-500 text-white text-xs">
                Current: {currentModel.name}
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Manage your trained models and versions
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
        >
          Close
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'all'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('active')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'active'
                ? 'bg-success-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilter('deprecated')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'deprecated'
                ? 'bg-warning-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Deprecated
          </button>
          <button
            onClick={() => setFilter('archived')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'archived'
                ? 'bg-slate-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Archived
          </button>
        </div>
        <div className="relative flex-1 sm:flex-none w-full sm:w-auto">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search models..."
            className="w-full sm:w-48 px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
        </div>
        <button
          onClick={() => toast.info('Refreshing...')}
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <FiRefreshCw className="w-4 h-4 text-slate-600 dark:text-slate-400" />
        </button>
      </div>

      {/* Model List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin">
        {filteredModels.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto">
              <FaRobot className="w-6 h-6 text-slate-400" />
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">No models found</p>
          </div>
        ) : (
          filteredModels.map((model) => (
            <ModelVersionCard
              key={model.id}
              model={model}
              isCurrent={model.status === 'active'}
              onDeploy={handleDeploy}
              onDelete={handleDelete}
              onToggleFavorite={handleToggleFavorite}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-200/50 dark:border-slate-700/50 text-xs text-slate-500 dark:text-slate-400">
        <span>{filteredModels.length} models</span>
        <span>Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

// Mock data
const mockModels = [
  {
    id: '1',
    name: 'DevOps Assistant v2',
    version: '2.3.1',
    status: 'active',
    accuracy: 0.947,
    f1: 0.945,
    parameters: '1.2M',
    size: '234 MB',
    createdAt: '2024-01-15',
    framework: 'PyTorch',
    trainingData: 'DevOps logs (10k samples)',
    description: 'Main DevOps assistant model with improved reasoning',
    favorite: true,
    notes: 'Trained on latest DevOps logs. Improved error detection.',
  },
  {
    id: '2',
    name: 'DevOps Assistant v1',
    version: '2.3.0',
    status: 'deprecated',
    accuracy: 0.932,
    f1: 0.928,
    parameters: '1.1M',
    size: '210 MB',
    createdAt: '2024-01-12',
    framework: 'PyTorch',
    trainingData: 'DevOps logs (8k samples)',
    description: 'Previous version with good performance',
    favorite: false,
    notes: 'Replaced by v2.3.1',
  },
  {
    id: '3',
    name: 'DevOps Assistant v1.9',
    version: '1.9.0',
    status: 'archived',
    accuracy: 0.878,
    f1: 0.872,
    parameters: '980K',
    size: '180 MB',
    createdAt: '2024-01-08',
    framework: 'TensorFlow',
    trainingData: 'DevOps logs (5k samples)',
    description: 'Legacy model',
    favorite: false,
  },
  {
    id: '4',
    name: 'Security Scanner Model',
    version: '1.0.0',
    status: 'active',
    accuracy: 0.965,
    f1: 0.962,
    parameters: '890K',
    size: '160 MB',
    createdAt: '2024-01-14',
    framework: 'Transformers',
    trainingData: 'Security logs (3k samples)',
    description: 'Specialized model for security vulnerability scanning',
    favorite: true,
    notes: 'High accuracy for code vulnerability detection',
  },
  {
    id: '5',
    name: 'Log Analyzer Model',
    version: '1.2.0',
    status: 'active',
    accuracy: 0.978,
    f1: 0.972,
    parameters: '1.5M',
    size: '280 MB',
    createdAt: '2024-01-13',
    framework: 'PyTorch',
    trainingData: 'System logs (15k samples)',
    description: 'Advanced log analysis and error detection',
    favorite: true,
  },
];

export default ModelVersions;