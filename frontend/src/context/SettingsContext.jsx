import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const SettingsContext = createContext();

export const useSettings = () => {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
};

const DEFAULT_SETTINGS = {
  language: 'en',
  timezone: 'UTC',
  dateFormat: 'MM/DD/YYYY',
  theme: 'dark',
  compactMode: false,
  animations: true,
  emailNotifications: true,
  slackNotifications: false,
  alertSeverity: 'high',
  sessionTimeout: 30,
  passwordExpiry: 90,
};

// ═══════════════════════════════════════════════════════════
// ⭐ GLOBAL TIMEZONE + DATE FORMAT PATCH
// ═══════════════════════════════════════════════════════════
// This patches Date.prototype methods GLOBALLY so every component
// (LiveLogs, Dashboard, Pipelines, Monitoring, AIAssistant, etc.)
// automatically displays times in the user's selected timezone
// and date format — WITHOUT needing to modify each component.
// ═══════════════════════════════════════════════════════════

const _originalToLocaleTimeString = Date.prototype.toLocaleTimeString;
const _originalToLocaleDateString = Date.prototype.toLocaleDateString;
const _originalToLocaleString = Date.prototype.toLocaleString;

function _getUserTimezone() {
  if (typeof window !== 'undefined' && window.__USER_TIMEZONE__) {
    return window.__USER_TIMEZONE__;
  }
  return 'UTC';
}

function _getUserDateFormat() {
  if (typeof window !== 'undefined' && window.__USER_DATE_FORMAT__) {
    return window.__USER_DATE_FORMAT__;
  }
  return 'MM/DD/YYYY';
}

function _formatDateWithUserFormat(date) {
  const tz = _getUserTimezone();
  const fmt = _getUserDateFormat();

  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: tz,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(date);

    const get = (type) => parts.find(p => p.type === type)?.value || '';
    const month = get('month');
    const day = get('day');
    const year = get('year');

    switch (fmt) {
      case 'DD/MM/YYYY': return `${day}/${month}/${year}`;
      case 'YYYY-MM-DD': return `${year}-${month}-${day}`;
      case 'MM/DD/YYYY':
      default: return `${month}/${day}/${year}`;
    }
  } catch (e) {
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
  }
}

// ⭐ Patch toLocaleTimeString
Date.prototype.toLocaleTimeString = function (locales, options) {
  try {
    const tz = _getUserTimezone();
    const mergedOptions = { ...(options || {}), timeZone: tz };
    return _originalToLocaleTimeString.call(this, locales || 'en-US', mergedOptions);
  } catch (e) {
    return _originalToLocaleTimeString.call(this, locales, options);
  }
};

// ⭐ Patch toLocaleDateString
Date.prototype.toLocaleDateString = function (locales, options) {
  try {
    // If user has custom format selected, use it (unless caller passed explicit options)
    if (!options || Object.keys(options).length === 0) {
      return _formatDateWithUserFormat(this);
    }
    const tz = _getUserTimezone();
    const mergedOptions = { ...options, timeZone: tz };
    return _originalToLocaleDateString.call(this, locales || 'en-US', mergedOptions);
  } catch (e) {
    return _originalToLocaleDateString.call(this, locales, options);
  }
};

// ⭐ Patch toLocaleString (combined date + time)
Date.prototype.toLocaleString = function (locales, options) {
  try {
    const tz = _getUserTimezone();
    const mergedOptions = { ...(options || {}), timeZone: tz };
    return _originalToLocaleString.call(this, locales || 'en-US', mergedOptions);
  } catch (e) {
    return _originalToLocaleString.call(this, locales, options);
  }
};

// ⭐ Patch toTimeString (raw time)
const _originalToTimeString = Date.prototype.toTimeString;
Date.prototype.toTimeString = function () {
  try {
    const tz = _getUserTimezone();
    return this.toLocaleTimeString('en-US', {
      timeZone: tz,
      hour12: false,
    });
  } catch (e) {
    return _originalToTimeString.call(this);
  }
};

// ═══════════════════════════════════════════════════════════
// SettingsProvider
// ═══════════════════════════════════════════════════════════

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Load on mount
  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const r = await axios.get('/api/auth/settings');
        if (!mounted) return;
        if (r.data.success && r.data.settings) {
          setSettings({ ...DEFAULT_SETTINGS, ...r.data.settings });
        }
      } catch {
        if (mounted) setSettings(DEFAULT_SETTINGS);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  // ⭐ Apply THEME
  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === 'dark') {
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
    } else if (settings.theme === 'light') {
      root.classList.remove('dark');
      root.setAttribute('data-theme', 'light');
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  }, [settings.theme]);

  // ⭐ Apply COMPACT MODE globally
  useEffect(() => {
    const root = document.documentElement;
    if (settings.compactMode) {
      root.classList.add('compact-mode');
    } else {
      root.classList.remove('compact-mode');
    }
  }, [settings.compactMode]);

  // ⭐ Apply ANIMATIONS
  useEffect(() => {
    const root = document.documentElement;
    if (settings.animations === false) {
      root.classList.add('no-animations');
    } else {
      root.classList.remove('no-animations');
    }
  }, [settings.animations]);

  // ⭐ Apply TIMEZONE + DATE FORMAT globally
  // Every Date.toString() / toLocaleTimeString() call will now
  // respect the user's chosen timezone and date format.
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const tz = settings.timezone || 'UTC';
    const fmt = settings.dateFormat || 'MM/DD/YYYY';

    window.__USER_TIMEZONE__ = tz;
    window.__USER_DATE_FORMAT__ = fmt;

    // Force a re-render of listening components
    try {
      window.dispatchEvent(new CustomEvent('settingsTimezoneChanged', {
        detail: { timezone: tz, dateFormat: fmt },
      }));
    } catch (_) {}
  }, [settings.timezone, settings.dateFormat]);

  const updateSetting = useCallback(async (key, value) => {
    const previous = settings;
    const updated = { ...settings, [key]: value };
    setSettings(updated);
    setSaving(true);

    try {
      const r = await axios.put('/api/auth/settings', updated);
      if (!r.data.success) throw new Error(r.data.error);
      return { success: true };
    } catch (e) {
      setSettings(previous);
      toast.error(e.response?.data?.error || 'Failed to save');
      return { success: false };
    } finally {
      setSaving(false);
    }
  }, [settings]);

  const updateMultiple = useCallback(async (patch) => {
    const previous = settings;
    const updated = { ...settings, ...patch };
    setSettings(updated);
    setSaving(true);
    try {
      const r = await axios.put('/api/auth/settings', updated);
      if (!r.data.success) throw new Error(r.data.error);
      return { success: true };
    } catch {
      setSettings(previous);
      toast.error('Failed to save');
      return { success: false };
    } finally {
      setSaving(false);
    }
  }, [settings]);

  const resetSettings = useCallback(async () => {
    setSettings(DEFAULT_SETTINGS);
    try {
      await axios.put('/api/auth/settings', DEFAULT_SETTINGS);
      toast.success('Settings reset');
    } catch {
      toast.error('Failed to reset');
    }
  }, []);

  const reloadSettings = useCallback(async () => {
    try {
      const r = await axios.get('/api/auth/settings');
      if (r.data.success) setSettings({ ...DEFAULT_SETTINGS, ...r.data.settings });
    } catch {}
  }, []);

  const value = {
    settings, loading, saving,
    updateSetting, updateMultiple, resetSettings, reloadSettings,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export default SettingsContext;