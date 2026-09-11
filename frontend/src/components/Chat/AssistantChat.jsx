import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import io from 'socket.io-client';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './AssistantChat.css';

// Icons
import {
  FaRobot, FaPaperPlane, FaMicrophone, FaSpinner,
  FaCheckCircle, FaTimesCircle, FaCopy, FaDownload,
  FaCode, FaFolderOpen, FaRocket, FaBug, FaShieldAlt,
  FaCloud, FaTrash, FaClock, FaTerminal, FaGithub,
  FaExternalLinkAlt, FaGlobe, FaServer, FaPlay, FaPause,
  FaGitAlt, FaLayerGroup, FaPlus, FaMagic
} from 'react-icons/fa';
import { FiZap, FiActivity } from 'react-icons/fi';
import { BsLightningCharge } from 'react-icons/bs';

// ============================================
// Config
// ============================================
const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5000';

// ============================================
// Download utility
// ============================================
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
    toast.success(`✅ Downloaded: ${filename}`);
  } catch {
    toast.error('❌ Download failed');
  }
};

// ============================================
// Message Component
// ============================================
const Message = ({ message, content, isUser, timestamp, execution }) => {
  const [copied, setCopied] = useState(false);
  const text = (message ?? content ?? '').toString();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('📋 Copied!');
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
                        dockerfile: 'Dockerfile',
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
              <p style={{ opacity: 0.4, fontStyle: 'italic' }}>(empty message)</p>
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

// ============================================
// Live Terminal
// ============================================
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
          <button onClick={() => setIsPaused(!isPaused)}>
            {isPaused ? <FaPlay /> : <FaPause />}
          </button>
          <button onClick={onExport}><FaDownload /></button>
          <button onClick={onClear}><FaTrash /></button>
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

// ============================================
// Add Project Modal
// ============================================
const AddProjectModal = ({ isOpen, onClose, onAdd }) => {
  const [method, setMethod] = useState('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [projectName, setProjectName] = useState('');
  const [liveUrl, setLiveUrl] = useState('');
  const [template, setTemplate] = useState('react-node');

  if (!isOpen) return null;

  const methods = [
    { v: 'github', l: 'GitHub', i: FaGithub },
    { v: 'git', l: 'Git URL', i: FaGitAlt },
    { v: 'live', l: 'Live URL', i: FaGlobe },
    { v: 'template', l: 'Template', i: FaLayerGroup },
    { v: 'blank', l: 'Blank', i: FaCode },
  ];

  const handleSubmit = () => {
    if (method === 'github' || method === 'git') {
      if (!repoUrl.trim()) {
        toast.error('Please enter repo URL');
        return;
      }
      const name = projectName.trim() || repoUrl.split('/').pop().replace('.git', '') || 'Repo Project';
      onAdd({
        projectId: `${method}-${Date.now()}`,
        projectName: name,
        source: method,
        repoUrl,
        analysis: { healthScore: null },
      });
    } else if (method === 'live') {
      if (!liveUrl.trim()) {
        toast.error('Please enter live URL');
        return;
      }
      let name = projectName.trim();
      if (!name) {
        try { name = new URL(liveUrl).hostname; } catch { name = 'Live Project'; }
      }
      onAdd({
        projectId: `live-${Date.now()}`,
        projectName: name,
        source: 'live',
        liveUrl,
        analysis: { healthScore: null },
      });
    } else if (method === 'template') {
      onAdd({
        projectId: `tpl-${Date.now()}`,
        projectName: projectName.trim() || `${template} App`,
        source: 'template',
        template,
        analysis: { healthScore: 100 },
      });
    } else {
      onAdd({
        projectId: `blank-${Date.now()}`,
        projectName: projectName.trim() || 'New Project',
        source: 'blank',
        analysis: { healthScore: 100 },
      });
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <h3><FaFolderOpen /> Add Project</h3>
        <p className="modal-sub">Upload is optional — pick any method</p>

        <div className="modal-field">
          <label>Method</label>
          <div className="radio-group" style={{ flexWrap: 'wrap' }}>
            {methods.map(({ v, l, i: Icon }) => (
              <button key={v} className={method === v ? 'active' : ''} onClick={() => setMethod(v)}
                style={{ minWidth: '80px', fontSize: '10px' }}>
                <Icon /> {l}
              </button>
            ))}
          </div>
        </div>

        {(method === 'github' || method === 'git') && (
          <div className="modal-field">
            <label>Repository URL</label>
            <input type="text"
              placeholder={method === 'github' ? 'https://github.com/user/repo' : 'https://gitlab.com/user/repo.git'}
              value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} autoFocus />
          </div>
        )}

        {method === 'live' && (
          <div className="modal-field">
            <label>Live URL</label>
            <input type="text" placeholder="https://myapp.vercel.app"
              value={liveUrl} onChange={(e) => setLiveUrl(e.target.value)} autoFocus />
          </div>
        )}

        {method === 'template' && (
          <div className="modal-field">
            <label>Template</label>
            <select value={template} onChange={(e) => setTemplate(e.target.value)}>
              <option value="react-node">React + Node.js</option>
              <option value="nextjs">Next.js Full-Stack</option>
              <option value="python-flask">Python Flask API</option>
              <option value="static">Static HTML/CSS/JS</option>
              <option value="django">Django + PostgreSQL</option>
              <option value="mern">MERN Stack</option>
            </select>
          </div>
        )}

        <div className="modal-field">
          <label>Project Name (optional)</label>
          <input type="text" placeholder="My Awesome Project"
            value={projectName} onChange={(e) => setProjectName(e.target.value)} />
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleSubmit}>
            <FaRocket /> Add Project
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ============================================
// Deploy Modal
// ============================================
const DeployModal = ({ isOpen, onClose, project, onDeploy }) => {
  const [deployType, setDeployType] = useState('fullstack');
  const [provider, setProvider] = useState('auto');
  const [autoFix, setAutoFix] = useState(true);
  const [repoUrl, setRepoUrl] = useState('');

  // ⭐ Pre-fill repoUrl when project changes
  useEffect(() => {
    if (project?.repoUrl) {
      setRepoUrl(project.repoUrl);
    }
  }, [project]);

  if (!isOpen) return null;

  const handleDeployClick = () => {
    if (!repoUrl.trim()) {
      toast.error('Please enter a GitHub repo URL');
      return;
    }
    onDeploy({ deployType, provider, autoFix, repoUrl: repoUrl.trim() });
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <h3><FaRocket /> Deploy Project</h3>
        <p className="modal-sub">Configure deployment for <b>{project?.projectName || 'your project'}</b></p>

        <div className="modal-field">
          <label>Deploy Type</label>
          <div className="radio-group">
            {[
              { v: 'frontend', l: 'Frontend', i: FaGlobe },
              { v: 'backend', l: 'Backend', i: FaServer },
              { v: 'fullstack', l: 'Full Stack', i: FaLayerGroup },
            ].map(({ v, l, i: Icon }) => (
              <button key={v} className={deployType === v ? 'active' : ''} onClick={() => setDeployType(v)}>
                <Icon /> {l}
              </button>
            ))}
          </div>
        </div>

        <div className="modal-field">
          <label>Build Method (No local Docker needed)</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value)}>
            <option value="auto">🤖 Auto-detect (Recommended)</option>
            <option value="vercel">▲ Vercel (Frontend)</option>
            <option value="render">🎨 Render (Backend)</option>
            <option value="kaniko">Kaniko (In-cluster build)</option>
            <option value="buildah">Buildah (Daemonless)</option>
          </select>
        </div>

        <div className="modal-field">
          <label style={{ textTransform: 'none', letterSpacing: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="checkbox" checked={autoFix} onChange={(e) => setAutoFix(e.target.checked)} />
            Auto-fix code errors during deployment
          </label>
        </div>

        <div className="modal-field">
          <label>GitHub Repo URL ⭐ Required</label>
          <input
            type="text"
            placeholder="https://github.com/user/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            autoFocus
          />
          <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
            💡 This will trigger a real Vercel deployment
          </p>
        </div>

        <div className="modal-actions">
          <button onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleDeployClick}>
            <FaRocket /> Deploy Now
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================
const AssistantChat = () => {
  const [messages, setMessages] = useState([{
    id: 'welcome',
    content: `# 🚀 Welcome to Smart DevOps Assistant

I can help you with:
- 🚀 **Deploy** your applications
- ⚙️ **Pipeline** creation and management
- 🔧 **Fix Code** errors automatically
- 🔍 **Security** scans
- 📊 **Monitor** your infrastructure
- 📈 **Scale** your services

**Add a project and type a command to get started!**`,
    isUser: false,
    timestamp: new Date().toLocaleTimeString(),
  }]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [showAddProjectModal, setShowAddProjectModal] = useState(false);
  const [deployments, setDeployments] = useState([]);

  const [projects, setProjects] = useState([
    { projectId: 'demo-1', projectName: 'Demo Project', source: 'github', repoUrl: 'https://github.com/user/demo', analysis: { healthScore: 85 } },
    { projectId: 'test-1', projectName: 'Test Upload', source: 'file', analysis: { healthScore: 92 } },
  ]);

  const [logs, setLogs] = useState([
    { timestamp: new Date().toISOString(), level: 'info', message: '🤖 Agent Socket Stream Online' },
    { timestamp: new Date().toISOString(), level: 'info', message: '⏳ Waiting for commands...' },
  ]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const socketRef = useRef(null);

  const addLog = useCallback((level, message) => {
    setLogs(prev => [...prev, { timestamp: new Date().toISOString(), level, message }]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ============================================
  // WebSocket Connection
  // ============================================
  useEffect(() => {
    console.log('🔌 Connecting to:', WS_URL);

    const newSocket = io(WS_URL, {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      autoConnect: true,
    });

    socketRef.current = newSocket;

    newSocket.on('connect', () => {
      console.log('✅ Socket connected!', newSocket.id);
      setIsConnected(true);
      addLog('success', '🔌 WebSocket Connected');
    });

    newSocket.on('disconnect', (reason) => {
      console.log('❌ Socket disconnected:', reason);
      setIsConnected(false);
      addLog('warning', `🔌 Disconnected: ${reason}`);
    });

    newSocket.on('connect_error', (err) => {
      console.error('❌ Socket connect error:', err.message);
      addLog('error', `❌ Connect error: ${err.message}`);
    });

    newSocket.on('connected', (data) => {
      console.log('📡 Server says connected:', data);
      addLog('success', `✅ ${data.message || 'Server ready'}`);
    });

    newSocket.on('live_log', (data) => {
      const level = data.type || data.level || 'info';
      const msg = data.log || data.message || '';
      addLog(level, msg);
    });

    newSocket.on('chat_response', (data) => {
      console.log('💬 chat_response:', data);

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

      const replyText = typeof data.message === 'string' && data.message.trim()
        ? data.message
        : '✅ Task completed!';

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: replyText,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: data.execution,
      }]);
      setLoading(false);
      addLog('success', '✅ Response received');
    });

    newSocket.on('action_response', (data) => {
      console.log('⚡ action_response:', data);
      if (data.status === 'success') {
        addLog('success', `✅ ${data.action} done`);
      } else {
        addLog('error', `❌ ${data.action} failed`);
      }
      setLoading(false);
    });

    newSocket.on('deploy_complete', (data) => {
      console.log('🎉 deploy_complete:', data);
      setDeployments(prev => [...prev, data]);

      // Only add chat message if it's not already added
      // (the chat_response handler handles the main message)
      if (data.error) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `## ❌ Deployment Failed\n\n**Error:** ${data.error}`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        }]);
      } else {
        toast.success(`🎉 Live at ${data.liveUrl}`);
      }
      setLoading(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
      socketRef.current = null;
    };
  }, [addLog]);

  // ============================================
  // Send Message
  // ============================================
  const handleSend = async (customInput = null) => {
    console.log('🚀 handleSend called');

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
    addLog('info', `💬 User: ${text.substring(0, 60)}`);

    let project = selectedProject;
    if (!project) {
      project = {
        projectId: 'default-project',
        projectName: 'Default Project',
        source: 'default',
      };
      addLog('warning', '⚠️ No project selected — using default');
    }

    if (socketRef.current && isConnected) {
      socketRef.current.emit('chat', {
        message: text,
        user_id: 'demo_user',
        project_id: project.projectId,
        project_name: project.projectName,
        source: project.source,
      });

      // Longer timeout for real deployments (Vercel can take 2-3 min)
      setTimeout(() => {
        setLoading(prevLoading => {
          if (prevLoading) {
            console.log('⏱️ Loading timeout — resetting');
            return false;
          }
          return prevLoading;
        });
      }, 180000); // 3 minutes
    } else {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: `✅ **Task received!**\n\n\`${text}\`\n\n*Socket not connected — mock response*`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
          execution: {
            status: 'completed',
            progress: 100,
            duration: '0.8s',
            steps: [
              { name: 'Analyze', status: 'completed', duration: '0.3s' },
              { name: 'Execute', status: 'completed', duration: '0.5s' },
            ],
          },
        }]);
        setLoading(false);
      }, 1000);
    }
  };

  // ============================================
  // Quick Actions
  // ============================================
  const handleQuickAction = (action) => {
    console.log('⚡ Quick action:', action);

    let project = selectedProject;
    if (!project) {
      project = { projectId: 'default-project', projectName: 'Default Project', source: 'default' };
    }

    if (socketRef.current && isConnected) {
      setLoading(true);
      addLog('info', `🚀 ${action.toUpperCase()} → ${project.projectName}`);
      socketRef.current.emit('devops_action', {
        action,
        project_id: project.projectId,
        project_name: project.projectName,
        user_id: 'demo_user',
      });
      setTimeout(() => setLoading(false), 60000);
    } else {
      handleSend(action);
    }
  };

  // ============================================
  // Deploy Handler
  // ============================================
  const handleDeploy = ({ deployType, provider, autoFix, repoUrl }) => {
    console.log('🚀 handleDeploy:', { deployType, provider, autoFix, repoUrl });

    let project = selectedProject;
    if (!project) {
      project = { projectId: 'default-project', projectName: 'Default Project', source: 'default' };
    }

    // ⭐ Use the repoUrl from the modal (this is what gets passed)
    const finalRepoUrl = repoUrl || project.repoUrl || null;

    if (!finalRepoUrl) {
      toast.error('Please provide a GitHub repo URL');
      return;
    }

    const payload = {
      projectId: project.projectId,
      projectName: project.projectName,
      deployType,
      provider,
      autoFix,
      repoUrl: finalRepoUrl,
      source: project.source || 'github',
      user_id: 'demo_user',
    };

    addLog('info', `🚀 Deploy: ${deployType} (${provider}) → ${finalRepoUrl}`);

    if (socketRef.current && isConnected) {
      socketRef.current.emit('deploy_start', payload);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: `⏳ **Deployment started**\n\n- Type: \`${deployType}\`\n- Builder: \`${provider}\`\n- Repo: [${finalRepoUrl}](${finalRepoUrl})\n\nWatch the **Live Terminal** →`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: {
          status: 'running',
          progress: 5,
          steps: [
            { name: '📦 Clone repo', status: 'running' },
            { name: '🔍 Detect stack', status: 'pending' },
            { name: '⚙️ Create Vercel project', status: 'pending' },
            { name: '🚀 Deploy', status: 'pending' },
            { name: '✅ Health check', status: 'pending' },
          ],
        },
      }]);

      // Long timeout for real deployments
      setTimeout(() => {
        setLoading(prevLoading => {
          if (prevLoading) return false;
          return prevLoading;
        });
      }, 180000);
    } else {
      toast.error('Socket not connected');
    }
  };

  // ============================================
  // Helpers
  // ============================================
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
    'Fix this code: ```python def add(a, b) return a + b```',
    'Create CI/CD pipeline',
    'Run security scan',
    'Scale to 5 replicas',
  ];

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearLogs = () => { setLogs([]); addLog('info', '🗑️ Logs cleared'); };
  const exportLogs = () => {
    const text = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    downloadFile(text, `logs_${Date.now()}.txt`);
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="chat-main">
      {/* SIDEBAR */}
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
              <div className="active-project-meta">
                <span className="health">{selectedProject.analysis?.healthScore || '—'}%</span>
                <span className="source">{selectedProject.source}</span>
              </div>
            </div>
          ) : (
            <div className="no-project">
              <p>No project selected</p>
              <p className="no-project-sub">Pick one below or use default</p>
            </div>
          )}
        </div>

        <div className="sidebar-section">
          <div className="section-title">System Health</div>
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
              style={{
                background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                border: 'none', color: '#fff',
                width: '18px', height: '18px',
                borderRadius: '4px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
              title="Add Project"
            >
              <FaPlus />
            </button>
          </div>

          {projects.map((p) => (
            <div
              key={p.projectId}
              className={`project-item ${selectedProject?.projectId === p.projectId ? 'active' : ''}`}
              onClick={() => setSelectedProject(p)}
            >
              <div className="project-name">
                <FaFolderOpen /> {p.projectName}
              </div>
              <div className="project-meta">
                <span>{p.source}</span>
                <span className="health">Health: {p.analysis?.healthScore ? `${p.analysis.healthScore}%` : '—'}</span>
              </div>
            </div>
          ))}
        </div>

        {deployments.length > 0 && (
          <div className="sidebar-section">
            <div className="section-title">Live Deployments</div>
            {deployments.slice(-3).map((d, i) => (
              <a key={i} href={d.liveUrl} target="_blank" rel="noopener noreferrer" className="deploy-link">
                <FaRocket /> {d.type || 'app'}
              </a>
            ))}
          </div>
        )}

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar">D</div>
            <div>
              <div className="name">Demo User</div>
              <div className="role">Engineer</div>
            </div>
          </div>
          <div className="version">v3.0.0 • {isConnected ? 'Online' : 'Idle'}</div>
        </div>
      </div>

      {/* CENTER CHAT */}
      <div className="chat-center">
        <div className="chat-header">
          <div className="header-left">
            <h2><FaRobot /> AI Assistant</h2>
            <span className={`live-badge ${isConnected ? 'connected' : 'offline'}`}>
              ● {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          <div className="header-right">
            <button onClick={() => setShowAddProjectModal(true)}>
              <FaPlus /> Add
            </button>
            <button onClick={() => setMessages([messages[0]])}>
              <FaTrash /> Clear
            </button>
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
            <Message
              key={msg.id}
              message={msg.content}
              content={msg.content}
              isUser={msg.isUser}
              timestamp={msg.timestamp}
              execution={msg.execution}
            />
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-wrapper">
                <div className="avatar"><FaRobot /></div>
                <div className="bubble">
                  <div className="thinking">
                    <span className="dots"><span /><span /><span /></span>
                    <span>Processing... (this may take 1-2 minutes for real deploys)</span>
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
            <button key={i} onClick={() => handleSend(s)}>{s.length > 40 ? s.substring(0, 40) + '...' : s}</button>
          ))}
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me to deploy, fix code, create pipelines..."
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
            />
            <button className="mic"><FaMicrophone /></button>
          </div>
          <button className="send" onClick={() => handleSend()} disabled={!input.trim() || loading}>
            {loading ? <FaSpinner className="spin" /> : <FaPaperPlane />}
          </button>
        </div>
      </div>

      <LiveTerminal logs={logs} onClear={clearLogs} onExport={exportLogs} />

      <AddProjectModal
        isOpen={showAddProjectModal}
        onClose={() => setShowAddProjectModal(false)}
        onAdd={(newProject) => {
          setProjects(prev => [...prev, newProject]);
          setSelectedProject(newProject);
          addLog('success', `📁 Added: ${newProject.projectName}`);
          toast.success(`✅ ${newProject.projectName} added`);
          setShowAddProjectModal(false);
        }}
      />

      <DeployModal
        isOpen={showDeployModal}
        onClose={() => setShowDeployModal(false)}
        project={selectedProject}
        onDeploy={handleDeploy}
      />
    </div>
  );
};

export default AssistantChat;