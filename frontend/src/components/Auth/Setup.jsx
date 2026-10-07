import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { FaRobot } from 'react-icons/fa';
import { FiUser, FiMail, FiLock, FiLoader, FiCheckCircle } from 'react-icons/fi';

const Setup = () => {
  const { setup } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordChecks = {
    length: password.length >= 12,
    number: /\d/.test(password),
    upper: /[A-Z]/.test(password),
    symbol: /[^A-Za-z0-9]/.test(password),
  };
  const allValid = Object.values(passwordChecks).every(Boolean);
  const match = password && password === confirm;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!allValid || !match) return;
    setLoading(true);
    await setup(name, email, password);
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)', padding: '20px',
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          width: '100%', maxWidth: '480px',
          background: 'rgba(30, 41, 59, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(148, 163, 184, 0.15)',
          borderRadius: '24px', padding: '40px 32px',
          boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '64px', height: '64px', margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            borderRadius: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FaRobot style={{ fontSize: '28px', color: '#fff' }} />
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#fff', margin: 0 }}>
            First-Time Setup
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', marginTop: '6px' }}>
            Create your admin account
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {[
            { icon: FiUser, value: name, set: setName, type: 'text', ph: 'Your name', label: 'Name', ac: 'name' },
            { icon: FiMail, value: email, set: setEmail, type: 'email', ph: 'you@example.com', label: 'Email', ac: 'email' },
          ].map(({ icon: Icon, value, set, type, ph, label, ac }, i) => (
            <div key={i} style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
                {label}
              </label>
              <div style={{ position: 'relative' }}>
                <Icon style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }} />
                <input
                  type={type} value={value} onChange={(e) => set(e.target.value)}
                  placeholder={ph} autoComplete={ac} autoFocus={i === 0}
                  style={{
                    width: '100%', padding: '12px 12px 12px 40px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                    borderRadius: '12px', color: '#fff', fontSize: '14px', outline: 'none',
                  }}
                />
              </div>
            </div>
          ))}

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
              Password (min 12 chars)
            </label>
            <div style={{ position: 'relative' }}>
              <FiLock style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }} />
              <input
                type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 12 characters"
                style={{
                  width: '100%', padding: '12px 12px 12px 40px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '12px', color: '#fff', fontSize: '14px', outline: 'none',
                }}
              />
            </div>
            {password && (
              <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '11px' }}>
                {[
                  ['length', '12+ characters'],
                  ['upper', 'Uppercase letter'],
                  ['number', 'Number'],
                  ['symbol', 'Symbol'],
                ].map(([key, label]) => (
                  <div key={key} style={{
                    color: passwordChecks[key] ? '#10b981' : 'rgba(255,255,255,0.35)',
                    display: 'flex', alignItems: 'center', gap: '4px',
                  }}>
                    <FiCheckCircle size={12} /> {label}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
              Confirm Password
            </label>
            <div style={{ position: 'relative' }}>
              <FiLock style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)' }} />
              <input
                type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                placeholder="Repeat password"
                style={{
                  width: '100%', padding: '12px 12px 12px 40px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: `1px solid ${confirm && !match ? '#ef4444' : 'rgba(148, 163, 184, 0.2)'}`,
                  borderRadius: '12px', color: '#fff', fontSize: '14px', outline: 'none',
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !name || !email || !allValid || !match}
            style={{
              width: '100%', padding: '14px',
              background: 'linear-gradient(135deg, #a855f7, #6366f1)',
              border: 'none', borderRadius: '12px',
              color: '#fff', fontSize: '15px', fontWeight: 600,
              cursor: loading ? 'wait' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              opacity: (!name || !email || !allValid || !match) ? 0.5 : 1,
            }}
          >
            {loading ? <><FiLoader style={{ animation: 'spin 1s linear infinite' }} /> Creating...</> : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '11px', marginTop: '20px' }}>
          🔒 Premium security: bcrypt 12 rounds, JWT, httpOnly cookies
        </p>
      </motion.div>
    </div>
  );
};

export default Setup;