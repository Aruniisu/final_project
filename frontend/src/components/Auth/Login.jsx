import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { FaRobot, FaGithub, FaGoogle } from 'react-icons/fa';
import {
  FiLock, FiMail, FiEye, FiEyeOff, FiLoader, FiUser,
  FiCheck, FiX, FiZap, FiShield, FiActivity,
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// ═══════════════════════════════════════════════════════════
// Premium Background with animated elements
// ═══════════════════════════════════════════════════════════
const PremiumBackground = () => (
  <>
    {/* Animated gradient orbs */}
    <motion.div
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.15, 0.25, 0.15],
      }}
      transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
      style={{
        position: 'absolute',
        width: '600px', height: '600px',
        background: 'radial-gradient(circle, rgba(168,85,247,0.5), transparent 70%)',
        top: '-200px', left: '-200px',
        filter: 'blur(80px)',
        pointerEvents: 'none',
      }}
    />
    <motion.div
      animate={{
        scale: [1, 1.3, 1],
        opacity: [0.15, 0.25, 0.15],
      }}
      transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
      style={{
        position: 'absolute',
        width: '500px', height: '500px',
        background: 'radial-gradient(circle, rgba(99,102,241,0.5), transparent 70%)',
        bottom: '-150px', right: '-150px',
        filter: 'blur(80px)',
        pointerEvents: 'none',
      }}
    />
    <motion.div
      animate={{
        scale: [1, 1.1, 1],
        opacity: [0.08, 0.15, 0.08],
      }}
      transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut', delay: 4 }}
      style={{
        position: 'absolute',
        width: '400px', height: '400px',
        background: 'radial-gradient(circle, rgba(236,72,153,0.4), transparent 70%)',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        filter: 'blur(80px)',
        pointerEvents: 'none',
      }}
    />

    {/* Grid pattern */}
    <div style={{
      position: 'absolute', inset: 0,
      backgroundImage: `
        linear-gradient(rgba(168,85,247,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(168,85,247,0.03) 1px, transparent 1px)
      `,
      backgroundSize: '60px 60px',
      pointerEvents: 'none',
    }} />

    {/* Floating dots */}
    {[...Array(20)].map((_, i) => (
      <motion.div
        key={i}
        animate={{
          y: [0, -30, 0],
          opacity: [0.1, 0.4, 0.1],
        }}
        transition={{
          duration: 4 + Math.random() * 4,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: Math.random() * 3,
        }}
        style={{
          position: 'absolute',
          width: '3px', height: '3px',
          borderRadius: '50%',
          background: '#a855f7',
          top: `${Math.random() * 100}%`,
          left: `${Math.random() * 100}%`,
          pointerEvents: 'none',
        }}
      />
    ))}
  </>
);

// ═══════════════════════════════════════════════════════════
// Left-side Illustration Panel
// ═══════════════════════════════════════════════════════════
const IllustrationPanel = () => {
  const features = [
    { icon: FiZap, label: 'Autonomous Deployment', color: '#a855f7' },
    { icon: FiShield, label: 'AI Security Scanning', color: '#10b981' },
    { icon: FiActivity, label: 'Real-time Monitoring', color: '#3b82f6' },
  ];

  return (
    <div style={{
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      height: '100%',
      overflow: 'hidden',
    }}>
      {/* Central robot illustration with orbit rings */}
      <div style={{ position: 'relative', marginBottom: '40px' }}>
        {/* Orbit rings */}
        {[1, 2, 3].map((ring) => (
          <motion.div
            key={ring}
            animate={{ rotate: 360 }}
            transition={{
              duration: 20 + ring * 5,
              repeat: Infinity,
              ease: 'linear',
            }}
            style={{
              position: 'absolute',
              top: '50%', left: '50%',
              width: `${180 + ring * 80}px`,
              height: `${180 + ring * 80}px`,
              marginLeft: `-${(180 + ring * 80) / 2}px`,
              marginTop: `-${(180 + ring * 80) / 2}px`,
              border: `1px dashed rgba(168,85,247,${0.15 - ring * 0.03})`,
              borderRadius: '50%',
              pointerEvents: 'none',
            }}
          />
        ))}

        {/* Orbiting dots */}
        {[0, 1, 2, 3].map((i) => (
          <motion.div
            key={i}
            animate={{ rotate: 360 }}
            transition={{
              duration: 12 + i * 2,
              repeat: Infinity,
              ease: 'linear',
            }}
            style={{
              position: 'absolute',
              top: '50%', left: '50%',
              width: '320px', height: '320px',
              marginLeft: '-160px', marginTop: '-160px',
              pointerEvents: 'none',
            }}
          >
            <div style={{
              position: 'absolute',
              top: 0, left: '50%',
              width: '8px', height: '8px',
              marginLeft: '-4px',
              borderRadius: '50%',
              background: ['#a855f7', '#10b981', '#3b82f6', '#ec4899'][i],
              boxShadow: `0 0 12px ${['#a855f7', '#10b981', '#3b82f6', '#ec4899'][i]}`,
            }} />
          </motion.div>
        ))}

        {/* Central logo */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.8, type: 'spring', bounce: 0.5 }}
          style={{
            width: '140px', height: '140px',
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            borderRadius: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 20px 60px rgba(168,85,247,0.5), 0 0 0 1px rgba(168,85,247,0.3)',
            position: 'relative',
            zIndex: 1,
          }}
        >
          <FaRobot style={{ fontSize: '68px', color: '#fff' }} />
        </motion.div>
      </div>

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        style={{
          fontSize: '32px',
          fontWeight: 800,
          color: '#fff',
          margin: '0 0 12px 0',
          letterSpacing: '-0.5px',
          textAlign: 'center',
        }}
      >
        Smart DevOps
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        style={{
          fontSize: '14px',
          color: 'rgba(255,255,255,0.6)',
          margin: '0 0 40px 0',
          textAlign: 'center',
          maxWidth: '400px',
          lineHeight: 1.6,
        }}
      >
        Autonomous AI-powered DevOps platform with multi-agent architecture
      </motion.p>

      {/* Feature pills */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '340px' }}>
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 + i * 0.1 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              padding: '12px 16px',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid rgba(148, 163, 184, 0.1)',
              borderRadius: '12px',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div style={{
              width: '36px', height: '36px',
              borderRadius: '10px',
              background: `${f.color}20`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <f.icon style={{ color: f.color, fontSize: '18px' }} />
            </div>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.8)', fontWeight: 500 }}>
              {f.label}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// Password strength indicator
// ═══════════════════════════════════════════════════════════
const PasswordStrength = ({ password }) => {
  const checks = {
    length: password.length >= 12,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    symbol: /[^A-Za-z0-9]/.test(password),
  };
  const score = Object.values(checks).filter(Boolean).length;

  const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981'];

  if (!password) return null;

  return (
    <div style={{ marginTop: '10px' }}>
      <div style={{ display: 'flex', gap: '4px', marginBottom: '6px' }}>
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              flex: 1, height: '3px', borderRadius: '2px',
              background: i < score ? colors[score - 1] : 'rgba(148,163,184,0.15)',
              transition: 'all 0.3s ease',
            }}
          />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
        <span style={{ color: colors[Math.max(0, score - 1)] }}>
          {labels[Math.max(0, score - 1)]}
        </span>
        <span style={{ color: 'rgba(255,255,255,0.4)' }}>{score}/5</span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// Main Login Component
// ═══════════════════════════════════════════════════════════
const Login = () => {
  const { login, setup } = useAuth();
  const [mode, setMode] = useState('signin'); // 'signin' | 'signup'
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(null);

  // Sign In fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);

  // Sign Up fields
  const [suName, setSuName] = useState('');
  const [suEmail, setSuEmail] = useState('');
  const [suPassword, setSuPassword] = useState('');
  const [suConfirm, setSuConfirm] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);

  // Error handling from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const error = params.get('error');
    const oauth = params.get('oauth');

    if (oauth) {
      toast.success(`${oauth.replace('_', ' ')}! 🎉`);
      window.history.replaceState({}, '', '/login');
    }

    if (error) {
      const messages = {
        github_access_denied: 'GitHub login cancelled',
        google_access_denied: 'Google login cancelled',
        no_email: 'No email found in OAuth account',
        no_account_matching_email: 'No account with that email. Please sign up.',
        invalid_state: 'Invalid OAuth state — try again',
        oauth_not_configured: 'OAuth not configured yet',
        server_error: 'Server error during login',
        create_failed: 'Failed to create account',
        missing_params: 'Missing OAuth parameters',
      };
      toast.error(messages[error] || `Login error: ${error}`, { duration: 6000 });
      window.history.replaceState({}, '', '/login');
    }
  }, []);

  const handleSignIn = async (e) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    await login(email, password);
    setLoading(false);
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    if (!suName || !suEmail || !suPassword) return toast.error('All fields required');
    if (suPassword.length < 12) return toast.error('Password must be 12+ characters');
    if (suPassword !== suConfirm) return toast.error('Passwords do not match');
    if (!agreeTerms) return toast.error('Please agree to terms');

    setLoading(true);
    try {
      const r = await axios.post('/api/auth/register', {
        name: suName.trim(),
        email: suEmail.trim().toLowerCase(),
        password: suPassword,
      });
      if (r.data.success) {
        toast.success('Account created! 🎉');
        window.location.href = '/dashboard';
      } else {
        toast.error(r.data.error || 'Registration failed');
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = (provider) => {
    setOauthLoading(provider);
    window.location.href = `${API_URL}/api/auth/oauth/${provider}/start`;
  };

  const inputBase = {
    width: '100%',
    padding: '13px 42px 13px 44px',
    background: 'rgba(15, 23, 42, 0.5)',
    border: '1px solid rgba(148, 163, 184, 0.15)',
    borderRadius: '12px',
    color: '#fff',
    fontSize: '14px',
    outline: 'none',
    transition: 'all 0.2s ease',
  };

  const inputFocus = (e) => {
    e.target.style.borderColor = 'rgba(168,85,247,0.5)';
    e.target.style.background = 'rgba(15, 23, 42, 0.7)';
    e.target.style.boxShadow = '0 0 0 3px rgba(168,85,247,0.1)';
  };
  const inputBlur = (e) => {
    e.target.style.borderColor = 'rgba(148, 163, 184, 0.15)';
    e.target.style.background = 'rgba(15, 23, 42, 0.5)';
    e.target.style.boxShadow = 'none';
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #1e1b4b 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <PremiumBackground />

      {/* Main container */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{
          position: 'relative',
          zIndex: 2,
          width: '100%',
          maxWidth: '1100px',
          display: 'grid',
          gridTemplateColumns: window.innerWidth > 900 ? '1fr 1fr' : '1fr',
          background: 'rgba(30, 41, 59, 0.4)',
          backdropFilter: 'blur(30px)',
          border: '1px solid rgba(148, 163, 184, 0.15)',
          borderRadius: '28px',
          overflow: 'hidden',
          boxShadow: '0 40px 100px rgba(0,0,0,0.6), 0 0 0 1px rgba(168,85,247,0.1)',
          minHeight: '640px',
        }}
      >
        {/* LEFT: Illustration (hidden on mobile) */}
        {window.innerWidth > 900 && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(99,102,241,0.08))',
            borderRight: '1px solid rgba(148, 163, 184, 0.1)',
            position: 'relative',
          }}>
            <IllustrationPanel />
          </div>
        )}

        {/* RIGHT: Form */}
        <div style={{
          padding: window.innerWidth > 900 ? '50px 45px' : '40px 28px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          {/* Header */}
          <div style={{ marginBottom: '28px' }}>
            <h1 style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#fff',
              margin: 0,
              letterSpacing: '-0.5px',
            }}>
              {mode === 'signin' ? 'Welcome back' : 'Create account'}
            </h1>
            <p style={{
              fontSize: '13px',
              color: 'rgba(255,255,255,0.5)',
              marginTop: '6px',
            }}>
              {mode === 'signin'
                ? 'Sign in to your Smart DevOps account'
                : 'Get started with autonomous DevOps'}
            </p>
          </div>

          {/* Tab switcher */}
          <div style={{
            display: 'flex',
            padding: '4px',
            background: 'rgba(15, 23, 42, 0.5)',
            borderRadius: '12px',
            marginBottom: '24px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
          }}>
            {['signin', 'signup'].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                style={{
                  flex: 1,
                  padding: '10px',
                  background: mode === m
                    ? 'linear-gradient(135deg, #a855f7, #6366f1)'
                    : 'transparent',
                  color: mode === m ? '#fff' : 'rgba(255,255,255,0.5)',
                  border: 'none',
                  borderRadius: '9px',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: mode === m ? '0 4px 16px rgba(168,85,247,0.3)' : 'none',
                }}
              >
                {m === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {mode === 'signin' ? (
              <motion.form
                key="signin"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                onSubmit={handleSignIn}
              >
                {/* Email */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{
                    display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)',
                    marginBottom: '6px', fontWeight: 500,
                  }}>
                    Email
                  </label>
                  <div style={{ position: 'relative' }}>
                    <FiMail style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      autoComplete="email"
                      style={inputBase}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                  </div>
                </div>

                {/* Password */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>
                      Password
                    </label>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <FiLock style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      autoComplete="current-password"
                      style={inputBase}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw(!showPw)}
                      style={{
                        position: 'absolute', right: '12px', top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'none', border: 'none',
                        color: 'rgba(255,255,255,0.4)',
                        cursor: 'pointer', fontSize: '16px', padding: '4px',
                      }}
                    >
                      {showPw ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                </div>

                {/* Remember me */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', fontSize: '12px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'rgba(255,255,255,0.6)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      style={{ accentColor: '#a855f7' }}
                    />
                    Remember me
                  </label>
                  <button
                    type="button"
                    onClick={() => toast.info('Contact admin to reset password')}
                    style={{
                      background: 'none', border: 'none',
                      color: '#a855f7', cursor: 'pointer',
                      fontSize: '12px', fontWeight: 500,
                    }}
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading || !email || !password}
                  style={{
                    width: '100%',
                    padding: '13px',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '14px',
                    fontWeight: 700,
                    cursor: (!email || !password || loading) ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                    color: '#fff',
                    boxShadow: '0 10px 30px rgba(168,85,247,0.4)',
                    opacity: (!email || !password) ? 0.5 : 1,
                    transition: 'all 0.2s',
                  }}
                >
                  {loading ? (
                    <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Signing in...</>
                  ) : (
                    <>Sign In</>
                  )}
                </button>
              </motion.form>
            ) : (
              <motion.form
                key="signup"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                onSubmit={handleSignUp}
              >
                {/* Name */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px', fontWeight: 500 }}>
                    Full Name
                  </label>
                  <div style={{ position: 'relative' }}>
                    <FiUser style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type="text"
                      value={suName}
                      onChange={(e) => setSuName(e.target.value)}
                      placeholder="Your full name"
                      autoComplete="name"
                      style={inputBase}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                  </div>
                </div>

                {/* Email */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px', fontWeight: 500 }}>
                    Email
                  </label>
                  <div style={{ position: 'relative' }}>
                    <FiMail style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type="email"
                      value={suEmail}
                      onChange={(e) => setSuEmail(e.target.value)}
                      placeholder="you@example.com"
                      autoComplete="email"
                      style={inputBase}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                  </div>
                </div>

                {/* Password */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px', fontWeight: 500 }}>
                    Password
                  </label>
                  <div style={{ position: 'relative' }}>
                    <FiLock style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={suPassword}
                      onChange={(e) => setSuPassword(e.target.value)}
                      placeholder="Min 12 characters"
                      autoComplete="new-password"
                      style={inputBase}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw(!showPw)}
                      style={{
                        position: 'absolute', right: '12px', top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'none', border: 'none',
                        color: 'rgba(255,255,255,0.4)',
                        cursor: 'pointer', fontSize: '16px', padding: '4px',
                      }}
                    >
                      {showPw ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                  <PasswordStrength password={suPassword} />
                </div>

                {/* Confirm Password */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px', fontWeight: 500 }}>
                    Confirm Password
                  </label>
                  <div style={{ position: 'relative' }}>
                    <FiLock style={{
                      position: 'absolute', left: '14px', top: '50%',
                      transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)',
                      fontSize: '16px',
                    }} />
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={suConfirm}
                      onChange={(e) => setSuConfirm(e.target.value)}
                      placeholder="Repeat password"
                      autoComplete="new-password"
                      style={{
                        ...inputBase,
                        borderColor: suConfirm && suConfirm !== suPassword
                          ? 'rgba(239,68,68,0.5)'
                          : 'rgba(148, 163, 184, 0.15)',
                      }}
                      onFocus={inputFocus}
                      onBlur={inputBlur}
                    />
                    {suConfirm && suConfirm === suPassword && (
                      <FiCheck style={{
                        position: 'absolute', right: '14px', top: '50%',
                        transform: 'translateY(-50%)',
                        color: '#10b981', fontSize: '18px',
                      }} />
                    )}
                  </div>
                </div>

                {/* Terms */}
                <label style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px',
                  marginBottom: '18px', fontSize: '12px',
                  color: 'rgba(255,255,255,0.6)', cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={agreeTerms}
                    onChange={(e) => setAgreeTerms(e.target.checked)}
                    style={{ marginTop: '2px', accentColor: '#a855f7' }}
                  />
                  <span>
                    I agree to the <span style={{ color: '#a855f7' }}>Terms of Service</span> and{' '}
                    <span style={{ color: '#a855f7' }}>Privacy Policy</span>
                  </span>
                </label>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading || !suName || !suEmail || !suPassword || !agreeTerms}
                  style={{
                    width: '100%',
                    padding: '13px',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '14px',
                    fontWeight: 700,
                    cursor: (!suName || !suEmail || !suPassword || !agreeTerms || loading) ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                    color: '#fff',
                    boxShadow: '0 10px 30px rgba(168,85,247,0.4)',
                    opacity: (!suName || !suEmail || !suPassword || !agreeTerms) ? 0.5 : 1,
                    transition: 'all 0.2s',
                  }}
                >
                  {loading ? (
                    <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Creating...</>
                  ) : (
                    <>Create Account</>
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
            <div style={{ flex: 1, height: '1px', background: 'rgba(148, 163, 184, 0.15)' }} />
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.5px', fontWeight: 500 }}>
              OR
            </span>
            <div style={{ flex: 1, height: '1px', background: 'rgba(148, 163, 184, 0.15)' }} />
          </div>

          {/* OAuth Buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <button
              type="button"
              onClick={() => handleOAuth('github')}
              disabled={!!oauthLoading}
              style={{
                padding: '11px',
                background: 'rgba(15, 23, 42, 0.5)',
                color: '#fff',
                border: '1px solid rgba(148, 163, 184, 0.15)',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: oauthLoading ? 'wait' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(51, 65, 85, 0.6)';
                e.currentTarget.style.borderColor = 'rgba(168,85,247,0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(15, 23, 42, 0.5)';
                e.currentTarget.style.borderColor = 'rgba(148, 163, 184, 0.15)';
              }}
            >
              {oauthLoading === 'github' ? (
                <FiLoader style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <FaGithub style={{ fontSize: '18px' }} />
              )}
              GitHub
            </button>

            <button
              type="button"
              onClick={() => handleOAuth('google')}
              disabled={!!oauthLoading}
              style={{
                padding: '11px',
                background: 'rgba(15, 23, 42, 0.5)',
                color: '#fff',
                border: '1px solid rgba(148, 163, 184, 0.15)',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: oauthLoading ? 'wait' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(51, 65, 85, 0.6)';
                e.currentTarget.style.borderColor = 'rgba(168,85,247,0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(15, 23, 42, 0.5)';
                e.currentTarget.style.borderColor = 'rgba(148, 163, 184, 0.15)';
              }}
            >
              {oauthLoading === 'google' ? (
                <FiLoader style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <FaGoogle style={{ fontSize: '16px' }} />
              )}
              Google
            </button>
          </div>

          {/* Security footer */}
          <div style={{
            marginTop: '20px',
            padding: '10px 14px',
            background: 'rgba(16, 185, 129, 0.06)',
            border: '1px solid rgba(16, 185, 129, 0.15)',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}>
            <FiLock style={{ color: '#10b981', fontSize: '14px', flexShrink: 0 }} />
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', lineHeight: 1.5 }}>
              <strong style={{ color: '#10b981' }}>Enterprise-grade security</strong> — bcrypt 12 rounds · JWT httpOnly cookies · Rate limiting
            </div>
          </div>
        </div>
      </motion.div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @media (max-width: 900px) {
          body { overflow-x: hidden; }
        }
      `}</style>
    </div>
  );
};

export default Login;