import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiSearch,
  FiFilter,
  FiDownload,
  FiRefreshCw,
  FiChevronLeft,
  FiChevronRight,
  FiUser,
  FiClock,
  FiActivity,
  FiShield,
  FiServer,
  FiDatabase,
  FiAlertCircle,
  FiCheckCircle,
  FiXCircle,
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const AuditLogItem = ({ log }) => {
  const getActionIcon = (action) => {
    switch (action) {
      case 'login': return FiUser;
      case 'logout': return FiUser;
      case 'create': return FiCheckCircle;
      case 'update': return FiActivity;
      case 'delete': return FiXCircle;
      case 'deploy': return FiServer;
      case 'configure': return FiShield;
      case 'database': return FiDatabase;
      default: return FiActivity;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'login': return 'text-primary-500 bg-primary-500/10';
      case 'logout': return 'text-slate-500 bg-slate-500/10';
      case 'create': return 'text-success-500 bg-success-500/10';
      case 'update': return 'text-warning-500 bg-warning-500/10';
      case 'delete': return 'text-error-500 bg-error-500/10';
      case 'deploy': return 'text-accent-500 bg-accent-500/10';
      case 'configure': return 'text-info-500 bg-info-500/10';
      case 'database': return 'text-indigo-500 bg-indigo-500/10';
      default: return 'text-slate-500 bg-slate-500/10';
    }
  };

  const Icon = getActionIcon(log.action);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
    >
      <div className={`p-2 rounded-lg flex-shrink-0 ${getActionColor(log.action)}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center flex-wrap gap-2">
          <span className="text-sm font-medium text-slate-900 dark:text-white">
            {log.user}
          </span>
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {log.action}
          </span>
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {log.target}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            log.status === 'success' ? 'bg-success-500/10 text-success-500' :
            log.status === 'failed' ? 'bg-error-500/10 text-error-500' :
            'bg-warning-500/10 text-warning-500'
          }`}>
            {log.status}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          <span className="flex items-center gap-1">
            <FiClock className="w-3 h-3" />
            {log.time}
          </span>
          <span>•</span>
          <span>IP: {log.ip}</span>
          {log.details && (
            <>
              <span>•</span>
              <span className="truncate max-w-xs">{log.details}</span>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
};

const AuditLogs = ({ onClose }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 10;

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      setLogs(mockAuditLogs);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.action === filter || log.status === filter;
    const matchesSearch = searchTerm === '' ||
      log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.target.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const currentLogs = filteredLogs.slice(
    (currentPage - 1) * logsPerPage,
    currentPage * logsPerPage
  );

  const handleExport = () => {
    const csv = ['User,Action,Target,Status,Time,IP,Details'];
    logs.forEach(log => {
      csv.push(`${log.user},${log.action},${log.target},${log.status},${log.time},${log.ip},${log.details || ''}`);
    });
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Logs exported');
  };

  const getActionCounts = () => {
    const counts = {};
    logs.forEach(log => {
      counts[log.action] = (counts[log.action] || 0) + 1;
    });
    return counts;
  };

  const actionCounts = getActionCounts();

  if (loading) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-10 w-24 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        </div>
        <div className="space-y-3 mt-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
              <div className="flex-1">
                <div className="h-4 w-48 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div className="h-3 w-32 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <FiShield className="text-primary-500" />
            Audit Logs
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            System activity and security audit trail
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
            title="Export CSV"
          >
            <FiDownload className="w-4 h-4" />
          </button>
          <button
            onClick={fetchLogs}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
            title="Refresh"
          >
            <FiRefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Close
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-2 mb-4">
        <div className="px-3 py-1.5 rounded-lg bg-white/50 dark:bg-slate-800/50 text-sm">
          <span className="text-slate-500 dark:text-slate-400">Total: </span>
          <span className="font-medium text-slate-900 dark:text-white">{logs.length}</span>
        </div>
        {Object.entries(actionCounts).map(([action, count]) => (
          <div key={action} className="px-3 py-1.5 rounded-lg bg-white/50 dark:bg-slate-800/50 text-sm">
            <span className="text-slate-500 dark:text-slate-400 capitalize">{action}: </span>
            <span className="font-medium text-slate-900 dark:text-white">{count}</span>
          </div>
        ))}
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
            onClick={() => setFilter('login')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'login'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setFilter('deploy')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'deploy'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Deploy
          </button>
          <button
            onClick={() => setFilter('configure')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'configure'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Configure
          </button>
          <button
            onClick={() => setFilter('success')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'success'
                ? 'bg-success-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Success
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-2 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === 'failed'
                ? 'bg-error-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            Failed
          </button>
        </div>
        <div className="relative flex-1 sm:flex-none w-full sm:w-auto">
          <FiSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search logs..."
            className="w-full sm:w-48 pl-8 pr-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Log List */}
      <div className="space-y-1 max-h-96 overflow-y-auto scrollbar-thin">
        {currentLogs.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-slate-500 dark:text-slate-400">No logs found</p>
          </div>
        ) : (
          currentLogs.map((log, index) => (
            <AuditLogItem key={index} log={log} />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-200/50 dark:border-slate-700/50">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Showing {(currentPage - 1) * logsPerPage + 1} to {Math.min(currentPage * logsPerPage, filteredLogs.length)} of {filteredLogs.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-slate-500"
            >
              <FiChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-slate-600 dark:text-slate-400 px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-slate-500"
            >
              <FiChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Mock data
const mockAuditLogs = [
  {
    user: 'john.doe@example.com',
    action: 'login',
    target: 'System',
    status: 'success',
    time: '2024-01-15 14:23:45',
    ip: '192.168.1.100',
    details: 'Successful login from Chrome browser',
  },
  {
    user: 'jane.smith@example.com',
    action: 'deploy',
    target: 'frontend-app',
    status: 'success',
    time: '2024-01-15 14:20:12',
    ip: '192.168.1.101',
    details: 'Deployed version 2.3.1 to production',
  },
  {
    user: 'admin@example.com',
    action: 'configure',
    target: 'Security Settings',
    status: 'success',
    time: '2024-01-15 13:55:30',
    ip: '192.168.1.100',
    details: 'Updated MFA settings for all users',
  },
  {
    user: 'john.doe@example.com',
    action: 'update',
    target: 'Pipeline',
    status: 'failed',
    time: '2024-01-15 13:30:15',
    ip: '192.168.1.100',
    details: 'Failed to update pipeline configuration',
  },
  {
    user: 'sarah.wilson@example.com',
    action: 'database',
    target: 'User Table',
    status: 'success',
    time: '2024-01-15 13:10:00',
    ip: '192.168.1.102',
    details: 'Database migration v2.0 completed',
  },
  {
    user: 'jane.smith@example.com',
    action: 'create',
    target: 'New Project',
    status: 'success',
    time: '2024-01-15 12:45:20',
    ip: '192.168.1.101',
    details: 'Created new project: "devops-automation"',
  },
  {
    user: 'admin@example.com',
    action: 'logout',
    target: 'System',
    status: 'success',
    time: '2024-01-15 12:30:00',
    ip: '192.168.1.100',
    details: 'User initiated logout',
  },
  {
    user: 'john.doe@example.com',
    action: 'login',
    target: 'System',
    status: 'failed',
    time: '2024-01-15 12:15:33',
    ip: '192.168.1.105',
    details: 'Failed login attempt - invalid password',
  },
  {
    user: 'sarah.wilson@example.com',
    action: 'deploy',
    target: 'backend-api',
    status: 'success',
    time: '2024-01-15 11:50:10',
    ip: '192.168.1.102',
    details: 'Deployed backend service with blue-green strategy',
  },
  {
    user: 'admin@example.com',
    action: 'configure',
    target: 'RBAC',
    status: 'success',
    time: '2024-01-15 11:30:45',
    ip: '192.168.1.100',
    details: 'Updated role permissions for developer group',
  },
  {
    user: 'jane.smith@example.com',
    action: 'delete',
    target: 'Old Pipeline',
    status: 'success',
    time: '2024-01-15 11:15:20',
    ip: '192.168.1.101',
    details: 'Removed deprecated CI pipeline',
  },
  {
    user: 'john.doe@example.com',
    action: 'update',
    target: 'Config File',
    status: 'success',
    time: '2024-01-15 10:55:00',
    ip: '192.168.1.100',
    details: 'Updated nginx configuration',
  },
];

export default AuditLogs;