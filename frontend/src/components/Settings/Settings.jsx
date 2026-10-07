import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './Settings.css';
import usePlatformEvents from '../../hooks/usePlatformEvents';
import { useSettings } from '../../context/SettingsContext';
import { useAuth } from '../../context/AuthContext';
import { APP_VERSION } from '../../config/version';
import {
  FiSettings, FiShield, FiBell, FiLock,
  FiLink, FiChevronRight,
  FiMoon, FiSun, FiMonitor, FiZap,
  FiLoader, FiX, FiEye, FiEyeOff, FiAlertCircle, FiCheck,
  FiSend,
} from 'react-icons/fi';
import { FaGithub, FaRobot, FaSlack } from 'react-icons/fa';
import toast from 'react-hot-toast';
import axios from 'axios';
import AuditLogs from './AuditLogs';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// ═══════════════════════════════════════════════════════════
// Change Password Modal
// ═══════════════════════════════════════════════════════════
const ChangePasswordModal = ({ isOpen, onClose }) => {
  const [current, setCurrent] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const checks = {
    length: newPw.length >= 12,
    upper: /[A-Z]/.test(newPw),
    number: /\d/.test(newPw),
    symbol: /[^A-Za-z0-9]/.test(newPw),
  };
  const allValid = Object.values(checks).every(Boolean);
  const matches = newPw && newPw === confirm;

  const handleSubmit = async () => {
    if (!current || !allValid || !matches) return;
    setLoading(true);
    try {
      const r = await axios.post('/api/auth/change-password', {
        current_password: current,
        new_password: newPw,
      });
      if (r.data.success) {
        toast.success('Password changed successfully! 🔒');
        onClose();
        setCurrent(''); setNewPw(''); setConfirm('');
      } else {
        toast.error(r.data.error || 'Failed');
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    background: 'rgba(15, 23, 42, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    borderRadius: '10px',
    color: '#fff',
    fontSize: '13px',
    outline: 'none',
  };

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '20px', backdropFilter: 'blur(4px)',
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: '440px',
          background: 'rgba(30, 41, 59, 0.98)',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          borderRadius: '20px', padding: '28px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '12px',
              background: 'linear-gradient(135deg, #a855f7, #6366f1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <FiLock style={{ color: '#fff', fontSize: '18px' }} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Change Password</div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Min 12 chars, strong</div>
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none',
            color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: '20px',
          }}><FiX /></button>
        </div>

        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
            Current Password
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type={showPw ? 'text' : 'password'}
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              placeholder="Current password"
              autoFocus
              style={{ ...inputStyle, paddingRight: '40px' }}
            />
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              style={{
                position: 'absolute', right: '12px', top: '50%',
                transform: 'translateY(-50%)', background: 'none',
                border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer',
              }}
            >
              {showPw ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>
        </div>

        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
            New Password
          </label>
          <input
            type={showPw ? 'text' : 'password'}
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            placeholder="Min 12 chars"
            style={inputStyle}
          />
          {newPw && (
            <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '10px' }}>
              {[
                ['length', '12+ chars'],
                ['upper', 'Uppercase'],
                ['number', 'Number'],
                ['symbol', 'Symbol'],
              ].map(([k, l]) => (
                <div key={k} style={{
                  color: checks[k] ? '#10b981' : 'rgba(255,255,255,0.35)',
                  display: 'flex', alignItems: 'center', gap: '4px',
                }}>
                  <FiCheck size={10} /> {l}
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
            Confirm Password
          </label>
          <input
            type={showPw ? 'text' : 'password'}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Repeat"
            style={{
              ...inputStyle,
              borderColor: confirm && !matches ? '#ef4444' : 'rgba(148, 163, 184, 0.2)',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={onClose} style={{
            flex: 1, padding: '11px',
            background: 'rgba(148, 163, 184, 0.1)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '10px', color: '#fff',
            cursor: 'pointer', fontSize: '13px', fontWeight: 500,
          }}>
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !current || !allValid || !matches}
            style={{
              flex: 2, padding: '11px',
              background: 'linear-gradient(135deg, #a855f7, #6366f1)',
              border: 'none', borderRadius: '10px',
              color: '#fff', cursor: 'pointer',
              fontSize: '13px', fontWeight: 600,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              opacity: (!current || !allValid || !matches || loading) ? 0.5 : 1,
            }}
          >
            {loading ? <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Saving...</> : 'Change Password'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// GitHub Connect Modal
// ═══════════════════════════════════════════════════════════
const GitHubConnectModal = ({ isOpen, onClose, onConnected }) => {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    const t = token.trim();
    if (!t) return setError('Token required');
    if (!t.startsWith('ghp_') && !t.startsWith('github_pat_')) {
      return setError('Invalid format. Should start with "ghp_" or "github_pat_"');
    }

    setLoading(true);
    setError('');
    try {
      const r = await axios.post('/api/auth/verify-github', { github_token: t });
      if (r.data.valid) {
        toast.success(`Connected as ${r.data.user.login}! 🎉`);
        onConnected(r.data.user);
        onClose();
        setToken('');
      } else {
        setError(r.data.error || 'Invalid token');
      }
    } catch (e) {
      setError(e.response?.data?.error || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '20px', backdropFilter: 'blur(4px)',
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: '460px',
          background: 'rgba(30, 41, 59, 0.98)',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          borderRadius: '20px', padding: '28px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '12px',
              background: 'linear-gradient(135deg, #333, #1a1a1a)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <FaGithub style={{ color: '#fff', fontSize: '20px' }} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Connect GitHub</div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Personal Access Token (Classic)</div>
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none',
            color: 'rgba(255,255,255,0.5)', cursor: 'pointer', fontSize: '20px',
          }}><FiX /></button>
        </div>

        <div style={{
          padding: '12px 14px',
          background: 'rgba(168, 85, 247, 0.08)',
          border: '1px solid rgba(168, 85, 247, 0.2)',
          borderRadius: '10px', fontSize: '11px',
          color: 'rgba(255,255,255,0.7)', lineHeight: 1.6, marginBottom: '16px',
        }}>
          <strong style={{ color: '#a855f7' }}>💡 How to get token:</strong>
          <ol style={{ margin: '6px 0 0 0', paddingLeft: '18px' }}>
            <li>Go to <a href="https://github.com/settings/tokens/new" target="_blank" rel="noreferrer" style={{ color: '#a855f7' }}>github.com/settings/tokens/new</a></li>
            <li>Select <strong>Classic</strong> token</li>
            <li>Scopes: <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: '3px' }}>read:user</code> + <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: '3px' }}>user:email</code></li>
            <li>Generate → Copy → Paste below</li>
          </ol>
        </div>

        <input
          type="password"
          value={token}
          onChange={(e) => { setToken(e.target.value); setError(''); }}
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
          autoFocus
          style={{
            width: '100%', padding: '12px 14px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: `1px solid ${error ? '#ef4444' : 'rgba(148, 163, 184, 0.2)'}`,
            borderRadius: '10px', color: '#fff',
            fontSize: '12px', fontFamily: 'monospace',
            outline: 'none', marginBottom: '10px',
          }}
          onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
        />

        {error && (
          <div style={{
            padding: '8px 12px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: '8px', fontSize: '11px',
            color: '#f87171', display: 'flex',
            alignItems: 'center', gap: '6px', marginBottom: '12px',
          }}>
            <FiAlertCircle size={12} /> {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
          <button onClick={onClose} style={{
            flex: 1, padding: '11px',
            background: 'rgba(148, 163, 184, 0.1)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: '10px', color: '#fff',
            cursor: 'pointer', fontSize: '13px', fontWeight: 500,
          }}>
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={loading || !token.trim()}
            style={{
              flex: 2, padding: '11px',
              background: 'linear-gradient(135deg, #a855f7, #6366f1)',
              border: 'none', borderRadius: '10px',
              color: '#fff', cursor: 'pointer',
              fontSize: '13px', fontWeight: 600,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              opacity: (!token.trim() || loading) ? 0.5 : 1,
            }}
          >
            {loading ? <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Verifying...</> : <><FaGithub /> Connect</>}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// Main Settings
// ═══════════════════════════════════════════════════════════
const Settings = () => {
  const { settings, loading: settingsLoading, updateSetting } = useSettings();
  const { user, refreshUser } = useAuth();

  const [activeTab, setActiveTab] = useState('general');
  const [showAuditLogs, setShowAuditLogs] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showGitHubConnect, setShowGitHubConnect] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  // ⭐ Slack + Email test states
  const [slackWebhook, setSlackWebhook] = useState('');
  const [testingEmail, setTestingEmail] = useState(false);
  const [testingSlack, setTestingSlack] = useState(false);

  usePlatformEvents('settings', (evt) => {
    console.log('📡 Settings received:', evt.type);
  });

  useEffect(() => {
    if (user?.tokens?.slack_webhook) {
      setSlackWebhook(user.tokens.slack_webhook);
    }
  }, [user]);

  const tabs = [
    { id: 'general', label: 'General', icon: FiSettings },
    { id: 'appearance', label: 'Appearance', icon: FiMonitor },
    { id: 'notifications', label: 'Notifications', icon: FiBell },
    { id: 'security', label: 'Security', icon: FiShield },
    { id: 'integrations', label: 'Integrations', icon: FiLink },
    { id: 'about', label: 'About', icon: FiZap },
  ];

  const handleUpdate = async (key, value) => {
    await updateSetting(key, value);
    toast.success('Setting saved', { duration: 1200 });
  };

  const handleGitHubConnected = async () => {
    await refreshUser();
    setShowGitHubConnect(false);
  };

  const handleGitHubDisconnect = async () => {
    if (!window.confirm('Disconnect GitHub?')) return;
    setDisconnecting(true);
    try {
      await axios.delete('/api/auth/tokens/github');
      await refreshUser();
      toast.success('GitHub disconnected');
    } catch {
      toast.error('Failed');
    } finally {
      setDisconnecting(false);
    }
  };

  const handleTestEmail = async () => {
    setTestingEmail(true);
    try {
      const r = await axios.post('/api/auth/test-email');
      if (r.data.success) toast.success('✅ Test email sent! Check your inbox.');
      else toast.error(r.data.error || 'Failed to send', { duration: 6000 });
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed', { duration: 6000 });
    } finally {
      setTestingEmail(false);
    }
  };

  const handleTestSlack = async () => {
    setTestingSlack(true);
    try {
      const r = await axios.post('/api/auth/test-slack');
      if (r.data.success) toast.success('✅ Test message sent to Slack!');
      else toast.error(r.data.error || 'Failed', { duration: 6000 });
    } catch (e) {
      toast.error(e.response?.data?.error || 'Failed', { duration: 6000 });
    } finally {
      setTestingSlack(false);
    }
  };

  const handleSaveSlackWebhook = async () => {
    try {
      const r = await axios.put('/api/auth/tokens', { slack_webhook: slackWebhook });
      if (r.data.success) {
        toast.success('Slack webhook saved');
        await refreshUser();
      }
    } catch {
      toast.error('Failed to save');
    }
  };

  const githubConnected = !!user?.tokens?.github;

  // ─── General (UPDATED: Language English only, Timezone expanded) ───
  const renderGeneral = () => (
    <div className="settings-card">
      <h4 className="settings-card-title">General Settings</h4>
      
      {/* Language - English Only */}
      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Language</p>
          <p className="settings-item-description">English (Default)</p>
        </div>
        <select 
          value="en" 
          disabled 
          className="settings-select" 
          style={{ opacity: 0.6, cursor: 'not-allowed' }}
        >
          <option value="en">English</option>
        </select>
      </div>

      {/* Timezone - Global Expanded */}
      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Timezone</p>
          <p className="settings-item-description">Your current timezone</p>
        </div>
        <select 
          value={settings.timezone || 'UTC'}
          onChange={(e) => handleUpdate('timezone', e.target.value)}
          className="settings-select"
          style={{ maxWidth: '280px' }}
        >
          <option value="UTC">UTC (Coordinated Universal Time)</option>
          <option value="Pacific/Honolulu">(GMT-10:00) Hawaii</option>
          <option value="America/Anchorage">(GMT-09:00) Alaska</option>
          <option value="America/Los_Angeles">(GMT-08:00) Pacific Time (US & Canada)</option>
          <option value="America/Denver">(GMT-07:00) Mountain Time (US & Canada)</option>
          <option value="America/Chicago">(GMT-06:00) Central Time (US & Canada)</option>
          <option value="America/New_York">(GMT-05:00) Eastern Time (US & Canada)</option>
          <option value="America/Sao_Paulo">(GMT-03:00) Sao Paulo</option>
          <option value="Europe/London">(GMT+00:00) London</option>
          <option value="Europe/Paris">(GMT+01:00) Paris, Berlin, Rome</option>
          <option value="Europe/Athens">(GMT+02:00) Athens, Cairo</option>
          <option value="Europe/Moscow">(GMT+03:00) Moscow, Riyadh</option>
          <option value="Asia/Dubai">(GMT+04:00) Dubai, Abu Dhabi</option>
          <option value="Asia/Karachi">(GMT+05:00) Karachi, Islamabad</option>
          <option value="Asia/Kolkata">(GMT+05:30) Mumbai, New Delhi</option>
          <option value="Asia/Colombo">(GMT+05:30) Colombo, Sri Lanka</option>
          <option value="Asia/Dhaka">(GMT+06:00) Dhaka</option>
          <option value="Asia/Bangkok">(GMT+07:00) Bangkok, Jakarta</option>
          <option value="Asia/Shanghai">(GMT+08:00) Beijing, Singapore, Hong Kong</option>
          <option value="Asia/Tokyo">(GMT+09:00) Tokyo, Seoul</option>
          <option value="Australia/Sydney">(GMT+10:00) Sydney, Melbourne</option>
          <option value="Pacific/Auckland">(GMT+12:00) Auckland, Fiji</option>
        </select>
      </div>

      {/* Date Format */}
      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Date Format</p>
          <p className="settings-item-description">Preferred date display format</p>
        </div>
        <select value={settings.dateFormat || 'MM/DD/YYYY'}
          onChange={(e) => handleUpdate('dateFormat', e.target.value)}
          className="settings-select">
          <option value="MM/DD/YYYY">MM/DD/YYYY</option>
          <option value="DD/MM/YYYY">DD/MM/YYYY</option>
          <option value="YYYY-MM-DD">YYYY-MM-DD</option>
        </select>
      </div>
    </div>
  );

  // ─── Appearance ───
  const renderAppearance = () => (
    <>
      <div className="settings-card">
        <h4 className="settings-card-title">Theme</h4>
        <div className="settings-theme-grid">
          {['light', 'dark', 'system'].map((theme) => (
            <button key={theme} onClick={() => handleUpdate('theme', theme)}
              className={`settings-theme-btn ${settings.theme === theme ? 'settings-theme-btn-active' : ''}`}>
              {theme === 'light' && <FiSun className="settings-theme-icon settings-theme-icon-light" />}
              {theme === 'dark' && <FiMoon className="settings-theme-icon settings-theme-icon-dark" />}
              {theme === 'system' && <FiMonitor className="settings-theme-icon settings-theme-icon-system" />}
              <span className="settings-theme-label">{theme}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="settings-card">
        <h4 className="settings-card-title">Display Options</h4>
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Compact Mode</p>
            <p className="settings-item-description">Reduce spacing and padding</p>
          </div>
          <button onClick={() => handleUpdate('compactMode', !settings.compactMode)}
            className={`settings-toggle ${settings.compactMode ? 'settings-toggle-active' : ''}`}>
            <div className={`settings-toggle-knob ${settings.compactMode ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Animations</p>
            <p className="settings-item-description">Enable UI animations and transitions</p>
          </div>
          <button onClick={() => handleUpdate('animations', !settings.animations)}
            className={`settings-toggle ${settings.animations ? 'settings-toggle-active' : ''}`}>
            <div className={`settings-toggle-knob ${settings.animations ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>
      </div>
    </>
  );

  // ─── Notifications ───
  const renderNotifications = () => (
    <>
      <div className="settings-card">
        <h4 className="settings-card-title">Notification Settings</h4>

        {/* Email */}
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Email Notifications</p>
            <p className="settings-item-description">Receive updates via email</p>
          </div>
          <button onClick={() => handleUpdate('emailNotifications', !settings.emailNotifications)}
            className={`settings-toggle ${settings.emailNotifications ? 'settings-toggle-active' : ''}`}>
            <div className={`settings-toggle-knob ${settings.emailNotifications ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>

        {settings.emailNotifications && (
          <div style={{ padding: '8px 16px 16px' }}>
            <button onClick={handleTestEmail} disabled={testingEmail} style={{
              width: '100%', padding: '10px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '10px', color: '#10b981',
              fontSize: '12px', fontWeight: 600, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}>
              {testingEmail ? <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Sending...</> : <><FiSend /> Send Test Email</>}
            </button>
          </div>
        )}

        {/* Slack */}
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Slack Notifications</p>
            <p className="settings-item-description">Receive updates on Slack</p>
          </div>
          <button onClick={() => handleUpdate('slackNotifications', !settings.slackNotifications)}
            className={`settings-toggle ${settings.slackNotifications ? 'settings-toggle-active' : ''}`}>
            <div className={`settings-toggle-knob ${settings.slackNotifications ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>

        {settings.slackNotifications && (
          <div style={{ padding: '8px 16px 16px' }}>
            <label style={{
              display: 'block', fontSize: '11px',
              color: 'rgba(255,255,255,0.6)', marginBottom: '6px',
            }}>
              Slack Webhook URL
            </label>
            <input type="text" value={slackWebhook}
              onChange={(e) => setSlackWebhook(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              style={{
                width: '100%', padding: '10px 12px',
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                borderRadius: '10px', color: '#fff',
                fontSize: '12px', outline: 'none', marginBottom: '8px',
              }} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleSaveSlackWebhook} style={{
                flex: 1, padding: '9px',
                background: 'rgba(168, 85, 247, 0.15)',
                border: '1px solid rgba(168, 85, 247, 0.3)',
                borderRadius: '8px', color: '#a855f7',
                fontSize: '11px', fontWeight: 600, cursor: 'pointer',
              }}>
                Save Webhook
              </button>
              <button onClick={handleTestSlack}
                disabled={testingSlack || !slackWebhook}
                style={{
                  flex: 1, padding: '9px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '8px', color: '#10b981',
                  fontSize: '11px', fontWeight: 600,
                  cursor: (!slackWebhook || testingSlack) ? 'not-allowed' : 'pointer',
                  opacity: (!slackWebhook || testingSlack) ? 0.5 : 1,
                }}>
                {testingSlack ? 'Sending...' : 'Test Slack'}
              </button>
            </div>
          </div>
        )}

        {/* Alert Severity */}
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Alert Severity</p>
            <p className="settings-item-description">Minimum severity for notifications</p>
          </div>
          <select value={settings.alertSeverity || 'high'}
            onChange={(e) => handleUpdate('alertSeverity', e.target.value)}
            className="settings-select">
            <option value="critical">Critical only</option>
            <option value="high">High + Critical</option>
            <option value="medium">Medium + above</option>
            <option value="low">Low + above</option>
            <option value="info">All</option>
          </select>
        </div>
      </div>

      {/* Info box */}
      <div className="settings-card" style={{ padding: '16px 20px' }}>
        <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', lineHeight: 1.6 }}>
          <strong style={{ color: '#a855f7' }}>💡 Setup Required:</strong>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px' }}>
            <li><strong>Email:</strong> Add <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: '3px' }}>SMTP_USER</code> + <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: '3px' }}>SMTP_PASSWORD</code> (Gmail app password) to backend <code>.env</code></li>
            <li><strong>Slack:</strong> Create webhook at <a href="https://api.slack.com/apps" target="_blank" rel="noreferrer" style={{ color: '#a855f7' }}>api.slack.com/apps</a> → Incoming Webhooks</li>
          </ul>
        </div>
      </div>
    </>
  );

  // ─── Security ───
  const renderSecurity = () => (
    <>
      <div className="settings-card">
        <h4 className="settings-card-title">Security Settings</h4>
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Session Timeout</p>
            <p className="settings-item-description">Auto-logout after inactivity</p>
          </div>
          <select value={settings.sessionTimeout || 30}
            onChange={(e) => handleUpdate('sessionTimeout', parseInt(e.target.value))}
            className="settings-select">
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={60}>1 hour</option>
            <option value={120}>2 hours</option>
            <option value={240}>4 hours</option>
          </select>
        </div>
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Password Expiry</p>
            <p className="settings-item-description">Days before password expires</p>
          </div>
          <select value={settings.passwordExpiry || 90}
            onChange={(e) => handleUpdate('passwordExpiry', parseInt(e.target.value))}
            className="settings-select">
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
          </select>
        </div>

        {user?.password_expired && (
          <div style={{
            margin: '12px 16px', padding: '12px 14px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: '10px', fontSize: '12px',
            color: '#f87171', display: 'flex',
            alignItems: 'center', gap: '10px',
          }}>
            <FiAlertCircle />
            <span>Your password has expired ({user.password_age_days} days old). Please change it.</span>
          </div>
        )}
      </div>

      <button onClick={() => setShowChangePassword(true)}
        className="settings-audit-btn" style={{ marginBottom: '12px' }}>
        <div className="settings-audit-btn-left">
          <div className="settings-audit-btn-icon"><FiLock className="w-5 h-5" /></div>
          <div>
            <p className="settings-audit-btn-title">Change Password</p>
            <p className="settings-audit-btn-description">
              {user?.password_age_days !== null && user?.password_age_days !== undefined
                ? `Last changed ${user.password_age_days} days ago`
                : 'Update your account password'}
            </p>
          </div>
        </div>
        <FiChevronRight className="settings-audit-btn-arrow" />
      </button>

      <button onClick={() => setShowAuditLogs(!showAuditLogs)} className="settings-audit-btn">
        <div className="settings-audit-btn-left">
          <div className="settings-audit-btn-icon"><FiShield className="w-5 h-5" /></div>
          <div>
            <p className="settings-audit-btn-title">Audit Logs</p>
            <p className="settings-audit-btn-description">View system activity logs</p>
          </div>
        </div>
        <FiChevronRight className="settings-audit-btn-arrow" />
      </button>

      <AnimatePresence>
        {showAuditLogs && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="settings-audit-panel"
          >
            <AuditLogs onClose={() => setShowAuditLogs(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );

  // ─── Integrations ───
  const renderIntegrations = () => (
    <div className="settings-card">
      <h4 className="settings-card-title">Connected Services</h4>

      <div className="settings-integration">
        <div className="settings-integration-left">
          <FaGithub className="settings-integration-icon" style={{ fontSize: '22px', color: '#fff' }} />
          <div className="settings-integration-info">
            <p className="settings-integration-name">GitHub</p>
            <p className="settings-integration-status">
              {githubConnected ? (
                <span style={{ color: '#10b981' }}>✓ Connected ({user.tokens.github})</span>
              ) : (
                'Not connected — connect to deploy from your repos'
              )}
            </p>
          </div>
        </div>
        {githubConnected ? (
          <button onClick={handleGitHubDisconnect} disabled={disconnecting}
            className="settings-integration-btn settings-integration-btn-disconnect">
            {disconnecting ? 'Disconnecting...' : 'Disconnect'}
          </button>
        ) : (
          <button onClick={() => setShowGitHubConnect(true)}
            className="settings-integration-btn settings-integration-btn-connect">
            Connect
          </button>
        )}
      </div>

      <div style={{
        marginTop: '16px', padding: '12px 14px',
        background: 'rgba(168, 85, 247, 0.05)',
        border: '1px solid rgba(168, 85, 247, 0.15)',
        borderRadius: '10px', fontSize: '11px',
        color: 'rgba(255,255,255,0.6)', lineHeight: 1.6,
      }}>
        <strong style={{ color: '#a855f7' }}>💡 GitHub integration enables:</strong>
        <ul style={{ margin: '6px 0 0 0', paddingLeft: '18px' }}>
          <li>Automatic deploy from private repositories</li>
          <li>Auto-fix + PR creation on your repos</li>
          <li>Security scanning with repo access</li>
        </ul>
      </div>
    </div>
  );

  // ─── About ───
  const renderAbout = () => (
    <>
      <div className="settings-card">
        <div className="settings-about-logo"><FaRobot /></div>
        <h3 className="settings-about-title">Smart DevOps Assistant</h3>
        <p className="settings-about-subtitle">AI-Powered DevOps Automation</p>
        <div className="settings-about-stats">
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">Version</p>
            <p className="settings-about-stat-value">{APP_VERSION}</p>
          </div>
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">Status</p>
            <p className="settings-about-stat-value settings-about-stat-value-success">✓ Operational</p>
          </div>
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">User</p>
            <p className="settings-about-stat-value">{user?.name || 'Unknown'}</p>
          </div>
        </div>
        <hr className="settings-about-divider" />
        <p className="settings-about-copyright">© 2026 Smart DevOps Assistant. All rights reserved.</p>
      </div>

      <div className="settings-card">
        <h4 className="settings-card-title">System Information</h4>
        <div className="settings-system-info">
          <div className="settings-system-item">
            <span className="settings-system-item-label">Account</span>
            <span className="settings-system-item-value">{user?.email || 'N/A'}</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">Role</span>
            <span className="settings-system-item-value">{user?.role || 'user'}</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">Backend</span>
            <span className="settings-system-item-value">Flask + MongoDB</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">AI Model</span>
            <span className="settings-system-item-value">Groq GPT-OSS 120B</span>
          </div>
        </div>
      </div>
    </>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'general': return renderGeneral();
      case 'appearance': return renderAppearance();
      case 'notifications': return renderNotifications();
      case 'security': return renderSecurity();
      case 'integrations': return renderIntegrations();
      case 'about': return renderAbout();
      default: return renderGeneral();
    }
  };

  if (settingsLoading) {
    return (
      <div className="settings-container">
        <div style={{ padding: '60px', textAlign: 'center', color: 'rgba(255,255,255,0.5)' }}>
          <FiLoader style={{ animation: 'spin 1s linear infinite', fontSize: '24px' }} />
          <p style={{ marginTop: '12px', fontSize: '13px' }}>Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <div>
          <h2 className="settings-header-title">
            <FiSettings className="settings-header-title-icon" />
            Settings
          </h2>
          <p className="settings-header-subtitle">Configure your application preferences</p>
        </div>
      </div>

      <div className="settings-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`settings-tab-btn ${activeTab === tab.id ? 'settings-tab-btn-active' : ''}`}>
              <Icon className="settings-tab-icon" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="settings-content">
          {renderContent()}
        </motion.div>
      </AnimatePresence>

      <div className="settings-version-info">
        Smart DevOps Assistant {APP_VERSION} • {user?.email || ''}
      </div>

      <ChangePasswordModal isOpen={showChangePassword} onClose={() => setShowChangePassword(false)} />
      <GitHubConnectModal
        isOpen={showGitHubConnect}
        onClose={() => setShowGitHubConnect(false)}
        onConnected={handleGitHubConnected}
      />

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Settings;