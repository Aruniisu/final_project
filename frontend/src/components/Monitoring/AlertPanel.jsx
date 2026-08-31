import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiAlertCircle,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiFilter,
  FiSearch,
  FiBellOff,
  FiBell,
  FiRefreshCw,
  FiTrash2,
  FiChevronDown,
  FiChevronUp,
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const AlertItem = ({ alert, onAcknowledge, onResolve, onDismiss }) => {
  const [expanded, setExpanded] = useState(false);

  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'critical':
        return { color: 'text-error-500', bgColor: 'bg-error-500/10', borderColor: 'border-error-500/20', label: 'Critical' };
      case 'high':
        return { color: 'text-warning-500', bgColor: 'bg-warning-500/10', borderColor: 'border-warning-500/20', label: 'High' };
      case 'medium':
        return { color: 'text-info-500', bgColor: 'bg-info-500/10', borderColor: 'border-info-500/20', label: 'Medium' };
      case 'low':
        return { color: 'text-slate-500', bgColor: 'bg-slate-500/10', borderColor: 'border-slate-500/20', label: 'Low' };
      default:
        return { color: 'text-slate-500', bgColor: 'bg-slate-500/10', borderColor: 'border-slate-500/20', label: 'Unknown' };
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'acknowledged':
        return <FiBellOff className="w-4 h-4" />;
      case 'resolved':
        return <FiCheckCircle className="w-4 h-4" />;
      case 'dismissed':
        return <FiXCircle className="w-4 h-4" />;
      default:
        return <FiBell className="w-4 h-4 animate-pulse" />;
    }
  };

  const config = getSeverityConfig(alert.severity);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`glass-card border-l-4 ${config.borderColor} p-4`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor} ${config.color} mt-0.5`}>
            <FiAlertCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                {alert.title}
              </h4>
              <span className={`text-xs px-2 py-0.5 rounded-full ${config.bgColor} ${config.color}`}>
                {config.label}
              </span>
              <span className="text-xs text-slate-400">{alert.status}</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {alert.message}
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
              <span className="flex items-center gap-0.5">
                <FiClock className="w-3 h-3" />
                {alert.time}
              </span>
              <span>•</span>
              <span>Source: {alert.source}</span>
              {alert.count > 1 && (
                <>
                  <span>•</span>
                  <span>Occurred {alert.count} times</span>
                </>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400"
        >
          {expanded ? <FiChevronUp className="w-4 h-4" /> : <FiChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3">
        {alert.status === 'active' && (
          <>
            <button
              onClick={() => onAcknowledge(alert.id)}
              className="px-3 py-1 text-xs bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              Acknowledge
            </button>
            <button
              onClick={() => onResolve(alert.id)}
              className="px-3 py-1 text-xs bg-success-500 text-white rounded-lg hover:bg-success-600 transition-colors"
            >
              Resolve
            </button>
          </>
        )}
        {alert.status === 'acknowledged' && (
          <button
            onClick={() => onResolve(alert.id)}
            className="px-3 py-1 text-xs bg-success-500 text-white rounded-lg hover:bg-success-600 transition-colors"
          >
            Resolve
          </button>
        )}
        <button
          onClick={() => onDismiss(alert.id)}
          className="px-3 py-1 text-xs bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
        >
          Dismiss
        </button>
        <button
          onClick={() => toast.info('Viewing details...')}
          className="px-3 py-1 text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          View Details
        </button>
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
              <span className="font-medium text-slate-700 dark:text-slate-300">Details:</span>
              {alert.details || 'No additional details available'}
            </div>
            {alert.affectedServices && (
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                <span className="font-medium text-slate-700 dark:text-slate-300">Affected:</span>
                {alert.affectedServices.join(', ')}
              </div>
            )}
            {alert.recommendation && (
              <div className="p-2 rounded-lg bg-primary-500/10 text-primary-600 dark:text-primary-400 text-xs">
                💡 {alert.recommendation}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const AlertPanel = ({ onClose }) => {
  const [alerts, setAlerts] = useState(mockAlerts);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const handleAcknowledge = (id) => {
    setAlerts(alerts.map(a => 
      a.id === id ? { ...a, status: 'acknowledged' } : a
    ));
    toast.success('Alert acknowledged');
  };

  const handleResolve = (id) => {
    setAlerts(alerts.map(a => 
      a.id === id ? { ...a, status: 'resolved' } : a
    ));
    toast.success('Alert resolved');
  };

  const handleDismiss = (id) => {
    setAlerts(alerts.filter(a => a.id !== id));
    toast.success('Alert dismissed');
  };

  const filteredAlerts = alerts.filter(alert => {
    const matchesFilter = filter === 'all' || alert.severity === filter || alert.status === filter;
    const matchesSearch = searchTerm === '' ||
      alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.message.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const activeCount = alerts.filter(a => a.status === 'active').length;

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FiBell className="text-primary-500" />
            Alerts
            {activeCount > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-error text-white text-xs">
                {activeCount} active
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time alerts from your infrastructure
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onClose}
            className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Close
          </button>
        </div>
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
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilter('critical')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'critical'
                ? 'bg-error-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Critical
          </button>
          <button
            onClick={() => setFilter('high')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'high'
                ? 'bg-warning-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            High
          </button>
        </div>
        <div className="relative flex-1 sm:flex-none w-full sm:w-auto">
          <FiSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search alerts..."
            className="w-full sm:w-48 pl-8 pr-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto">
              <FiBellOff className="w-6 h-6 text-slate-400" />
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">No alerts found</p>
            <p className="text-xs text-slate-400 dark:text-slate-500">All clear! 🎉</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertItem
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              onDismiss={handleDismiss}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-200/50 dark:border-slate-700/50 text-xs text-slate-500 dark:text-slate-400">
        <span>{filteredAlerts.length} alerts</span>
        <button className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-300">
          <FiRefreshCw className="w-3 h-3" />
          Refresh
        </button>
      </div>
    </div>
  );
};

// Mock data
const mockAlerts = [
  {
    id: '1',
    title: 'High CPU Usage Detected',
    message: 'CPU usage exceeded 85% threshold on Production Cluster',
    severity: 'critical',
    status: 'active',
    time: '2 minutes ago',
    source: 'Production Cluster',
    count: 3,
    affectedServices: ['frontend', 'api-gateway'],
    recommendation: 'Scale up the cluster or optimize resource usage',
    details: 'Current CPU: 92% | Threshold: 85% | Duration: 5m',
  },
  {
    id: '2',
    title: 'Database Connection Timeout',
    message: 'Multiple connection timeouts detected from API service',
    severity: 'high',
    status: 'acknowledged',
    time: '15 minutes ago',
    source: 'PostgreSQL',
    count: 1,
    affectedServices: ['api-service', 'auth-service'],
    recommendation: 'Check database connectivity and connection pool size',
  },
  {
    id: '3',
    title: 'Memory Usage Warning',
    message: 'Memory usage approaching 80% on Staging Cluster',
    severity: 'medium',
    status: 'active',
    time: '45 minutes ago',
    source: 'Staging Cluster',
    count: 2,
    affectedServices: ['backend', 'worker'],
  },
  {
    id: '4',
    title: 'SSL Certificate Expiring',
    message: 'SSL certificate for example.com expires in 5 days',
    severity: 'low',
    status: 'active',
    time: '1 hour ago',
    source: 'Certificate Manager',
    count: 1,
    recommendation: 'Renew SSL certificate before expiration date',
  },
];

export default AlertPanel;