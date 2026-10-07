import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import AssistantChat from './components/Chat/AssistantChat';
import PipelineDashboard from './components/Pipelines/PipelineDashboard';
import PipelineDetails from './components/Pipelines/PipelineDetails';
import MonitoringDashboard from './components/Monitoring/MonitoringDashboard';
import InfraManager from './components/Infrastructure/InfraManager';
import TrainingDashboard from './components/Training/TrainingDashboard';
import ModelVersions from './components/Training/ModelVersions';
import Settings from './components/Settings/Settings';
import AuditLogs from './components/Settings/AuditLogs';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import ProtectedRoute from './components/Auth/ProtectedRoute';

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Router>
                    <div className="min-h-screen">
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />
                            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                                <Route index element={<Navigate to="/dashboard" />} />
                                <Route path="dashboard" element={<Dashboard />} />
                                <Route path="chat" element={<AssistantChat />} />

                                {/* Pipelines */}
                                <Route path="pipelines" element={<PipelineDashboard />} />
                                <Route path="pipelines/:id" element={<PipelineDetails />} />

                                {/* Monitoring — connected from Assistant */}
                                <Route path="monitoring" element={<MonitoringDashboard />} />

                                {/* Infrastructure — connected from Assistant Scale */}
                                <Route path="infrastructure" element={<InfraManager />} />

                                {/* Training */}
                                <Route path="training" element={<TrainingDashboard />} />
                                <Route path="training/versions" element={<ModelVersions />} />

                                {/* Settings */}
                                <Route path="settings" element={<Settings />} />
                                <Route path="settings/audit" element={<AuditLogs />} />
                            </Route>
                        </Routes>
                        <Toaster />
                    </div>
                </Router>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;