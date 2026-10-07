import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FiSearch, FiDownload, FiRefreshCw,
  FiChevronLeft, FiChevronRight,
  FiUser, FiClock, FiActivity, FiShield, FiServer,
  FiDatabase, FiAlertCircle, FiCheckCircle, FiXCircle,
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import axios from 'axios';

const AuditLogItem = ({ log }) => {
  const getIcon = (action) => {
    const a = (action || '').toLowerCase();
    if (a.includes('login')) return FiUser;
    if (a.includes('logout')) return FiUser;
    if (a.includes('deploy')) return FiServer;
    if (a.includes('security')) return FiShield;
    if (a.includes('settings')) return FiDatabase;
    if (a.includes('password')) return FiShield;
    if (a.includes('setup')) return FiCheckCircle;
    if (a.includes('github')) return FiActivity;
    return FiActivity;
  };

  const getColor = (action) => {
    const a = (action || '').toLowerCase();
    if (a.includes('login')) return '#3b82f6';
    if (a.includes('deploy')) return '#a855f7';
    if (a.includes('security')) return '#10b981';
    if (a.includes('password')) return '#f59e0b';
    if (a.includes('setup')) return '#10b981';
    return '#94a3b8';
  };

  const Icon = getIcon(log.action);
  const color = getColor(log.action);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      style={{
        display: 'flex', alignItems: 'flex-start', gap: '12px',
        padding: '10px 12px', borderRadius: '10px',
        background: 'rgba(255,255,255,0.02)', marginBottom: '4px',
      }}
    >
      <div style={{
        padding: '8px', borderRadius: '8px', flexShrink: 0,
        background: `${color}15`,
        color: color,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={14} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>
            {log.action}
          </span>
          {log.target && (
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>
              → {log.target}
            </span>
          )}
          <span style={{
            padding: '2px 8px', borderRadius: '9999px',
            fontSize: '10px', fontWeight: 600,
            background: log.status === 'success' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
            color: log.status === 'success' ? '#10b981' : '#ef4444',
          }}>
            {log.status}
          </span>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '3px',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <FiClock size={10} /> {log.time}
          </span>
          {log.ip && <><span>•</span><span>IP: {log.ip}</span></>}
          {log.details && (
            <>
              <span>•</span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '280px' }}>
                {log.details}
              </span>
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

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const r = await axios.get('/api/auth/audit-logs?limit=100');
      if (r.data.success) setLogs(r.data.logs || []);
      else setLogs([]);
    } catch (e) {
      console.error('Audit logs error:', e);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, []);

  const filteredLogs = logs.filter((log) => {
    const matchesFilter = filter === 'all' || log.status === filter;
    const term = searchTerm.toLowerCase();
    const matchesSearch = !searchTerm ||
      (log.action || '').toLowerCase().includes(term) ||
      (log.target || '').toLowerCase().includes(term) ||
      (log.details || '').toLowerCase().includes(term);
    return matchesFilter && matchesSearch;
  });

  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);
  const currentLogs = filteredLogs.slice(
    (currentPage - 1) * logsPerPage,
    currentPage * logsPerPage
  );

  const handleExport = () => {
    if (!logs.length) return toast.error('No logs');
    const csv = ['Timestamp,Action,Target,Status,IP,Details'];
    logs.forEach((log) => {
      csv.push([
        log.timestamp || log.time,
        log.action || '',
        log.target || '',
        log.status || '',
        log.ip || '',
        (log.details || '').replace(/,/g, ';'),
      ].join(','));
    });
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Exported');
  };

  if (loading) {
    return (
      <div style={{
        padding: '40px', background: 'rgba(30,41,59,0.5)',
        borderRadius: '12px', textAlign: 'center',
        color: 'rgba(255,255,255,0.5)', fontSize: '13px',
      }}>
        <FiRefreshCw style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
        <div>Loading audit logs...</div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '20px', background: 'rgba(30,41,59,0.5)',
      border: '1px solid rgba(148,163,184,0.15)',
      borderRadius: '16px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <FiShield style={{ color: '#a855f7' }} /> Audit Logs
          </h3>
          <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>
            System activity and security audit trail
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleExport} title="Export CSV" style={{
            padding: '8px', background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(148,163,184,0.2)',
            borderRadius: '8px', color: '#fff', cursor: 'pointer',
          }}>
            <FiDownload size={14} />
          </button>
          <button onClick={fetchLogs} title="Refresh" style={{
            padding: '8px', background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(148,163,184,0.2)',
            borderRadius: '8px', color: '#fff', cursor: 'pointer',
          }}>
            <FiRefreshCw size={14} />
          </button>
          {onClose && (
            <button onClick={onClose} style={{
              padding: '8px 14px', background: 'rgba(148,163,184,0.1)',
              border: '1px solid rgba(148,163,184,0.2)',
              borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '12px',
            }}>
              Close
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
        <div style={{
          padding: '6px 12px', borderRadius: '8px',
          background: 'rgba(168,85,247,0.1)',
          fontSize: '12px', color: '#a855f7', fontWeight: 500,
        }}>
          Total: {logs.length}
        </div>
        <div style={{
          padding: '6px 12px', borderRadius: '8px',
          background: 'rgba(16,185,129,0.1)',
          fontSize: '12px', color: '#10b981', fontWeight: 500,
        }}>
          Success: {logs.filter(l => l.status === 'success').length}
        </div>
        <div style={{
          padding: '6px 12px', borderRadius: '8px',
          background: 'rgba(239,68,68,0.1)',
          fontSize: '12px', color: '#ef4444', fontWeight: 500,
        }}>
          Failed: {logs.filter(l => l.status === 'failed').length}
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
        {['all', 'success', 'failed'].map((f) => (
          <button
            key={f}
            onClick={() => { setFilter(f); setCurrentPage(1); }}
            style={{
              padding: '5px 12px', borderRadius: '8px',
              fontSize: '11px', fontWeight: 500,
              background: filter === f ? '#a855f7' : 'rgba(255,255,255,0.05)',
              color: filter === f ? '#fff' : 'rgba(255,255,255,0.6)',
              border: 'none', cursor: 'pointer',
            }}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: '12px' }}>
        <FiSearch style={{
          position: 'absolute', left: '12px', top: '50%',
          transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
        }} size={14} />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
          placeholder="Search logs..."
          style={{
            width: '100%', padding: '10px 12px 10px 36px',
            background: 'rgba(15,23,42,0.6)',
            border: '1px solid rgba(148,163,184,0.2)',
            borderRadius: '10px', color: '#fff',
            fontSize: '12px', outline: 'none',
          }}
        />
      </div>

      {/* Log list */}
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {currentLogs.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '40px 20px',
            color: 'rgba(255,255,255,0.4)', fontSize: '13px',
          }}>
            <FiAlertCircle size={20} style={{ marginBottom: '8px', opacity: 0.5 }} />
            <div>No audit logs yet</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>
              Activity will appear as you use the system
            </div>
          </div>
        ) : (
          currentLogs.map((log, idx) => <AuditLogItem key={log.id || idx} log={log} />)
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', marginTop: '14px',
          paddingTop: '12px', borderTop: '1px solid rgba(148,163,184,0.1)',
          fontSize: '11px', color: 'rgba(255,255,255,0.5)',
        }}>
          <span>
            {(currentPage - 1) * logsPerPage + 1}–{Math.min(currentPage * logsPerPage, filteredLogs.length)} of {filteredLogs.length}
          </span>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '6px', borderRadius: '6px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(148,163,184,0.2)',
                color: '#fff', cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                opacity: currentPage === 1 ? 0.4 : 1,
              }}
            >
              <FiChevronLeft size={12} />
            </button>
            <span style={{ padding: '0 8px', fontSize: '12px', color: '#fff' }}>
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              style={{
                padding: '6px', borderRadius: '6px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(148,163,184,0.2)',
                color: '#fff', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                opacity: currentPage === totalPages ? 0.4 : 1,
              }}
            >
              <FiChevronRight size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;