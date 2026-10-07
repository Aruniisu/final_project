import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import io from 'socket.io-client';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { actionAPI } from '../../api/assistant';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import { useAuth } from '../../context/AuthContext';
import './AssistantChat.css';
import { APP_VERSION } from '../../config/version';

import {
  FaRobot, FaPaperPlane, FaMicrophone, FaStop, FaSpinner,
  FaCheckCircle, FaTimesCircle, FaCopy, FaDownload,
  FaCode, FaFolderOpen, FaRocket, FaBug, FaShieldAlt,
  FaCloud, FaTrash, FaClock, FaTerminal, FaGithub,
  FaExternalLinkAlt, FaGlobe, FaServer, FaPlay, FaPause,
  FaGitAlt, FaLayerGroup, FaPlus, FaMagic
} from 'react-icons/fa';
import { FiZap, FiActivity } from 'react-icons/fi';
import { BsLightningCharge } from 'react-icons/bs';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5000';
const PROJECTS_STORAGE_KEY = 'smartdevops.projects.v1';

const downloadFile = (content, filename, type = 'text/plain') => {
  try {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded: ${filename}`);
  } catch {
    toast.error('Download failed');
  }
};

// ═══════════════════════════════════════════════════════════
// localStorage helpers
// ═══════════════════════════════════════════════════════════
const loadProjectsFromStorage = () => {
  try {
    const raw = localStorage.getItem(PROJECTS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch (e) {
    console.warn('Failed to load projects:', e);
    return [];
  }
};

const saveProjectsToStorage = (projects) => {
  try {
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  } catch (e) {
    console.warn('Failed to save projects:', e);
  }
};

const Message = ({ message, content, isUser, timestamp, execution }) => {
  const [copied, setCopied] = useState(false);
  const text = (message ?? content ?? '').toString();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Copy failed');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`message ${isUser ? 'user' : 'assistant'}`}
    >
      <div className="message-wrapper">
        <div className="avatar">{isUser ? <span>U</span> : <FaRobot />}</div>
        <div className="bubble">
          <div className="text">
            {text ? (
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    if (!inline && match) {
                      const codeString = String(children).replace(/\n$/, '');
                      const extMap = {
                        javascript: 'js', js: 'js', jsx: 'jsx',
                        typescript: 'ts', ts: 'ts', tsx: 'tsx',
                        python: 'py', py: 'py',
                        java: 'java', go: 'go', rust: 'rs',
                        yaml: 'yaml', yml: 'yml',
                        json: 'json', html: 'html', css: 'css',
                        bash: 'sh', sh: 'sh', shell: 'sh',
                      };
                      const ext = extMap[match[1].toLowerCase()] || 'txt';
                      return (
                        <div className="code-block">
                          <div className="code-header">
                            <span><FaCode /> {match[1]}</span>
                            <button onClick={() => downloadFile(codeString, `code.${ext}`)}>
                              <FaDownload /> Download
                            </button>
                          </div>
                          <SyntaxHighlighter style={atomDark} language={match[1]} PreTag="div">
                            {codeString}
                          </SyntaxHighlighter>
                        </div>
                      );
                    }
                    return <code className="inline-code">{children}</code>;
                  },
                }}
              >
                {text}
              </ReactMarkdown>
            ) : (
              <p style={{ opacity: 0.4, fontStyle: 'italic' }}>(empty)</p>
            )}
          </div>

          {execution && (
            <div className="execution-box">
              <div className="execution-top">
                <span className={`status ${execution.status}`}>
                  {execution.status === 'running' && <FaSpinner className="spin" />}
                  {execution.status === 'completed' && <FaCheckCircle />}
                  {execution.status === 'failed' && <FaTimesCircle />}
                  {execution.status || 'Pending'}
                </span>
                <span className="progress-text">{execution.progress || 0}%</span>
                <span className="duration-text"><FaClock /> {execution.duration || '0s'}</span>
              </div>
              <div className="progress-track">
                <div className={`progress-fill ${execution.status}`}
                  style={{ width: `${execution.progress || 0}%` }} />
              </div>
              {execution.liveUrl && (
                <div className="live-url">
                  <FaRocket />
                  <a href={execution.liveUrl} target="_blank" rel="noopener noreferrer">
                    {execution.liveUrl} <FaExternalLinkAlt />
                  </a>
                </div>
              )}
              {execution.steps?.map((s, i) => (
                <div key={i} className={`step ${s.status}`}>
                  {s.status === 'completed' && <FaCheckCircle />}
                  {s.status === 'running' && <FaSpinner className="spin" />}
                  {s.status === 'failed' && <FaTimesCircle />}
                  {s.status === 'fixed' && <FaMagic />}
                  <span>{s.name}</span>
                  {s.duration && <span className="step-time">{s.duration}</span>}
                </div>
              ))}
            </div>
          )}

          <div className="actions">
            <button onClick={handleCopy}>{copied ? '✓' : <FaCopy />}</button>
            <button onClick={() => downloadFile(text, `msg_${Date.now()}.md`, 'text/markdown')}>
              <FaDownload />
            </button>
            <span className="time"><FaClock /> {timestamp}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const LiveTerminal = ({ logs, onClear, onExport }) => {
  const [filter, setFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    if (autoScroll && !isPaused) endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs, autoScroll, isPaused]);

  const filtered = logs.filter(l => filter === 'all' || l.level === filter);
  const total = logs.length;
  const errors = logs.filter(l => l.level === 'error').length;
  const success = logs.filter(l => l.level === 'success').length;

  return (
    <div className="terminal">
      <div className="terminal-header">
        <div className="terminal-title">
          <FaTerminal /> <span>Live Logs</span>
          <span className="live-badge">● Live</span>
        </div>
        <div className="terminal-actions">
          <button onClick={() => setIsPaused(!isPaused)} title={isPaused ? 'Resume' : 'Pause'}>
            {isPaused ? <FaPlay /> : <FaPause />}
          </button>
          <button onClick={onExport} title="Download logs">
            <FaDownload />
          </button>
          <button onClick={onClear} title="Clear logs">
            <FaTrash />
          </button>
        </div>
      </div>
      <div className="terminal-stats">
        <span>Total: <b>{total}</b></span>
        <span className="stat-success"><FaCheckCircle /> <b>{success}</b></span>
        <span className="stat-error"><FaTimesCircle /> <b>{errors}</b></span>
        <button className={autoScroll ? 'active' : ''} onClick={() => setAutoScroll(!autoScroll)}>
          Auto-scroll
        </button>
      </div>
      <div className="terminal-filters">
        {['all', 'success', 'info', 'warning', 'error'].map(f => (
          <button key={f} className={filter === f ? 'active' : ''} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>
      <div className="terminal-logs">
        {filtered.length === 0 ? (
          <div className="log-empty">
            <p>Waiting for events...</p>
            <p className="log-empty-sub">Agent is idle</p>
          </div>
        ) : (
          filtered.map((log, i) => (
            <div key={i} className={`log ${log.level}`}>
              <span className="log-time">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className="log-msg">{log.message}</span>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
      <div className="terminal-footer">
        <span className="dot">●</span> Listening for events...
        <span className="footer-count">{total} logs</span>
      </div>
    </div>
  );
};

const DeployModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [deployType, setDeployType] = useState('auto');
  const [autoFix, setAutoFix] = useState(true);

  useEffect(() => {
    if (isOpen) setRepoUrl(project?.repoUrl || '');
  }, [isOpen, project]);

  if (!isOpen) return null;

  const types = [
    { v: 'auto', l: 'Auto Detect' },
    { v: 'frontend', l: 'Frontend' },
    { v: 'backend', l: 'Backend' },
    { v: 'fullstack', l: 'Full Stack' },
  ];

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim(), deployType, autoFix });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3><FaRocket /> Deploy to Self-Host</h3>
        <p className="modal-sub">Deploy to agent's own infrastructure</p>

        <div style={{
          padding: '10px 14px', background: 'rgba(16,185,129,0.08)',
          border: '1px solid rgba(16,185,129,0.2)', borderRadius: '8px',
          marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <FaRobot style={{ fontSize: '20px', color: '#10b981' }} />
          <div style={{ fontSize: '11px' }}>
            <div style={{ fontWeight: 600, color: '#10b981' }}>Agent Self-Host</div>
            <div style={{ opacity: 0.6, fontSize: '10px' }}>Zero cost • Cloudflare URL</div>
          </div>
        </div>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div className="modal-field">
          <label>🎯 What to deploy</label>
          <div className="radio-group" style={{ flexWrap: 'wrap' }}>
            {types.map(({ v, l }) => (
              <button key={v} className={deployType === v ? 'active' : ''}
                onClick={() => setDeployType(v)} style={{ minWidth: '90px' }}>
                {l}
              </button>
            ))}
          </div>
        </div>

        <div className="modal-field">
          <label style={{
            textTransform: 'none', letterSpacing: 0, display: 'flex',
            alignItems: 'center', gap: '8px', cursor: 'pointer',
          }}>
            <input type="checkbox" checked={autoFix} onChange={(e) => setAutoFix(e.target.checked)} />
            🩺 Auto-fix code errors
          </label>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}><FaRocket /> Deploy</button>
        </div>
      </motion.div>
    </div>
  );
};

const PipelineModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [maxAttempts, setMaxAttempts] = useState(50);
  const [autoDeploy, setAutoDeploy] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRepoUrl(project?.repoUrl || '');
      setMaxAttempts(50);
      setAutoDeploy(false);
    }
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim(), maxAttempts, autoDeploy });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>⚙️ Create CI/CD Pipeline</h3>
        <p className="modal-sub">Generate GitHub Actions workflow</p>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div className="modal-field">
          <label>🔁 Max Auto-Fix Attempts: <b>{maxAttempts}</b></label>
          <input type="range" min="5" max="100" step="5"
            value={maxAttempts} onChange={(e) => setMaxAttempts(parseInt(e.target.value))}
            style={{ width: '100%' }} />
        </div>

        <div className="modal-field">
          <label style={{
            textTransform: 'none', letterSpacing: 0, display: 'flex',
            alignItems: 'center', gap: '8px', cursor: 'pointer',
          }}>
            <input type="checkbox" checked={autoDeploy} onChange={(e) => setAutoDeploy(e.target.checked)} />
            🚀 Auto-deploy after pipeline passes
          </label>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}>⚙️ Create</button>
        </div>
      </motion.div>
    </div>
  );
};

const MonitorModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [url, setUrl] = useState('');

  useEffect(() => {
    if (isOpen) {
      setRepoUrl(project?.repoUrl || '');
      setUrl('');
    }
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim(), url: url.trim() });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>📊 Monitor Service</h3>
        <p className="modal-sub">Start real-time monitoring</p>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div className="modal-field">
          <label>🌐 Live URL (optional)</label>
          <input type="text" placeholder="https://myapp.com"
            value={url} onChange={(e) => setUrl(e.target.value)} />
          <p style={{ fontSize: '10px', opacity: 0.5, marginTop: '4px' }}>
            Leave empty to auto-detect from deployments
          </p>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}>📊 Monitor</button>
        </div>
      </motion.div>
    </div>
  );
};

const ScaleModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [service, setService] = useState('');
  const [replicas, setReplicas] = useState(3);

  useEffect(() => {
    if (isOpen) {
      setRepoUrl(project?.repoUrl || '');
      const name = project?.projectName?.toLowerCase().replace(/\s+/g, '-') || '';
      setService(name);
      setReplicas(3);
    }
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim(), service, replicas });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>📈 Scale Service</h3>
        <p className="modal-sub">Adjust replica count</p>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div className="modal-field">
          <label>Service name (auto)</label>
          <input type="text" value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="auto from repo name" />
        </div>

        <div className="modal-field">
          <label>Target replicas: <b>{replicas}</b></label>
          <input type="range" min="1" max="10" value={replicas}
            onChange={(e) => setReplicas(parseInt(e.target.value))}
            style={{ width: '100%' }} />
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}>📈 Scale to {replicas}</button>
        </div>
      </motion.div>
    </div>
  );
};

const SecurityModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');

  useEffect(() => {
    if (isOpen) setRepoUrl(project?.repoUrl || '');
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim() });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>🔒 Security Scan</h3>
        <p className="modal-sub">Scan repo for vulnerabilities</p>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}>🔒 Scan</button>
        </div>
      </motion.div>
    </div>
  );
};

const FixCodeModal = ({ isOpen, onClose, onRun, project }) => {
  const [repoUrl, setRepoUrl] = useState('');

  useEffect(() => {
    if (isOpen) setRepoUrl(project?.repoUrl || '');
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleRun = () => {
    if (!repoUrl.trim()) return toast.error('GitHub URL required');
    if (!repoUrl.includes('github.com')) return toast.error('Only GitHub URLs');
    onRun({ repoUrl: repoUrl.trim() });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>🔧 Fix Code</h3>
        <p className="modal-sub">Find & fix all errors — creates PR</p>

        <div className="modal-field">
          <label>📦 GitHub Repo URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
        </div>

        <div style={{
          padding: '10px 12px', background: 'rgba(168,85,247,0.08)',
          border: '1px solid rgba(168,85,247,0.2)', borderRadius: '8px',
          fontSize: '10px', color: 'rgba(255,255,255,0.7)', marginBottom: '12px',
        }}>
          💡 Agent will scan, fix errors, and create a PR for review
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleRun}>🔧 Fix All</button>
        </div>
      </motion.div>
    </div>
  );
};

const AddProjectModal = ({ isOpen, onClose, onAdd, existingIds }) => {
  const [method, setMethod] = useState('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [projectName, setProjectName] = useState('');

  useEffect(() => {
    if (isOpen) {
      setRepoUrl('');
      setProjectName('');
      setMethod('github');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = () => {
    const url = repoUrl.trim();
    if (!url) return toast.error('Enter repo URL');
    if (!url.includes('github.com')) return toast.error('Only GitHub URLs supported');

    const urlParts = url.replace(/\.git$/, '').split('/');
    const repoName = urlParts[urlParts.length - 1] || 'Project';
    const name = projectName.trim() || repoName;

    const normalizedUrl = url.replace(/\.git$/, '').toLowerCase();
    const isDuplicate = (existingIds || []).some(
      (existing) => (existing || '').toLowerCase() === normalizedUrl
    );
    if (isDuplicate) {
      return toast.error('This project is already added');
    }

    onAdd({
      projectId: `proj-${Date.now()}`,
      projectName: name,
      source: method,
      repoUrl: url,
      branch: 'main',
      analysis: { healthScore: null },
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3><FaFolderOpen /> Add Project</h3>
        <p className="modal-sub">GitHub repo URL</p>

        <div className="modal-field">
          <label>Repository URL <span style={{ color: '#ef4444' }}>*</span></label>
          <input type="text" placeholder="https://github.com/user/repo"
            value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} />
        </div>

        <div className="modal-field">
          <label>Project Name (optional)</label>
          <input type="text" placeholder="My Project (auto-detected)"
            value={projectName} onChange={(e) => setProjectName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} />
          <p style={{ fontSize: '10px', opacity: 0.5, marginTop: '4px' }}>
            Leave empty to auto-detect from repo name
          </p>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleSubmit}><FaPlus /> Add</button>
        </div>
      </motion.div>
    </div>
  );
};

const ConfirmDeleteModal = ({ isOpen, onClose, onConfirm, projectName }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="modal-content" onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '380px' }}>
        <h3><FaTrash /> Delete Project?</h3>
        <p className="modal-sub">This action cannot be undone</p>

        <div style={{
          padding: '12px 14px', background: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.25)', borderRadius: '8px',
          marginBottom: '16px',
        }}>
          <div style={{ fontSize: '12px', opacity: 0.7, marginBottom: '4px' }}>You are about to remove:</div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#ef4444' }}>
            {projectName}
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={onConfirm}
            style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)' }}>
            <FaTrash /> Delete
          </button>
        </div>
      </motion.div>
    </div>
  );
};

const AssistantChat = () => {
  // ⭐ REAL USER from AuthContext
  const { user } = useAuth();

  const [messages, setMessages] = useState([{
    id: 'welcome',
    content: `# 🚀 Smart DevOps Assistant\n\nI can help with:\n- 🚀 **Deploy** (Self-Host)\n- ⚙️ **Pipeline** (CI/CD)\n- 🔧 **Fix Code** (auto-fix + PR)\n- 🔒 **Security** (scan)\n- 📊 **Monitor** (real-time)\n- 📈 **Scale** (replicas)\n\n**Add a project and try a button!**`,
    isUser: false,
    timestamp: new Date().toLocaleTimeString(),
  }]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [deployments, setDeployments] = useState([]);

  const [showDeployModal, setShowDeployModal] = useState(false);
  const [showPipelineModal, setShowPipelineModal] = useState(false);
  const [showMonitorModal, setShowMonitorModal] = useState(false);
  const [showScaleModal, setShowScaleModal] = useState(false);
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [showFixCodeModal, setShowFixCodeModal] = useState(false);
  const [showAddProjectModal, setShowAddProjectModal] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);

  const [projects, setProjects] = useState([]);
  const [projectsLoaded, setProjectsLoaded] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const [logs, setLogs] = useState([
    { timestamp: new Date().toISOString(), level: 'info', message: '🤖 Agent Socket Online' },
  ]);

  const messagesEndRef = useRef(null);
  const socketRef = useRef(null);

  const addLog = useCallback((level, message) => {
    setLogs(prev => [...prev, { timestamp: new Date().toISOString(), level, message }]);
  }, []);

  // Load projects
  useEffect(() => {
    const stored = loadProjectsFromStorage();
    setProjects(stored);
    setProjectsLoaded(true);
    if (stored.length > 0) {
      setSelectedProject(stored[0]);
    }
  }, []); // eslint-disable-line

  // Save projects
  useEffect(() => {
    if (projectsLoaded) {
      saveProjectsToStorage(projects);
    }
  }, [projects, projectsLoaded]);

  usePlatformEvents('assistant', (evt) => {
    addLog('info', `📡 ${evt.type} ${evt.data?.name || evt.data?.service_name || ''}`);
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const s = io(WS_URL, {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      timeout: 20000,
    });
    socketRef.current = s;

    s.on('connect', () => {
      setIsConnected(true);
      addLog('success', '🔌 WebSocket Connected');
    });
    s.on('disconnect', (reason) => {
      setIsConnected(false);
      addLog('warning', `🔌 Disconnected: ${reason}`);
    });
    s.on('connected', (data) => {
      addLog('success', `✅ ${data.message || 'Ready'}`);
    });
    s.on('live_log', (data) => {
      addLog(data.type || data.level || 'info', data.log || data.message || '');
    });
    s.on('chat_response', (data) => {
      if (data.error) {
        addLog('error', `❌ ${data.error}`);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `❌ **Error:** ${data.error}`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        }]);
        setLoading(false);
        return;
      }
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: data.message || '✅ Done',
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: data.execution,
      }]);
      setLoading(false);
    });
    s.on('deploy_complete', (data) => {
      setDeployments(prev => [...prev, data]);
      if (data.liveUrl) toast.success(`🎉 Live: ${data.liveUrl}`);
      setLoading(false);
    });

    return () => s.disconnect();
  }, [addLog]);

  const handleDeploy = async ({ repoUrl, deployType, autoFix }) => {
    const project = selectedProject || {
      projectId: 'default-project', projectName: 'Default Project',
    };

    setLoading(true);
    addLog('info', `🚀 Deploy: ${repoUrl}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `🚀 **Deploy started**\n\n- Repo: [${repoUrl}](${repoUrl})\n- Type: \`${deployType}\`\n- Auto-fix: \`${autoFix}\``,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 5,
        steps: [
          { name: 'Clone repo', status: 'running' },
          { name: 'Build', status: 'pending' },
          { name: 'Deploy', status: 'pending' },
          { name: 'Live', status: 'pending' },
        ],
      },
    }]);

    try {
      const res = await fetch(`${WS_URL}/api/devops/deploy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',   // ⭐ IMPORTANT
        body: JSON.stringify({
          repo_url: repoUrl,
          deploy_type: deployType,
          provider: 'self-host',
          user_id: user?.id,       // ⭐ REAL USER ID
          project_id: project.projectId,
          project_name: project.projectName,
        }),
      });
      const data = await res.json();

      if (data.success) {
        const url = data.url || data.live_url;
        addLog('success', `✅ Deployed: ${url}`);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `## ✅ Deployed!\n\n**URL:** [${url}](${url})`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
          execution: { status: 'completed', progress: 100, liveUrl: url },
        }]);
      } else {
        toast.error(data.error || 'Deploy failed');
      }
    } catch (e) {
      toast.error('Deploy error');
    }

    setLoading(false);
  };

  const handlePipeline = async ({ repoUrl, maxAttempts, autoDeploy }) => {
    setLoading(true);
    addLog('info', `⚙️ Pipeline: ${repoUrl}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `⚙️ **Pipeline creating**\n\n- Repo: [${repoUrl}](${repoUrl})\n- Auto-deploy: \`${autoDeploy}\``,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 10,
        steps: [
          { name: 'Parse repo', status: 'running' },
          { name: 'Generate YAML', status: 'pending' },
          { name: 'Commit', status: 'pending' },
          { name: 'Monitor', status: 'pending' },
        ],
      },
    }]);

    try {
      const res = await fetch(`${WS_URL}/api/devops/pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',   // ⭐ IMPORTANT
        body: JSON.stringify({
          repo_url: repoUrl,
          mode: autoDeploy ? 'ci-cd+deploy' : 'ci-cd-only',
          max_fix_attempts: maxAttempts,
          user_id: user?.id,       // ⭐ REAL USER ID
        }),
      });
      const data = await res.json();

      if (data.success) {
        addLog('success', '✅ Pipeline created');
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `## ✅ Pipeline created!\n\n${data.response || 'Check Pipelines page'}`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
          execution: { status: 'completed', progress: 100 },
        }]);
      } else {
        toast.error(data.error || 'Pipeline failed');
      }
    } catch (e) {
      toast.error('Pipeline error');
    }

    setLoading(false);
  };

  const handleMonitor = async ({ repoUrl, url }) => {
    setLoading(true);
    addLog('info', `📊 Monitoring: ${repoUrl}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `📊 **Monitoring started**\n\n- Repo: [${repoUrl}](${repoUrl})\n${url ? `- URL: ${url}` : ''}`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 30,
        steps: [
          { name: 'HTTP check', status: 'running' },
          { name: 'Save result', status: 'pending' },
        ],
      },
    }]);

    const result = await actionAPI.monitor({
      repo_url: repoUrl,
      url: url || null,
      user_id: user?.id,         // ⭐ REAL USER ID
    });

    if (result.success) {
      addLog('success', '✅ Monitor started');
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: result.response || `## ✅ Monitoring\n\n${result.action?.result?.url || url || 'Check Monitoring page'}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: { status: 'completed', progress: 100 },
      }]);
    } else {
      toast.error(result.error || 'Monitor failed');
    }

    setLoading(false);
  };

  const handleScale = async ({ repoUrl, service, replicas }) => {
    setLoading(true);
    addLog('info', `📈 Scaling ${service || 'app'} → ${replicas}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `📈 **Scaling**\n\n- Repo: [${repoUrl}](${repoUrl})\n- Service: \`${service || 'auto'}\`\n- Target: \`${replicas} replicas\``,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 20,
        steps: [
          { name: 'Detect state', status: 'running' },
          { name: 'Apply scaling', status: 'pending' },
          { name: 'Verify', status: 'pending' },
        ],
      },
    }]);

    const result = await actionAPI.scale({
      repo_url: repoUrl,
      service,
      replicas,
      user_id: user?.id,         // ⭐ REAL USER ID
    });

    if (result.success) {
      const res = result.action?.result || result.result || {};
      const oldR = res.old_replicas ?? res.old ?? 1;
      const newR = res.new_replicas ?? res.new ?? res.replicas ?? replicas;
      addLog('success', `✅ Scaled: ${oldR} → ${newR}`);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: result.response || `## ✅ Scaled!\n\n- Service: ${res.service || service}\n- ${oldR} → **${newR}** replicas`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: { status: 'completed', progress: 100 },
      }]);
    } else {
      toast.error(result.error || 'Scale failed');
    }

    setLoading(false);
  };

  const handleSecurity = async ({ repoUrl }) => {
    setLoading(true);
    addLog('info', `🔒 Security: ${repoUrl}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `🔒 **Scanning**\n\n- Repo: [${repoUrl}](${repoUrl})`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 30,
        steps: [
          { name: 'Clone', status: 'running' },
          { name: 'Scan files', status: 'pending' },
          { name: 'Analyze', status: 'pending' },
        ],
      },
    }]);

    const result = await actionAPI.security({
      repo_url: repoUrl,
      user_id: user?.id,         // ⭐ REAL USER ID
    });

    if (result.success) {
      const res = result.result || result.action?.result || {};
      addLog('success', `✅ Scan done: ${res.critical || 0}C ${res.high || 0}H`);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: result.response || `## 🔒 Security Report\n\n- Critical: **${res.critical || 0}**\n- High: **${res.high || 0}**\n- Medium: **${res.medium || 0}**\n- Low: **${res.low || 0}**`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: { status: 'completed', progress: 100 },
      }]);
    } else {
      toast.error(result.error || 'Scan failed');
    }

    setLoading(false);
  };

  const handleFixCode = async ({ repoUrl }) => {
    setLoading(true);
    addLog('info', `🔧 Fix Code: ${repoUrl}`);

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: `🔧 **Scanning & Fixing**\n\n- Repo: [${repoUrl}](${repoUrl})\n\n⚠️ This creates a PR`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      execution: {
        status: 'running', progress: 15,
        steps: [
          { name: 'Clone', status: 'running' },
          { name: 'Scan', status: 'pending' },
          { name: 'Fix', status: 'pending' },
          { name: 'Commit + PR', status: 'pending' },
        ],
      },
    }]);

    const result = await actionAPI.fixCode({
      repo_url: repoUrl,
      user_id: user?.id,         // ⭐ REAL USER ID
    });

    if (result.success) {
      const res = result.result || {};
      addLog('success', `✅ Fixed: ${res.message || 'done'}`);

      let content = `## ✅ Code Fixed!\n\n`;
      if (res.pr_url) content += `**PR:** [${res.pr_url}](${res.pr_url})\n\n`;
      if (res.branch) content += `**Branch:** \`${res.branch}\`\n\n`;
      if (res.files_fixed?.length) {
        content += `**Files fixed:**\n${res.files_fixed.map(f => `- \`${f.file}\` (${f.issues})`).join('\n')}`;
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: result.response || content,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: { status: 'completed', progress: 100, liveUrl: res.pr_url },
      }]);
    } else {
      toast.error(result.error || 'Fix failed');
    }

    setLoading(false);
  };

  const handleSend = async (customInput = null) => {
    const text = (customInput || input).trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      content: text,
      isUser: true,
      timestamp: new Date().toLocaleTimeString(),
    }]);
    setInput('');
    setLoading(true);
    addLog('info', `💬 ${text.substring(0, 60)}`);

    const project = selectedProject || {
      projectId: 'default-project', projectName: 'Default Project', source: 'default',
    };

    if (socketRef.current && isConnected) {
      socketRef.current.emit('chat', {
        message: text,
        user_id: user?.id,       // ⭐ REAL USER ID
        project_id: project.projectId,
        project_name: project.projectName,
        source: project.source,
      });

      setTimeout(() => setLoading(false), 180000);
    } else {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `✅ Received: \`${text}\``,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        }]);
        setLoading(false);
      }, 800);
    }
  };

  const handleQuickAction = (action) => {
    if (action === 'deploy') return setShowDeployModal(true);
    if (action === 'pipeline') return setShowPipelineModal(true);
    if (action === 'monitor') return setShowMonitorModal(true);
    if (action === 'scale') return setShowScaleModal(true);
    if (action === 'security') return setShowSecurityModal(true);
    if (action === 'fix_code') return setShowFixCodeModal(true);
  };

  const handleAddProject = (project) => {
    setProjects(prev => [...prev, project]);
    setSelectedProject(project);
    addLog('success', `📁 Added: ${project.projectName}`);
    toast.success(`✅ ${project.projectName} added`);
    setShowAddProjectModal(false);
  };

  const handleDeleteProject = (project) => {
    setDeleteTarget(project);
  };

  const confirmDeleteProject = () => {
    if (!deleteTarget) return;
    const id = deleteTarget.projectId;

    setProjects(prev => prev.filter(p => p.projectId !== id));

    if (selectedProject?.projectId === id) {
      setSelectedProject(null);
    }

    addLog('warning', `🗑️ Removed: ${deleteTarget.projectName}`);
    toast.success(`Removed ${deleteTarget.projectName}`);
    setDeleteTarget(null);
  };

  const startVoiceRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('Voice not supported. Use Chrome or Edge.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        addLog('info', '🎤 Voice listening...');
        toast.success('🎤 Listening...');
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) final += transcript;
          else interim += transcript;
        }
        if (final) setInput((prev) => (prev + ' ' + final).trim());
        else if (interim) setInput((prev) => (prev + ' ' + interim).trim());
      };

      recognition.onerror = (event) => {
        setIsListening(false);
        addLog('error', `🎤 Voice error: ${event.error}`);
        if (event.error === 'not-allowed') toast.error('Microphone permission denied');
        else if (event.error !== 'aborted') toast.error(`Voice error: ${event.error}`);
      };

      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e) {
      setIsListening(false);
      addLog('error', `🎤 Voice init failed: ${String(e).slice(0, 100)}`);
      toast.error('Voice init failed');
    }
  }, [addLog]);

  const stopVoiceRecognition = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  const toggleVoice = useCallback(() => {
    if (isListening) stopVoiceRecognition();
    else startVoiceRecognition();
  }, [isListening, startVoiceRecognition, stopVoiceRecognition]);

  const quickActions = [
    { icon: BsLightningCharge, label: 'Deploy', action: 'deploy', color: 'blue' },
    { icon: FiZap, label: 'Pipeline', action: 'pipeline', color: 'purple' },
    { icon: FaBug, label: 'Fix Code', action: 'fix_code', color: 'orange' },
    { icon: FaShieldAlt, label: 'Security', action: 'security', color: 'green' },
    { icon: FiActivity, label: 'Monitor', action: 'monitor', color: 'cyan' },
    { icon: FaCloud, label: 'Scale', action: 'scale', color: 'indigo' },
  ];

  const suggestions = [
    'Deploy https://github.com/Aruniisu/Tomo-coffee',
    'Create CI/CD pipeline',
    'Run security scan',
    'Monitor my app',
  ];

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearLogs = () => { setLogs([]); addLog('info', '🗑️ Cleared'); };

  const exportLogs = () => {
    if (!logs || logs.length === 0) {
      toast.error('No logs to download');
      return;
    }

    const now = new Date();
    const successCount = logs.filter(l => l.level === 'success').length;
    const errorCount = logs.filter(l => l.level === 'error').length;
    const warningCount = logs.filter(l => l.level === 'warning').length;
    const infoCount = logs.filter(l => l.level === 'info').length;

    const header = [
      '═══════════════════════════════════════════════════════════',
      '  Smart DevOps — Live Logs Export',
      '═══════════════════════════════════════════════════════════',
      `  Generated: ${now.toLocaleString()}`,
      `  User: ${user?.email || 'unknown'}`,
      `  Total: ${logs.length} logs`,
      `  ✅ Success: ${successCount}`,
      `  ⚠️  Warning: ${warningCount}`,
      `  ❌ Error: ${errorCount}`,
      `  ℹ️  Info: ${infoCount}`,
      '═══════════════════════════════════════════════════════════',
      '',
      '',
    ].join('\n');

    const body = logs.map((l) => {
      const ts = new Date(l.timestamp);
      const level = (l.level || 'info').toUpperCase().padEnd(7);
      return `[${ts.toLocaleDateString()} ${ts.toLocaleTimeString()}] [${level}] ${(l.message || '').replace(/\n/g, ' ')}`;
    }).join('\n');

    const footer = '\n\n═══════════════════════════════════════════════════════════\n';

    const filename = `smartdevops-logs-${now.toISOString().replace(/[:.]/g, '-').slice(0, 19)}.txt`;
    downloadFile(header + body + footer, filename, 'text/plain');

    toast.success(`Downloaded ${logs.length} logs`);
    addLog('success', `📥 Exported ${logs.length} logs`);
  };

  const existingRepoUrls = projects.map(p => (p.repoUrl || '').toLowerCase());

  return (
    <div className="chat-main">
      <div className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon"><FaRobot /></div>
          <div>
            <div className="logo-text">Smart <span>DevOps</span></div>
            <div className="logo-sub">Agentic AI Platform</div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-title">Active Context</div>
          {selectedProject ? (
            <div className="active-project">
              <div className="active-project-name">
                <FaFolderOpen /> {selectedProject.projectName}
              </div>
            </div>
          ) : (
            <div className="no-project">
              <p>No project selected</p>
            </div>
          )}
        </div>

        <div className="sidebar-section">
          <div className="section-title">System</div>
          <div className="health-item">
            <span className={`dot ${isConnected ? 'online' : 'offline'}`}></span>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Projects ({projects.length})</span>
            <button
              onClick={() => setShowAddProjectModal(true)}
              title="Add project"
              style={{
                background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                border: 'none', color: '#fff',
                width: '20px', height: '20px',
                borderRadius: '4px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '10px',
              }}>
              <FaPlus />
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="no-project" style={{ padding: '12px 0', textAlign: 'center' }}>
              <p style={{ fontSize: '11px', opacity: 0.5 }}>
                No projects yet.<br />Click <FaPlus size={9} /> to add one.
              </p>
            </div>
          ) : (
            projects.map((p) => (
              <div
                key={p.projectId}
                className={`project-item ${selectedProject?.projectId === p.projectId ? 'active' : ''}`}
                style={{ position: 'relative' }}
              >
                <div
                  onClick={() => setSelectedProject(p)}
                  style={{ cursor: 'pointer', flex: 1, minWidth: 0 }}
                >
                  <div className="project-name"><FaFolderOpen /> {p.projectName}</div>
                  <div className="project-meta">
                    <span>{p.source || 'github'}</span>
                  </div>
                </div>

                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteProject(p); }}
                  title="Delete project"
                  className="project-delete-btn"
                  style={{
                    position: 'absolute', right: '6px', top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)',
                    color: '#ef4444',
                    width: '22px', height: '22px',
                    borderRadius: '4px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '10px',
                    opacity: 0.7,
                    transition: 'opacity 0.15s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '0.7'}
                >
                  <FaTrash />
                </button>
              </div>
            ))
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar">{user?.name?.[0]?.toUpperCase() || 'D'}</div>
            <div>
              <div className="name">{user?.name || 'Demo User'}</div>
              <div className="role">{user?.role || 'Engineer'}</div>
            </div>
          </div>
          <div className="version">{APP_VERSION}</div>
        </div>
      </div>

      <div className="chat-center">
        <div className="chat-header">
          <div className="header-left">
            <h2><FaRobot /> AI Assistant</h2>
            <span className={`live-badge ${isConnected ? 'connected' : 'offline'}`}>
              ● {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          <div className="header-right">
            <button onClick={() => setShowAddProjectModal(true)}><FaPlus /> Add</button>
            <button onClick={() => setMessages([messages[0]])}><FaTrash /> Clear</button>
            <button className="primary" onClick={() => setShowDeployModal(true)}>
              <FaRocket /> Deploy
            </button>
          </div>
        </div>

        <div className="quick-actions">
          {quickActions.map((a, i) => (
            <button key={i} className={`qa-btn ${a.color}`} onClick={() => handleQuickAction(a.action)}>
              <a.icon /> {a.label}
            </button>
          ))}
        </div>

        <div className="messages">
          {messages.map((msg) => (
            <Message key={msg.id} message={msg.content} content={msg.content}
              isUser={msg.isUser} timestamp={msg.timestamp} execution={msg.execution} />
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-wrapper">
                <div className="avatar"><FaRobot /></div>
                <div className="bubble">
                  <div className="thinking">
                    <span className="dots"><span /><span /><span /></span>
                    <span>Processing...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="suggestions">
          <span>💡 Try:</span>
          {suggestions.map((s, i) => (
            <button key={i} onClick={() => handleSend(s)}>
              {s.length > 40 ? s.substring(0, 40) + '...' : s}
            </button>
          ))}
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            <textarea value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me to deploy, fix code, create pipelines... (or click mic for voice)"
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }} />
            <button
              className={`mic ${isListening ? 'listening' : ''}`}
              onClick={toggleVoice}
              title={isListening ? 'Stop listening' : 'Voice input'}
              type="button"
            >
              {isListening ? <FaStop /> : <FaMicrophone />}
            </button>
          </div>
          <button className="send" onClick={() => handleSend()} disabled={!input.trim() || loading}>
            {loading ? <FaSpinner className="spin" /> : <FaPaperPlane />}
          </button>
        </div>
      </div>

      <LiveTerminal logs={logs} onClear={clearLogs} onExport={exportLogs} />

      <DeployModal isOpen={showDeployModal} onClose={() => setShowDeployModal(false)}
        onRun={(d) => { handleDeploy(d); setShowDeployModal(false); }} project={selectedProject} />

      <PipelineModal isOpen={showPipelineModal} onClose={() => setShowPipelineModal(false)}
        onRun={(d) => { handlePipeline(d); setShowPipelineModal(false); }} project={selectedProject} />

      <MonitorModal isOpen={showMonitorModal} onClose={() => setShowMonitorModal(false)}
        onRun={(d) => { handleMonitor(d); setShowMonitorModal(false); }} project={selectedProject} />

      <ScaleModal isOpen={showScaleModal} onClose={() => setShowScaleModal(false)}
        onRun={(d) => { handleScale(d); setShowScaleModal(false); }} project={selectedProject} />

      <SecurityModal isOpen={showSecurityModal} onClose={() => setShowSecurityModal(false)}
        onRun={(d) => { handleSecurity(d); setShowSecurityModal(false); }} project={selectedProject} />

      <FixCodeModal isOpen={showFixCodeModal} onClose={() => setShowFixCodeModal(false)}
        onRun={(d) => { handleFixCode(d); setShowFixCodeModal(false); }} project={selectedProject} />

      <AddProjectModal
        isOpen={showAddProjectModal}
        onClose={() => setShowAddProjectModal(false)}
        onAdd={handleAddProject}
        existingIds={existingRepoUrls}
      />

      <ConfirmDeleteModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDeleteProject}
        projectName={deleteTarget?.projectName || ''}
      />
    </div>
  );
};

export default AssistantChat;