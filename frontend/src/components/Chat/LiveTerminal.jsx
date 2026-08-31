import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  FaTerminal, 
  FaCheckCircle, 
  FaTimesCircle, 
  FaExclamationTriangle,
  FaInfoCircle,
  FaCopy,
  FaTrash,
  FaDownload,
  FaPlay,
  FaPause
} from 'react-icons/fa';
import { FiActivity } from 'react-icons/fi';
import toast from 'react-hot-toast';

const LiveTerminal = ({ logs = [], isLive = true, onClear, onExport }) => {
  const [filter, setFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const logEndRef = useRef(null);

  useEffect(() => {
    if (autoScroll && !isPaused) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, isPaused]);

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    return log.level === filter;
  });

  const getLogIcon = (level) => {
    switch (level) {
      case 'success': return <FaCheckCircle className="text-success-500" />;
      case 'error': return <FaTimesCircle className="text-error-500" />;
      case 'warning': return <FaExclamationTriangle className="text-warning-500" />;
      default: return <FaInfoCircle className="text-info-500" />;
    }
  };

  const getLogColor = (level) => {
    switch (level) {
      case 'success': return 'text-success-400';
      case 'error': return 'text-error-400';
      case 'warning': return 'text-warning-400';
      default: return 'text-slate-300';
    }
  };

  const totalLogs = logs.length;
  const errorCount = logs.filter(l => l.level === 'error').length;
  const successCount = logs.filter(l => l.level === 'success').length;

  return (
    <div className="terminal-panel">
      {/* Header */}
      <div className="terminal-header">
        <div className="terminal-header-left">
          <FaTerminal />
          <span className="terminal-header-title">Live Logs</span>
          <span className="terminal-status live">● Live</span>
        </div>
        <div className="terminal-actions">
          <button className="terminal-action-btn" onClick={() => setIsPaused(!isPaused)}>
            {isPaused ? <FaPlay /> : <FaPause />}
          </button>
          <button className="terminal-action-btn" onClick={onExport}>
            <FaDownload />
          </button>
          <button className="terminal-action-btn" onClick={onClear}>
            <FaTrash />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="terminal-stats">
        <span className="terminal-stat">Total: <span className="terminal-stat-value">{totalLogs}</span></span>
        <span className="terminal-stat">✅ <span className="terminal-stat-value success">{successCount}</span></span>
        <span className="terminal-stat">❌ <span className="terminal-stat-value error">{errorCount}</span></span>
        <button 
          className="terminal-filter-btn active"
          onClick={() => setAutoScroll(!autoScroll)}
        >
          {autoScroll ? 'Auto-scroll' : 'Manual'}
        </button>
      </div>

      {/* Filters */}
      <div className="terminal-filters">
        {['all', 'success', 'info', 'warning', 'error'].map((f) => (
          <button
            key={f}
            className={`terminal-filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Logs */}
      <div className="terminal-logs">
        {filteredLogs.length === 0 ? (
          <div className="terminal-empty">
            <FaTerminal />
            <p className="terminal-empty-text">Waiting for logs...</p>
            <p className="terminal-empty-sub">Execute a task to see output</p>
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="terminal-log"
            >
              <span className="terminal-log-time">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <span className="terminal-log-icon">
                {getLogIcon(log.level)}
              </span>
              <span className={`terminal-log-message ${getLogColor(log.level)}`}>
                {log.message}
              </span>
            </motion.div>
          ))
        )}
        <div ref={logEndRef} />
      </div>

      {/* Footer */}
      <div className="terminal-footer">
        <span className="terminal-footer-status">
          <span className="terminal-footer-dot live" />
          {isLive ? 'Listening for events...' : 'Paused'}
        </span>
        <span><FiActivity /> {totalLogs} events</span>
      </div>
    </div>
  );
};

export default LiveTerminal;