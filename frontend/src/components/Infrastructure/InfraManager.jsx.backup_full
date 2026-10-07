import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiServer,
  FiCpu,
  FiHardDrive,
  FiActivity,
  FiPlus,
  FiRefreshCw,
  FiChevronDown,
  FiChevronRight,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
  FiSettings,
  FiTrash2,
  FiZap,
  FiBarChart2,
  FiTerminal,
  FiGrid,
  FiList,
} from 'react-icons/fi';
import { FaKubernetes, FaDocker, FaAws, FaGoogle, FaMicrosoft } from 'react-icons/fa';
import { SiTerraform, SiAnsible } from 'react-icons/si';
import toast from 'react-hot-toast';
import ResourceMetrics from './ResourceMetrics';

const ClusterCard = ({ cluster, onSelect, onAction }) => {
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-success bg-success/10';
      case 'warning': return 'text-warning bg-warning/10';
      case 'error': return 'text-error bg-error/10';
      default: return 'text-slate-500 bg-slate-100 dark:bg-slate-700/50';
    }
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'aws': return FaAws;
      case 'gcp': return FaGoogle;
      case 'azure': return FaMicrosoft;
      default: return FiServer;
    }
  };

  const ProviderIcon = getProviderIcon(cluster.provider);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card hover:shadow-xl transition-all"
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20">
              <FaKubernetes className="w-5 h-5 text-primary-500" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                {cluster.name}
                <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(cluster.status)}`}>
                  {cluster.status}
                </span>
              </h4>
              <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                <span className="flex items-center gap-1">
                  <ProviderIcon className="w-3 h-3" />
                  {cluster.provider?.toUpperCase() || 'Unknown'}
                </span>
                <span>•</span>
                <span>{cluster.nodes} nodes</span>
                <span>•</span>
                <span>{cluster.pods} pods</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onAction(cluster.id, 'scale')}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
              title="Scale"
            >
              <FiZap className="w-4 h-4" />
            </button>
            <button
              onClick={() => onAction(cluster.id, 'settings')}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
              title="Settings"
            >
              <FiSettings className="w-4 h-4" />
            </button>
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
            >
              {expanded ? <FiChevronDown className="w-4 h-4" /> : <FiChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Resource Usage */}
        <div className="mt-3 grid grid-cols-3 gap-3">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">CPU</p>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 rounded-full"
                  style={{ width: `${cluster.cpuUsage || 0}%` }}
                />
              </div>
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                {cluster.cpuUsage || 0}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Memory</p>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-500 rounded-full"
                  style={{ width: `${cluster.memoryUsage || 0}%` }}
                />
              </div>
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                {cluster.memoryUsage || 0}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Disk</p>
            <div className="flex items-center gap-2 mt-0.5">
              <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-success-500 rounded-full"
                  style={{ width: `${cluster.diskUsage || 0}%` }}
                />
              </div>
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                {cluster.diskUsage || 0}%
              </span>
            </div>
          </div>
        </div>

        {/* Expanded Details */}
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-slate-200/50 dark:border-slate-700/50"
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400">Uptime</p>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {cluster.uptime || '99.9%'}
                </p>
              </div>
              <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400">Version</p>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {cluster.version || 'v1.28'}
                </p>
              </div>
              <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400">Region</p>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {cluster.region || 'us-west-2'}
                </p>
              </div>
              <div className="text-center p-2 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-xs text-slate-500 dark:text-slate-400">Cost</p>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {cluster.cost || '$0.00'}
                </p>
              </div>
            </div>

            {/* Pods List */}
            <div className="mt-3">
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Running Pods</p>
              <div className="flex flex-wrap gap-1.5">
                {(cluster.podsList || ['frontend-7d5f6b8c9-abcde', 'backend-6f8d9e7a5-bcdef', 'database-9e7f8d6c5-ghijk']).map((pod, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-400"
                  >
                    {pod}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

const InfraManager = () => {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchClusters();
    const interval = setInterval(fetchClusters, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchClusters = async () => {
    try {
      setLoading(true);
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setClusters(mockClusters);
    } catch (error) {
      console.error('Error fetching clusters:', error);
      toast.error('Failed to load clusters');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = (clusterId, action) => {
    toast.info(`${action} action on cluster ${clusterId}`);
  };

  const handleCreateCluster = () => {
    setShowCreateModal(true);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-10 w-32 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass-card p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
                <div className="flex-1">
                  <div className="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  <div className="h-3 w-48 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
                </div>
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
            <FiServer className="text-primary-500" />
            Infrastructure Manager
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage your Kubernetes clusters and cloud resources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 p-1 rounded-xl bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-all ${
                viewMode === 'grid'
                  ? 'bg-primary-500 text-white'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <FiGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-all ${
                viewMode === 'list'
                  ? 'bg-primary-500 text-white'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <FiList className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={fetchClusters}
            className="p-2 rounded-xl bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all"
          >
            <FiRefreshCw className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            onClick={handleCreateCluster}
            className="px-4 py-2 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
          >
            <FiPlus className="w-4 h-4" />
            New Cluster
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">Total Clusters</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">{clusters.length}</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">Total Nodes</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {clusters.reduce((acc, c) => acc + (c.nodes || 0), 0)}
          </p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">Total Pods</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            {clusters.reduce((acc, c) => acc + (c.pods || 0), 0)}
          </p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">Health</p>
          <p className="text-2xl font-bold text-success-500">
            {Math.round(clusters.filter(c => c.status === 'healthy').length / clusters.length * 100)}%
          </p>
        </div>
      </div>

      {/* Cluster List */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' : 'space-y-3'}>
        {clusters.map((cluster) => (
          <ClusterCard
            key={cluster.id}
            cluster={cluster}
            onSelect={setSelectedCluster}
            onAction={handleAction}
          />
        ))}
      </div>

      {/* Resource Metrics */}
      <ResourceMetrics clusters={clusters} />
    </div>
  );
};

// Mock Data
const mockClusters = [
  {
    id: '1',
    name: 'Production Cluster',
    provider: 'aws',
    status: 'healthy',
    nodes: 12,
    pods: 45,
    cpuUsage: 68,
    memoryUsage: 72,
    diskUsage: 45,
    uptime: '99.97%',
    version: 'v1.28.0',
    region: 'us-west-2',
    cost: '$2,340.00',
    podsList: ['frontend-7d5f6b8c9-abcde', 'backend-6f8d9e7a5-bcdef', 'database-9e7f8d6c5-ghijk'],
  },
  {
    id: '2',
    name: 'Staging Cluster',
    provider: 'gcp',
    status: 'healthy',
    nodes: 6,
    pods: 20,
    cpuUsage: 45,
    memoryUsage: 55,
    diskUsage: 30,
    uptime: '99.5%',
    version: 'v1.27.0',
    region: 'us-central1',
    cost: '$890.00',
    podsList: ['frontend-2a3b4c5d6e-xyz', 'backend-7f8g9h0i1j-klmn'],
  },
  {
    id: '3',
    name: 'Development Cluster',
    provider: 'azure',
    status: 'warning',
    nodes: 3,
    pods: 8,
    cpuUsage: 85,
    memoryUsage: 88,
    diskUsage: 72,
    uptime: '98.2%',
    version: 'v1.26.0',
    region: 'east-us',
    cost: '$450.00',
    podsList: ['frontend-3c4d5e6f7g-hij'],
  },
  {
    id: '4',
    name: 'Backup Cluster',
    provider: 'aws',
    status: 'error',
    nodes: 2,
    pods: 4,
    cpuUsage: 92,
    memoryUsage: 95,
    diskUsage: 88,
    uptime: '95.1%',
    version: 'v1.25.0',
    region: 'eu-west-1',
    cost: '$230.00',
    podsList: ['backup-node-1', 'backup-node-2'],
  },
];

export default InfraManager;