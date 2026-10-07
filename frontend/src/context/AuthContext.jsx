import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const AuthContext = createContext();

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  axios.defaults.withCredentials = true;
  axios.defaults.baseURL = API_URL;

  // Auto-refresh on 401
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (r) => r,
      async (error) => {
        const original = error.config;
        if (error.response?.status === 401 && !original._retry && !original.url?.includes('/auth/')) {
          original._retry = true;
          try {
            await axios.post('/api/auth/refresh');
            return axios(original);
          } catch {
            setUser(null);
            return Promise.reject(error);
          }
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  // Initial load
  useEffect(() => {
    (async () => {
      try {
        const status = await axios.get('/api/auth/setup-status');
        if (status.data.needs_setup) {
          setNeedsSetup(true);
          setLoading(false);
          return;
        }
        try {
          const me = await axios.get('/api/auth/me');
          setUser(me.data);
        } catch {
          setUser(null);
        }
      } catch (e) {
        console.error('Auth init error:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const r = await axios.post('/api/auth/login', { email, password });
      setUser(r.data.user);
      toast.success(`Welcome back, ${r.data.user.name}! 🎉`);
      return { success: true };
    } catch (e) {
      const msg = e.response?.data?.error || 'Login failed';
      const remaining = e.response?.data?.attempts_remaining;
      toast.error(remaining !== undefined ? `${msg} (${remaining} left)` : msg);
      return { success: false, error: msg };
    }
  }, []);

  const setup = useCallback(async (name, email, password) => {
    try {
      const r = await axios.post('/api/auth/setup', { name, email, password });
      setUser(r.data.user);
      setNeedsSetup(false);
      toast.success('Setup complete! 🎉');
      return { success: true };
    } catch (e) {
      const msg = e.response?.data?.error || 'Setup failed';
      toast.error(msg);
      return { success: false, error: msg };
    }
  }, []);

  const logout = useCallback(async () => {
    try { await axios.post('/api/auth/logout'); } catch {}
    setUser(null);
    toast.success('Logged out');
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const me = await axios.get('/api/auth/me');
      setUser(me.data);
      return me.data;
    } catch { return null; }
  }, []);

  const value = {
    user, loading, needsSetup,
    login, setup, logout, refreshUser,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;