import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import AssistantChat from './components/Chat/AssistantChat';
// import ProjectUpload from './components/Upload/ProjectUpload';  // ← REMOVED
import PipelineDashboard from './components/Pipelines/PipelineDashboard';
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
                                {/* <Route path="upload" element={<ProjectUpload />} />  ← REMOVED */}
                                <Route path="pipelines" element={<PipelineDashboard />} />
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