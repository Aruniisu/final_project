import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/main.css';
import './Settings.css';
import {
  FiSettings,
  FiUser,
  FiShield,
  FiGlobe,
  FiBell,
  FiLock,
  FiMail,
  FiKey,
  FiDatabase,
  FiServer,
  FiLink,
  FiRefreshCw,
  FiCheckCircle,
  FiAlertCircle,
  FiChevronRight,
  FiMoon,
  FiSun,
  FiMonitor,
  FiZap,
} from 'react-icons/fi';
import { FaGithub, FaGoogle, FaAws, FaDocker, FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';
import AuditLogs from './AuditLogs';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('general');
  const [showAuditLogs, setShowAuditLogs] = useState(false);
  const [settings, setSettings] = useState({
    // General
    language: 'en',
    timezone: 'UTC',
    dateFormat: 'MM/DD/YYYY',
    // Appearance
    theme: 'light',
    compactMode: false,
    animations: true,
    // Notifications
    emailNotifications: true,
    slackNotifications: false,
    alertSeverity: 'high',
    // Security
    twoFactorAuth: false,
    sessionTimeout: 30,
    passwordExpiry: 90,
    // Integrations
    github: { connected: true, repo: 'org/devops-assistant' },
    google: { connected: false },
    aws: { connected: true, region: 'us-west-2' },
    docker: { connected: false },
  });

  const tabs = [
    { id: 'general', label: 'General', icon: FiSettings },
    { id: 'appearance', label: 'Appearance', icon: FiMonitor },
    { id: 'notifications', label: 'Notifications', icon: FiBell },
    { id: 'security', label: 'Security', icon: FiShield },
    { id: 'integrations', label: 'Integrations', icon: FiLink },
    { id: 'about', label: 'About', icon: FiZap },
  ];

  const handleSettingChange = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
    toast.success('Setting updated');
  };

  // ============================================
  // RENDER FUNCTIONS
  // ============================================
  const renderGeneral = () => (
    <div className="settings-card">
      <h4 className="settings-card-title">General Settings</h4>
      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Language</p>
          <p className="settings-item-description">Choose your preferred language</p>
        </div>
        <select
          value={settings.language}
          onChange={(e) => handleSettingChange('language', e.target.value)}
          className="settings-select"
        >
          <option value="en">English</option>
          <option value="es">Español</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
          <option value="ja">日本語</option>
        </select>
      </div>

      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Timezone</p>
          <p className="settings-item-description">Your current timezone</p>
        </div>
        <select
          value={settings.timezone}
          onChange={(e) => handleSettingChange('timezone', e.target.value)}
          className="settings-select"
        >
          <option value="UTC">UTC</option>
          <option value="EST">EST</option>
          <option value="PST">PST</option>
          <option value="GMT">GMT</option>
          <option value="IST">IST</option>
        </select>
      </div>

      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Date Format</p>
          <p className="settings-item-description">Preferred date display format</p>
        </div>
        <select
          value={settings.dateFormat}
          onChange={(e) => handleSettingChange('dateFormat', e.target.value)}
          className="settings-select"
        >
          <option value="MM/DD/YYYY">MM/DD/YYYY</option>
          <option value="DD/MM/YYYY">DD/MM/YYYY</option>
          <option value="YYYY-MM-DD">YYYY-MM-DD</option>
        </select>
      </div>
    </div>
  );

  const renderAppearance = () => (
    <>
      <div className="settings-card">
        <h4 className="settings-card-title">Theme</h4>
        <div className="settings-theme-grid">
          {['light', 'dark', 'system'].map((theme) => (
            <button
              key={theme}
              onClick={() => handleSettingChange('theme', theme)}
              className={`settings-theme-btn ${settings.theme === theme ? 'settings-theme-btn-active' : ''}`}
            >
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
          <button
            onClick={() => handleSettingChange('compactMode', !settings.compactMode)}
            className={`settings-toggle ${settings.compactMode ? 'settings-toggle-active' : ''}`}
          >
            <div className={`settings-toggle-knob ${settings.compactMode ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>

        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Animations</p>
            <p className="settings-item-description">Enable UI animations and transitions</p>
          </div>
          <button
            onClick={() => handleSettingChange('animations', !settings.animations)}
            className={`settings-toggle ${settings.animations ? 'settings-toggle-active' : ''}`}
          >
            <div className={`settings-toggle-knob ${settings.animations ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>
      </div>
    </>
  );

  const renderNotifications = () => (
    <div className="settings-card">
      <h4 className="settings-card-title">Notification Settings</h4>
      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Email Notifications</p>
          <p className="settings-item-description">Receive updates via email</p>
        </div>
        <button
          onClick={() => handleSettingChange('emailNotifications', !settings.emailNotifications)}
          className={`settings-toggle ${settings.emailNotifications ? 'settings-toggle-active' : ''}`}
        >
          <div className={`settings-toggle-knob ${settings.emailNotifications ? 'settings-toggle-knob-active' : ''}`} />
        </button>
      </div>

      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Slack Notifications</p>
          <p className="settings-item-description">Receive updates on Slack</p>
        </div>
        <button
          onClick={() => handleSettingChange('slackNotifications', !settings.slackNotifications)}
          className={`settings-toggle ${settings.slackNotifications ? 'settings-toggle-active' : ''}`}
        >
          <div className={`settings-toggle-knob ${settings.slackNotifications ? 'settings-toggle-knob-active' : ''}`} />
        </button>
      </div>

      <div className="settings-item">
        <div className="settings-item-left">
          <p className="settings-item-label">Alert Severity</p>
          <p className="settings-item-description">Minimum severity for notifications</p>
        </div>
        <select
          value={settings.alertSeverity}
          onChange={(e) => handleSettingChange('alertSeverity', e.target.value)}
          className="settings-select"
        >
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
      </div>
    </div>
  );

  const renderSecurity = () => (
    <>
      <div className="settings-card">
        <h4 className="settings-card-title">Security Settings</h4>
        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Two-Factor Authentication</p>
            <p className="settings-item-description">Extra layer of security</p>
          </div>
          <button
            onClick={() => handleSettingChange('twoFactorAuth', !settings.twoFactorAuth)}
            className={`settings-toggle ${settings.twoFactorAuth ? 'settings-toggle-active' : ''}`}
          >
            <div className={`settings-toggle-knob ${settings.twoFactorAuth ? 'settings-toggle-knob-active' : ''}`} />
          </button>
        </div>

        <div className="settings-item">
          <div className="settings-item-left">
            <p className="settings-item-label">Session Timeout</p>
            <p className="settings-item-description">Auto-logout after inactivity</p>
          </div>
          <select
            value={settings.sessionTimeout}
            onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
            className="settings-select"
          >
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
          <select
            value={settings.passwordExpiry}
            onChange={(e) => handleSettingChange('passwordExpiry', parseInt(e.target.value))}
            className="settings-select"
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
          </select>
        </div>
      </div>

      <button        onClick={() => setShowAuditLogs(!showAuditLogs)}
        className="settings-audit-btn"
      >
        <div className="settings-audit-btn-left">
          <div className="settings-audit-btn-icon">
            <FiLock className="w-5 h-5" />
          </div>
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

  const renderIntegrations = () => (
    <div className="settings-card">
      <h4 className="settings-card-title">Connected Services</h4>
      
      <div className="settings-integration">
        <div className="settings-integration-left">
          <FaGithub className="settings-integration-icon" />
          <div className="settings-integration-info">
            <p className="settings-integration-name">GitHub</p>
            <p className="settings-integration-status">
              {settings.github.connected ? `Connected: ${settings.github.repo}` : 'Not connected'}
            </p>
          </div>
        </div>
        <button
          onClick={() => toast.info(settings.github.connected ? 'Disconnecting...' : 'Connecting...')}
          className={`settings-integration-btn ${
            settings.github.connected ? 'settings-integration-btn-disconnect' : 'settings-integration-btn-connect'
          }`}
        >
          {settings.github.connected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      <div className="settings-integration">
        <div className="settings-integration-left">
          <FaGoogle className="settings-integration-icon" />
          <div className="settings-integration-info">
            <p className="settings-integration-name">Google Drive</p>
            <p className="settings-integration-status">
              {settings.google.connected ? 'Connected' : 'Not connected'}
            </p>
          </div>
        </div>
        <button
          onClick={() => toast.info('Connecting to Google Drive...')}
          className={`settings-integration-btn ${
            settings.google.connected ? 'settings-integration-btn-disconnect' : 'settings-integration-btn-connect'
          }`}
        >
          {settings.google.connected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      <div className="settings-integration">
        <div className="settings-integration-left">
          <FaAws className="settings-integration-icon" />
          <div className="settings-integration-info">
            <p className="settings-integration-name">AWS</p>
            <p className="settings-integration-status">
              {settings.aws.connected ? `Connected: ${settings.aws.region}` : 'Not connected'}
            </p>
          </div>
        </div>
        <button
          onClick={() => toast.info(settings.aws.connected ? 'Disconnecting...' : 'Connecting...')}
          className={`settings-integration-btn ${
            settings.aws.connected ? 'settings-integration-btn-disconnect' : 'settings-integration-btn-connect'
          }`}
        >
          {settings.aws.connected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      <div className="settings-integration">
        <div className="settings-integration-left">
          <FaDocker className="settings-integration-icon" />
          <div className="settings-integration-info">
            <p className="settings-integration-name">Docker Hub</p>
            <p className="settings-integration-status">
              {settings.docker.connected ? 'Connected' : 'Not connected'}
            </p>
          </div>
        </div>
        <button
          onClick={() => toast.info('Connecting to Docker Hub...')}
          className={`settings-integration-btn ${
            settings.docker.connected ? 'settings-integration-btn-disconnect' : 'settings-integration-btn-connect'
          }`}
        >
          {settings.docker.connected ? 'Disconnect' : 'Connect'}
        </button>
      </div>
    </div>
  );

  const renderAbout = () => (
    <>
      <div className="settings-card">
        <div className="settings-about-logo">
          <FaRobot />
        </div>
        <h3 className="settings-about-title">Smart DevOps Assistant</h3>
        <p className="settings-about-subtitle">AI-Powered DevOps Automation</p>
        <div className="settings-about-stats">
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">Version</p>
            <p className="settings-about-stat-value">v2.3.1</p>
          </div>
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">Auto-Upgrade</p>
            <p className="settings-about-stat-value settings-about-stat-value-success">✓ Enabled</p>
          </div>
          <div className="settings-about-stat">
            <p className="settings-about-stat-label">Status</p>
            <p className="settings-about-stat-value settings-about-stat-value-success">Operational</p>
          </div>
        </div>
        <hr className="settings-about-divider" />
        <p className="settings-about-copyright">
          © 2024 Smart DevOps Assistant. All rights reserved.
        </p>
      </div>

      <div className="settings-card">
        <h4 className="settings-card-title">System Information</h4>
        <div className="settings-system-info">
          <div className="settings-system-item">
            <span className="settings-system-item-label">Node Version</span>
            <span className="settings-system-item-value">v18.17.0</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">Python Version</span>
            <span className="settings-system-item-value">3.11.4</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">Database</span>
            <span className="settings-system-item-value">MongoDB 6.0</span>
          </div>
          <div className="settings-system-item">
            <span className="settings-system-item-label">AI Models</span>
            <span className="settings-system-item-value">5 active</span>
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

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="settings-container">
      {/* Header */}
      <div className="settings-header">
        <div>
          <h2 className="settings-header-title">
            <FiSettings className="settings-header-title-icon" />
            Settings
          </h2>
          <p className="settings-header-subtitle">
            Configure your application preferences
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="settings-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`settings-tab-btn ${activeTab === tab.id ? 'settings-tab-btn-active' : ''}`}
            >
              <Icon className="settings-tab-icon" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="settings-content"
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>

      {/* Version Info - Same as Dashboard */}
      <div className="settings-version-info">
        Smart DevOps Assistant v2.3.1 • Auto-upgrade enabled • {new Date().getFullYear()}
      </div>
    </div>
  );
};

export default Settings;