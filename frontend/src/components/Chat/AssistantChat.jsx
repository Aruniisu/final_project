import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { assistantAPI, uploadAPI } from '../../api/assistant';
import LeftSidebar from './LeftSidebar';
import LiveTerminal from './LiveTerminal';
import UploadModal from './UploadModal';
import './AssistantChat.css';
import { 
  FaRobot, 
  FaPaperPlane, 
  FaUpload, 
  FaMicrophone,
  FaSpinner,
  FaCheckCircle,
  FaTimesCircle,
  FaCopy,
  FaDownload,
  FaHistory,
  FaCode,
  FaFileCode,
  FaFileAlt,
  FaFolderOpen,
  FaRocket,
  FaBug,
  FaWrench,
  FaShieldAlt,
  FaCloud,
  FaTrash,
  FaSearch,
  FaArrowRight,
  FaClock,
  FaExternalLinkAlt
} from 'react-icons/fa';
import { 
  FiZap, 
  FiActivity, 
  FiCode, 
  FiCopy, 
  FiTrash2
} from 'react-icons/fi';
import { BsLightningCharge, BsRocket } from 'react-icons/bs';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// ============================================
// FILE DOWNLOAD UTILITY
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
  } catch (error) {
    toast.error('❌ Failed to download file');
    console.error(error);
  }
};

// ============================================
// MESSAGE COMPONENT
// ============================================
const Message = ({ message, isUser, timestamp, execution }) => {
  const [copied, setCopied] = useState(false);
  const [showDownloads, setShowDownloads] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message);
    setCopied(true);
    toast.success('📋 Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const extractCodeBlocks = (text) => {
    const regex = /```(\w+)?\n([\s\S]*?)```/g;
    const blocks = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      blocks.push({
        language: match[1] || 'text',
        code: match[2].trim()
      });
    }
    return blocks;
  };

  const codeBlocks = !isUser ? extractCodeBlocks(message) : [];
  const isLongMessage = message.length > 500;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`message ${isUser ? 'user' : 'assistant'}`}
    >
      <div className="message-bubble">
        <div className="message-avatar">
          {isUser ? <span>U</span> : <FaRobot />}
        </div>
        <div className="message-content">
          <div className="message-text">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <div className="code-block-wrapper">
                      <div className="code-header">
                        <span className="code-language">
                          <FaCode /> {match[1]}
                        </span>
                        <button 
                          className="code-download-btn"
                          onClick={() => {
                            const content = String(children).replace(/\n$/, '');
                            const ext = match[1] === 'javascript' ? 'js' : 
                                      match[1] === 'python' ? 'py' : 
                                      match[1] === 'jsx' ? 'jsx' : 
                                      match[1] === 'html' ? 'html' : 
                                      match[1] === 'css' ? 'css' : 
                                      match[1] === 'json' ? 'json' : 
                                      match[1] === 'yaml' ? 'yaml' : 
                                      match[1] === 'sh' ? 'sh' : 'txt';
                            downloadFile(content, `code.${ext}`, 'text/plain');
                          }}
                        >
                          <FaDownload /> Download
                        </button>
                      </div>
                      <SyntaxHighlighter
                        style={atomDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-xl !mt-0"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className="inline-code" {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {isLongMessage && !expanded ? message.substring(0, 500) + '...' : message}
            </ReactMarkdown>
          </div>

          {isLongMessage && (
            <button className="expand-btn" onClick={() => setExpanded(!expanded)}>
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}

          {/* Execution Details */}
          {execution && (
            <div className="execution-details">
              <div className="execution-header">
                <span className={`status-badge ${execution.status}`}>
                  {execution.status === 'running' && <FaSpinner className="spin" />}
                  {execution.status === 'completed' && <FaCheckCircle />}
                  {execution.status === 'failed' && <FaTimesCircle />}
                  {execution.status || 'Pending'}
                </span>
                <span className="progress-text">{execution.progress || 0}%</span>
                <span className="duration-text"><FaClock /> {execution.duration || '0s'}</span>
              </div>
              
              <div className="progress-bar">
                <div 
                  className={`progress-fill ${execution.status}`}
                  style={{ width: `${execution.progress || 0}%` }}
                />
              </div>
              
              {execution.url && (
                <div className="live-url">
                  <FaRocket />
                  <a href={execution.url} target="_blank" rel="noopener noreferrer">
                    {execution.url}
                  </a>
                  <button onClick={() => {
                    navigator.clipboard.writeText(execution.url);
                    toast.success('URL copied!');
                  }}>
                    <FaCopy />
                  </button>
                  <button onClick={() => window.open(execution.url, '_blank')}>
                    <FaExternalLinkAlt />
                  </button>
                </div>
              )}

              {execution.steps && execution.steps.length > 0 && (
                <div className="execution-steps">
                  <div className="steps-header">📋 Steps</div>
                  {execution.steps.map((step, i) => (
                    <div key={i} className={`step-item ${step.status}`}>
                      {step.status === 'completed' && <FaCheckCircle />}
                      {step.status === 'running' && <FaSpinner className="spin" />}
                      {step.status === 'failed' && <FaTimesCircle />}
                      <span>{step.name}</span>
                      {step.duration && <span className="step-duration">{step.duration}</span>}
                    </div>
                  ))}
                </div>
              )}

              {execution.errors && execution.errors.length > 0 && (
                <div className="errors-container">
                  <div className="errors-header"><FaBug /> Errors</div>
                  {execution.errors.map((error, i) => (
                    <div key={i} className="error-item">
                      <div className="error-message">{error.message}</div>
                      {error.fix && <div className="error-fix"><FaWrench /> {error.fix}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Download Options */}
          {!isUser && codeBlocks.length > 0 && (
            <div className="download-options">
              <button className="download-toggle" onClick={() => setShowDownloads(!showDownloads)}>
                <FaDownload /> {showDownloads ? 'Hide Files' : 'Download Files'}
              </button>
              {showDownloads && (
                <div className="download-list">
                  {codeBlocks.map((block, i) => {
                    const ext = block.language === 'javascript' ? 'js' : 
                              block.language === 'python' ? 'py' : 
                              block.language === 'jsx' ? 'jsx' : 
                              block.language === 'html' ? 'html' : 
                              block.language === 'css' ? 'css' : 
                              block.language === 'json' ? 'json' : 
                              block.language === 'yaml' ? 'yaml' : 
                              block.language === 'sh' ? 'sh' : 'txt';
                    return (
                      <button 
                        key={i}
                        className="download-item"
                        onClick={() => downloadFile(block.code, `file_${i+1}.${ext}`, 'text/plain')}
                      >
                        <FaFileCode /> {block.language || 'text'}
                      </button>
                    );
                  })}
                  <button 
                    className="download-all-btn"
                    onClick={() => {
                      codeBlocks.forEach((block, i) => {
                        const ext = block.language === 'javascript' ? 'js' : 
                                  block.language === 'python' ? 'py' : 'txt';
                        downloadFile(block.code, `file_${i+1}.${ext}`, 'text/plain');
                      });
                    }}
                  >
                    <FaDownload /> Download All
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="message-actions">
            <button onClick={handleCopy}>
              {copied ? '✓ Copied' : <FaCopy />}
            </button>
            <button onClick={() => downloadFile(message, `message_${Date.now()}.md`, 'text/markdown')}>
              <FaDownload />
            </button>
            <span className="timestamp"><FaClock /> {timestamp}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ============================================
// CHAT HISTORY COMPONENT
// ============================================
const ChatHistory = ({ history, onLoad, onDelete, onClear }) => {
  const [search, setSearch] = useState('');

  const filtered = history.filter(h => 
    h.query?.toLowerCase().includes(search.toLowerCase()) ||
    h.response?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="chat-history-panel">
      <div className="history-header">
        <h3><FaHistory /> History ({history.length})</h3>
        <button className="history-clear" onClick={onClear}><FaTrash /> Clear</button>
      </div>
      <div className="history-search">
        <FaSearch />
        <input 
          type="text" 
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="history-list">
        {filtered.length === 0 ? (
          <p className="no-history">No history found</p>
        ) : (
          filtered.map((item, i) => (
            <div key={i} className="history-item">
              <div className="history-item-header">
                <span className="history-query">{item.query?.substring(0, 50) || 'Unknown'}</span>
                <span className="history-time">{new Date(item.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="history-item-actions">
                <button onClick={() => onLoad(item)}><FaArrowRight /> Load</button>
                <button className="danger" onClick={() => onDelete(i)}><FaTrash /></button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ============================================
// QUICK ACTION BUTTON
// ============================================
const QuickActionBtn = ({ icon: Icon, label, onClick, color }) => (
  <button onClick={onClick} className={`quick-action-btn ${color}`}>
    <Icon /> <span>{label}</span>
  </button>
);

// ============================================
// MAIN COMPONENT
// ============================================
const AssistantChat = () => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      content: `# 🚀 Smart DevOps Assistant

## AI-Powered DevOps Automation

### ✨ What I Can Do
- 🚀 **Deploy** - Deploy with live URLs
- ⚙️ **Pipelines** - Create CI/CD pipelines
- 🔧 **Fix Code** - Auto-detect and fix errors
- 🔍 **Analyze** - Security scans
- 📊 **Monitor** - Real-time monitoring
- 📥 **Download** - Any file format

### 💡 Try These
- *"Deploy my project to production"*
- *"Create a CI/CD pipeline"*
- *"Fix errors in my code"*
- *"Run security scan"*

**Upload a project to get started!** 🚀`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      isWelcome: true
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [uploadedProjects, setUploadedProjects] = useState([]);
  const [logs, setLogs] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [executionStatus, setExecutionStatus] = useState('idle');
  const [execution, setExecution] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto Scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load Data
  useEffect(() => {
    loadProjects();
    loadChatHistory();
  }, []);

  const loadProjects = async () => {
    try {
      const projects = await uploadAPI.getHistory();
      const projectsWithAnalysis = await Promise.all(
        projects.map(async (p) => {
          try {
            const analysis = await uploadAPI.getAnalysis(p.projectId);
            return { ...p, analysis };
          } catch {
            return p;
          }
        })
      );
      setUploadedProjects(projectsWithAnalysis);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const loadChatHistory = async () => {
    try {
      const history = await assistantAPI.getHistory();
      setChatHistory(history);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const addLog = (level, message) => {
    setLogs(prev => [...prev, { timestamp: new Date().toISOString(), level, message }]);
  };

  // Send Message & Connect to Backend API
  const handleSend = async (customInput = null) => {
    const text = (customInput || input).trim();
    if (!text || isLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      content: text,
      isUser: true,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setExecutionStatus('running');
    addLog('info', `💬 User: ${text.substring(0, 50)}...`);

    try {
      if (!selectedProject) {
        const msg = {
          id: (Date.now() + 1).toString(),
          content: '⚠️ **No project selected!** Please upload or select a project first.',
          isUser: false,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, msg]);
        setIsLoading(false);
        setExecutionStatus('idle');
        return;
      }

      // 🔗 ඇත්තම Node.js Backend API එකට සම්බන්ධ වන කොටස
      const backendResponse = await assistantAPI.askQuestion(selectedProject.projectId, text);
      
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        content: backendResponse.data.response, 
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: backendResponse.data.execution // Backend එකෙන් එවන steps/progress bars
      };
      
      setMessages(prev => [...prev, assistantMsg]);
      setChatHistory(prev => [{ query: text, response: backendResponse.data.response, timestamp: new Date().toISOString() }, ...prev]);
      addLog('success', '✅ Agent task completed successfully!');
      setExecutionStatus('idle');

    } catch (error) {
      addLog('error', `❌ ${error.message}`);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        content: `❌ **Error:** ${error.message}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        execution: { status: 'failed', errors: [{ message: error.message }] }
      };
      setMessages(prev => [...prev, errorMsg]);
      setExecutionStatus('idle');
    }

    setIsLoading(false);
  };

  // Handlers
  const handleUploadComplete = (project) => {
    setUploadedProjects(prev => [project, ...prev]);
    setSelectedProject(project);
    toast.success(`✅ Project "${project.projectName}" uploaded!`);
    addLog('success', `📁 ${project.projectName} uploaded`);
  };

  const handleSelectProject = (project) => {
    setSelectedProject(project);
    toast.success(`✅ Selected: ${project.projectName}`);
    addLog('info', `📂 Selected: ${project.projectName}`);
  };

  const handleUploadClick = () => setShowUploadModal(true);
  const clearChat = () => { setMessages([messages[0]]); toast.success('Chat cleared'); };
  const clearLogs = () => { setLogs([]); toast.success('Logs cleared'); };
  const exportLogs = () => {
    const text = logs.map(l => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.message}`).join('\n');
    downloadFile(text, `logs-${new Date().toISOString().slice(0, 10)}.txt`, 'text/plain');
  };

  const loadHistory = (item) => {
    const msg = {
      id: Date.now().toString(),
      content: item.response,
      isUser: false,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, msg]);
    toast.success('History loaded');
  };

  const deleteHistory = (index) => {
    setChatHistory(prev => prev.filter((_, i) => i !== index));
    toast.success('History item deleted');
  };

  const clearHistory = () => {
    setChatHistory([]);
    toast.success('History cleared');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    { icon: BsRocket, label: 'Deploy', color: 'primary', action: () => handleSend('Deploy my project to production') },
    { icon: FiZap, label: 'Pipeline', color: 'accent', action: () => handleSend('Create a CI/CD pipeline') },
    { icon: FaBug, label: 'Fix Code', color: 'warning', action: () => handleSend('Fix errors in my code') },
    { icon: FaShieldAlt, label: 'Security', color: 'info', action: () => handleSend('Run security scan on my project') },
    { icon: FiActivity, label: 'Monitor', color: 'success', action: () => handleSend('Monitor my project') },
    { icon: FaCloud, label: 'Scale', color: 'primary', action: () => handleSend('Scale my service to 5 replicas') },
  ];

  const commandSuggestions = [
    'Deploy my project to production',
    'Create a CI/CD pipeline',
    'Fix errors in my code',
    'Run security scan',
    'Scale my service to 5 replicas',
    'Monitor my project',
    'Generate deployment report',
    'Rollback last deployment'
  ];

  return (
    <div className="chat-container">
      <LeftSidebar
        selectedProject={selectedProject}
        uploadedProjects={uploadedProjects}
        executionStatus={executionStatus}
        onSelectProject={handleSelectProject}
      />

      <div className="chat-panel">
        <div className="chat-header">
          <div className="chat-header-left">
            <h2 className="chat-header-title"><FaRobot /> AI Assistant</h2>
            <span className="chat-header-badge online">● Live</span>
            {selectedProject && <span className="project-badge"><FaFolderOpen /> {selectedProject.projectName}</span>}
          </div>
          <div className="chat-header-actions">
            <button className={`chat-header-btn history-btn ${showHistory ? 'active' : ''}`} onClick={() => setShowHistory(!showHistory)}>
              <FaHistory /> {showHistory ? 'Hide' : 'History'}
            </button>
            <button className="chat-header-btn" onClick={clearChat}><FaTrash /> Clear</button>
            <button className="chat-header-btn primary" onClick={handleUploadClick}><FaUpload /> Upload</button>
          </div>
        </div>

        <div className="quick-actions">
          {quickActions.map((action, index) => (
            <QuickActionBtn key={index} icon={action.icon} label={action.label} color={action.color} onClick={action.action} />
          ))}
        </div>

        {showHistory && (
          <ChatHistory history={chatHistory} onLoad={loadHistory} onDelete={deleteHistory} onClear={clearHistory} />
        )}

        <div className="chat-messages">
          {messages.map((msg) => (
            <Message key={msg.id} message={msg.content} isUser={msg.isUser} timestamp={msg.timestamp} execution={msg.execution} />
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-bubble">
                <div className="message-avatar"><FaRobot /></div>
                <div className="message-content">
                  <div className="thinking-indicator">
                    <div className="thinking-dots"><span className="thinking-dot" /><span className="thinking-dot" /><span className="thinking-dot" /></div>
                    <span className="thinking-text">Processing...</span>
                  </div>
                  {execution && (
                    <div className="mini-progress">
                      <div className="mini-progress-bar"><div className="mini-progress-fill" style={{ width: `${execution.progress || 0}%` }} /></div>
                      <span className="mini-progress-text">{execution.progress || 0}%</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="command-suggestions">
          <span className="suggestions-label">💡 Try:</span>
          {commandSuggestions.slice(0, 5).map((cmd, i) => (
            <button key={i} className="command-suggestion-btn" onClick={() => { setInput(cmd); setTimeout(() => handleSend(cmd), 100); }}>
              {cmd}
            </button>
          ))}
        </div>

        <div className="chat-input-area">
          <div className="chat-input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={selectedProject ? `Ask about ${selectedProject.projectName}...` : "Upload a project first..."}
              className="chat-input"
              rows={1}
              style={{ overflowY: 'auto', resize: 'none' }}
            />
            <button 
              className={`send-btn ${(!input.trim() || isLoading) ? 'disabled' : ''}`} 
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? <FaSpinner className="spin" /> : <FaPaperPlane />}
            </button>
          </div>
        </div>
      </div>

      {/* Live Terminal & Upload Modal Components */}
      <LiveTerminal logs={logs} onClear={clearLogs} onExport={exportLogs} />
      
      <UploadModal 
        isOpen={showUploadModal} 
        onClose={() => setShowUploadModal(false)} 
        onUploadComplete={handleUploadComplete} 
      />
    </div>
  );
};

export default AssistantChat;