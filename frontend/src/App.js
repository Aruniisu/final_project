import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';

// Layout
import Layout from './components/Layout/Layout';

// Pages - We'll create these next
import Dashboard from './components/Dashboard/Dashboard';
import AssistantChat from './components/Chat/AssistantChat';
import PipelineDashboard from './components/Pipelines/PipelineDashboard';
import MonitoringDashboard from './components/Monitoring/MonitoringDashboard';
import TrainingDashboard from './components/Training/TrainingDashboard';
import Settings from './components/Settings/Settings';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import ProtectedRoute from './components/Auth/ProtectedRoute';

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-300">
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />
                            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                                <Route index element={<Navigate to="/dashboard" />} />
                                <Route path="dashboard" element={<Dashboard />} />
                                <Route path="chat" element={<AssistantChat />} />
                                <Route path="pipelines" element={<PipelineDashboard />} />
                                <Route path="monitoring" element={<MonitoringDashboard />} />
                                <Route path="training" element={<TrainingDashboard />} />
                                <Route path="settings" element={<Settings />} />
                            </Route>
                            <Route path="*" element={<Navigate to="/dashboard" />} />
                        </Routes>
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
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;