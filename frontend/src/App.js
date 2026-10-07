import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { SettingsProvider } from './context/SettingsContext';
import { useSessionTimeout } from './hooks/useSessionTimeout';

// Layout
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './components/Dashboard/Dashboard';
import AssistantChat from './components/Chat/AssistantChat';
import PipelineDashboard from './components/Pipelines/PipelineDashboard';
import MonitoringDashboard from './components/Monitoring/MonitoringDashboard';
import InfraManager from './components/Infrastructure/InfraManager';
import TrainingDashboard from './components/Training/TrainingDashboard';
import Settings from './components/Settings/Settings';

// Auth Pages
import Login from './components/Auth/Login';
import Setup from './components/Auth/Setup';

// ═══════════════════════════════════════════════════════════
// Loading Screen
// ═══════════════════════════════════════════════════════════
const LoadingScreen = () => (
  <div style={{
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
    color: '#fff',
    gap: '20px',
  }}>
    <div style={{
      width: '60px', height: '60px',
      border: '4px solid rgba(168, 85, 247, 0.2)',
      borderTop: '4px solid #a855f7',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
    }} />
    <div style={{ fontSize: '14px', opacity: 0.6 }}>Loading Smart DevOps...</div>
    <style>{`
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `}</style>
  </div>
);

// ═══════════════════════════════════════════════════════════
// SetupRedirect — if already authenticated, go to dashboard
// ═══════════════════════════════════════════════════════════
const SetupRedirect = ({ children }) => {
  const { loading, isAuthenticated, needsSetup } = useAuth();

  if (loading) return <LoadingScreen />;

  if (isAuthenticated && !needsSetup) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// ═══════════════════════════════════════════════════════════
// Auth Guard
// ═══════════════════════════════════════════════════════════
const AuthGuard = ({ children }) => {
  const { loading, isAuthenticated, needsSetup } = useAuth();
  const location = useLocation();

  if (loading) return <LoadingScreen />;

  if (needsSetup) {
    return <Navigate to="/setup" replace />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// ═══════════════════════════════════════════════════════════
// Public Route
// ═══════════════════════════════════════════════════════════
const PublicRoute = ({ children }) => {
  const { loading, isAuthenticated, needsSetup } = useAuth();

  if (loading) return <LoadingScreen />;

  if (needsSetup) {
    return <Navigate to="/setup" replace />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// ═══════════════════════════════════════════════════════════
// Routes
// ═══════════════════════════════════════════════════════════
const AppRoutes = () => {
  // ⭐ Auto-logout on inactivity
  useSessionTimeout();

  return (
    <Routes>
      {/* Setup Route — auto-redirects when done */}
      <Route path="/setup" element={<SetupRedirect><Setup /></SetupRedirect>} />

      {/* Public — Login */}
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />

      {/* Protected Routes */}
      <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="chat" element={<AssistantChat />} />
        <Route path="pipelines" element={<PipelineDashboard />} />
        <Route path="monitoring" element={<MonitoringDashboard />} />
        <Route path="infrastructure" element={<InfraManager />} />
        <Route path="training" element={<TrainingDashboard />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

// ═══════════════════════════════════════════════════════════
// Main App
// ═══════════════════════════════════════════════════════════
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <SettingsProvider>
          <Router>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-300">
              <AppRoutes />
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#363636',
                    color: '#fff',
                    borderRadius: '12px',
                    padding: '16px',
                  },
                }}
              />
            </div>
          </Router>
        </SettingsProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;