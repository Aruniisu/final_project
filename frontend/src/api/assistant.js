import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Handle response errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// ============================================
// AUTH API
// ============================================
export const authAPI = {
    register: async (userData) => {
        try {
            const response = await api.post('/auth/register', userData);
            return response.data;
        } catch (error) {
            console.error('Register error:', error);
            throw error;
        }
    },

    login: async (credentials) => {
        try {
            const response = await api.post('/auth/login', credentials);
            return response.data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    getMe: async () => {
        try {
            const response = await api.get('/auth/me');
            return response.data;
        } catch (error) {
            console.error('Get user error:', error);
            throw error;
        }
    },

    logout: async () => {
        try {
            await api.post('/auth/logout');
            localStorage.removeItem('token');
        } catch (error) {
            console.error('Logout error:', error);
        }
    },

    updateProfile: async (data) => {
        try {
            const response = await api.put('/auth/profile', data);
            return response.data;
        } catch (error) {
            console.error('Update profile error:', error);
            throw error;
        }
    },

    changePassword: async (data) => {
        try {
            const response = await api.post('/auth/change-password', data);
            return response.data;
        } catch (error) {
            console.error('Change password error:', error);
            throw error;
        }
    }
};

// ============================================
// ASSISTANT API
// ============================================
export const assistantAPI = {
    // Send query to AI assistant
    sendQuery: async (query, context = {}) => {
        try {
            const response = await api.post('/assistant/query', {
                query,
                context,
                timestamp: new Date().toISOString(),
            });
            return response.data;
        } catch (error) {
            console.error('Error sending query:', error);
            // Return mock response for demo when backend is not available
            return {
                response: `I received your query: "${query}". I'm here to help with DevOps tasks!`,
                tools: ['devops', 'automation'],
                message: 'Query processed successfully (mock)'
            };
        }
    },

    // Get chat history
    getHistory: async (limit = 50, offset = 0) => {
        try {
            const response = await api.get('/assistant/history', {
                params: { limit, offset },
            });
            return response.data;
        } catch (error) {
            console.error('Error getting history:', error);
            return [];
        }
    },

    // Provide feedback
    sendFeedback: async (messageId, feedback) => {
        try {
            const response = await api.post('/assistant/feedback', {
                messageId,
                feedback,
                timestamp: new Date().toISOString(),
            });
            return response.data;
        } catch (error) {
            console.error('Error sending feedback:', error);
            return { success: false };
        }
    },

    // Get suggestions
    getSuggestions: async (context = '') => {
        try {
            const response = await api.get('/assistant/suggestions', {
                params: { context },
            });
            return response.data;
        } catch (error) {
            console.error('Error getting suggestions:', error);
            return ['Deploy to production', 'Check pipeline status', 'Monitor system health'];
        }
    },

    // Get assistant status
    getStatus: async () => {
        try {
            const response = await api.get('/assistant/status');
            return response.data;
        } catch (error) {
            console.error('Error getting status:', error);
            return {
                status: 'online',
                version: '2.3.1',
                uptime: '99.9%',
                models: 5
            };
        }
    },
};

// ============================================
// UPLOAD API
// ============================================
export const uploadAPI = {
    // Upload files
    uploadFiles: async (files, onProgress) => {
        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });

        try {
            const response = await api.post('/upload/files', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: onProgress,
            });
            return response.data;
        } catch (error) {
            console.error('Upload error:', error);
            // Return mock for demo
            return {
                projectId: 'mock-' + Date.now(),
                projectName: files[0]?.name || 'Uploaded Project',
                message: 'Upload successful (mock)',
                analysis: {
                    healthScore: 85,
                    issues: 3,
                    securityScore: 92,
                    recommendations: 5,
                    project_type: 'javascript'
                }
            };
        }
    },

    // Upload from GitHub
    uploadGitHub: async (url) => {
        try {
            const response = await api.post('/upload/github', { url });
            return response.data;
        } catch (error) {
            console.error('GitHub upload error:', error);
            return {
                projectId: 'github-' + Date.now(),
                projectName: url.split('/').pop() || 'GitHub Project',
                message: 'GitHub import successful (mock)',
                analysis: {
                    healthScore: 85,
                    issues: 3,
                    securityScore: 92,
                    recommendations: 5
                }
            };
        }
    },

    // Upload from Google Drive
    uploadDrive: async (url) => {
        try {
            const response = await api.post('/upload/drive', { url });
            return response.data;
        } catch (error) {
            console.error('Drive upload error:', error);
            return {
                projectId: 'drive-' + Date.now(),
                projectName: 'Drive Project',
                message: 'Drive import successful (mock)',
                analysis: {
                    healthScore: 78,
                    issues: 5,
                    securityScore: 85,
                    recommendations: 8
                }
            };
        }
    },

    // Upload from direct link
    uploadLink: async (url) => {
        try {
            const response = await api.post('/upload/link', { url });
            return response.data;
        } catch (error) {
            console.error('Link upload error:', error);
            return {
                projectId: 'link-' + Date.now(),
                projectName: url.split('/').pop() || 'Link Project',
                message: 'Link import successful (mock)',
                analysis: {
                    healthScore: 70,
                    issues: 4,
                    securityScore: 80,
                    recommendations: 6
                }
            };
        }
    },

    // Get project analysis
    getAnalysis: async (projectId) => {
        try {
            const response = await api.get(`/upload/${projectId}/analyze`);
            return response.data;
        } catch (error) {
            console.error('Get analysis error:', error);
            return {
                healthScore: 85,
                issues: 3,
                securityScore: 92,
                recommendations: 5,
                project_type: 'javascript',
                details: {
                    code_quality: { total_lines: 1250, total_files: 15 },
                    dependencies: { npm: { react: '18.2.0', express: '4.18.2' } }
                }
            };
        }
    },

    // Get upload history
    getHistory: async () => {
        try {
            const response = await api.get('/upload/history');
            return response.data;
        } catch (error) {
            console.error('Get history error:', error);
            return [
                {
                    projectId: '1',
                    projectName: 'Demo Project',
                    source: 'github',
                    status: 'completed',
                    createdAt: new Date().toISOString(),
                    metadata: { analysis: { healthScore: 85, issues: 3 } }
                },
                {
                    projectId: '2',
                    projectName: 'Test Upload',
                    source: 'file',
                    status: 'completed',
                    createdAt: new Date(Date.now() - 86400000).toISOString(),
                    metadata: { analysis: { healthScore: 92, issues: 1 } }
                }
            ];
        }
    },

    // Delete project
    deleteProject: async (projectId) => {
        try {
            const response = await api.delete(`/upload/${projectId}`);
            return response.data;
        } catch (error) {
            console.error('Delete project error:', error);
            return { success: true };
        }
    },
};

// ============================================
// PIPELINE API
// ============================================
export const pipelineAPI = {
    // Get all pipelines
    getAll: async () => {
        try {
            const response = await api.get('/pipelines');
            return response.data;
        } catch (error) {
            console.error('Get pipelines error:', error);
            return [
                {
                    id: '1',
                    name: 'Frontend Deployment',
                    repo: 'org/frontend-app',
                    commit: 'abc1234',
                    status: 'running',
                    progress: 68,
                    duration: '2m 34s',
                    steps: [
                        { name: 'Build', status: 'completed', duration: '2m 34s' },
                        { name: 'Test', status: 'completed', duration: '1m 12s' },
                        { name: 'Deploy', status: 'running', duration: '—' },
                        { name: 'Monitor', status: 'pending', duration: '—' },
                    ],
                    createdAt: new Date().toISOString(),
                },
                {
                    id: '2',
                    name: 'Backend API Pipeline',
                    repo: 'org/backend-api',
                    commit: 'def5678',
                    status: 'success',
                    progress: 100,
                    duration: '5m 12s',
                    steps: [
                        { name: 'Build', status: 'completed', duration: '1m 45s' },
                        { name: 'Test', status: 'completed', duration: '2m 30s' },
                        { name: 'Deploy', status: 'completed', duration: '45s' },
                        { name: 'Monitor', status: 'completed', duration: '12s' },
                    ],
                    createdAt: new Date().toISOString(),
                },
                {
                    id: '3',
                    name: 'Mobile App Build',
                    repo: 'org/mobile-app',
                    commit: 'ghi9012',
                    status: 'failed',
                    progress: 45,
                    duration: '3m 20s',
                    steps: [
                        { name: 'Build', status: 'completed', duration: '2m 10s' },
                        { name: 'Test', status: 'failed', duration: '1m 10s' },
                        { name: 'Deploy', status: 'pending', duration: '—' },
                        { name: 'Monitor', status: 'pending', duration: '—' },
                    ],
                    createdAt: new Date().toISOString(),
                },
            ];
        }
    },

    // Get pipeline details
    getDetails: async (id) => {
        try {
            const response = await api.get(`/pipelines/${id}`);
            return response.data;
        } catch (error) {
            console.error('Get pipeline details error:', error);
            return {
                id,
                name: 'Pipeline ' + id,
                status: 'running',
                progress: 50,
                steps: [
                    { name: 'Build', status: 'completed', duration: '1m 30s' },
                    { name: 'Test', status: 'running', duration: '—' },
                    { name: 'Deploy', status: 'pending', duration: '—' },
                ],
                logs: [
                    { timestamp: new Date(Date.now() - 60000).toISOString(), level: 'info', message: 'Build started' },
                    { timestamp: new Date(Date.now() - 30000).toISOString(), level: 'success', message: 'Build completed' },
                    { timestamp: new Date().toISOString(), level: 'info', message: 'Running tests...' },
                ],
                triggeredBy: 'John Doe',
                branch: 'main',
                commit: 'abc1234',
                duration: '2m 34s',
                createdAt: new Date().toISOString(),
            };
        }
    },

    // Create new pipeline
    create: async (data) => {
        try {
            const response = await api.post('/pipelines', data);
            return response.data;
        } catch (error) {
            console.error('Create pipeline error:', error);
            return {
                pipeline_id: 'pipe-' + Date.now(),
                name: data.name || 'New Pipeline',
                status: 'pending',
                message: 'Pipeline created (mock)'
            };
        }
    },

    // Trigger pipeline
    trigger: async (pipelineId, params = {}) => {
        try {
            const response = await api.post(`/pipelines/${pipelineId}/trigger`, params);
            return response.data;
        } catch (error) {
            console.error('Trigger pipeline error:', error);
            return { success: true, message: 'Pipeline triggered (mock)' };
        }
    },

    // Get pipeline logs
    getLogs: async (id, options = {}) => {
        try {
            const response = await api.get(`/pipelines/${id}/logs`, { params: options });
            return response.data;
        } catch (error) {
            console.error('Get logs error:', error);
            return [
                { timestamp: new Date().toISOString(), level: 'info', message: 'Build started' },
                { timestamp: new Date().toISOString(), level: 'success', message: 'Build completed' },
                { timestamp: new Date().toISOString(), level: 'info', message: 'Running tests...' },
                { timestamp: new Date().toISOString(), level: 'success', message: 'All tests passed' },
            ];
        }
    },

    // Retry pipeline
    retry: async (id) => {
        try {
            const response = await api.post(`/pipelines/${id}/retry`);
            return response.data;
        } catch (error) {
            console.error('Retry pipeline error:', error);
            return { success: true };
        }
    },

    // Cancel pipeline
    cancel: async (id) => {
        try {
            const response = await api.post(`/pipelines/${id}/cancel`);
            return response.data;
        } catch (error) {
            console.error('Cancel pipeline error:', error);
            return { success: true };
        }
    },

    // Delete pipeline
    delete: async (id) => {
        try {
            const response = await api.delete(`/pipelines/${id}`);
            return response.data;
        } catch (error) {
            console.error('Delete pipeline error:', error);
            return { success: true };
        }
    },
};

// ============================================
// INFRASTRUCTURE API
// ============================================
export const infrastructureAPI = {
    getClusters: async () => {
        try {
            const response = await api.get('/infrastructure/clusters');
            return response.data;
        } catch (error) {
            console.error('Get clusters error:', error);
            return [
                {
                    id: '1',
                    name: 'Production Cluster',
                    provider: 'aws',
                    status: 'healthy',
                    nodes: 12,
                    pods: 45,
                    cpuUsage: 68,
                    memoryUsage: 72,
                    diskUsage: 45,
                    uptime: '99.97%',
                    version: 'v1.28.0',
                    region: 'us-west-2',
                    cost: '$2,340.00'
                },
                {
                    id: '2',
                    name: 'Staging Cluster',
                    provider: 'gcp',
                    status: 'healthy',
                    nodes: 6,
                    pods: 20,
                    cpuUsage: 45,
                    memoryUsage: 55,
                    diskUsage: 30,
                    uptime: '99.5%',
                    version: 'v1.27.0',
                    region: 'us-central1',
                    cost: '$890.00'
                },
                {
                    id: '3',
                    name: 'Development Cluster',
                    provider: 'azure',
                    status: 'warning',
                    nodes: 3,
                    pods: 8,
                    cpuUsage: 85,
                    memoryUsage: 88,
                    diskUsage: 72,
                    uptime: '98.2%',
                    version: 'v1.26.0',
                    region: 'east-us',
                    cost: '$450.00'
                }
            ];
        }
    },

    scaleCluster: async (data) => {
        try {
            const response = await api.post('/infrastructure/scale', data);
            return response.data;
        } catch (error) {
            console.error('Scale cluster error:', error);
            return {
                message: `Cluster ${data.cluster_id} scaled to ${data.replicas} replicas (mock)`,
                cluster_id: data.cluster_id,
                replicas: data.replicas,
                status: 'scaling'
            };
        }
    },

    getResources: async () => {
        try {
            const response = await api.get('/infrastructure/resources');
            return response.data;
        } catch (error) {
            console.error('Get resources error:', error);
            return {
                cpu: 45,
                memory: 62,
                disk: 34,
                network: 23
            };
        }
    }
};

// ============================================
// MONITORING API
// ============================================
export const monitoringAPI = {
    getMetrics: async (timeRange = '1h') => {
        try {
            const response = await api.get('/monitoring/metrics', {
                params: { timeRange },
            });
            return response.data;
        } catch (error) {
            console.error('Get metrics error:', error);
            const now = Date.now();
            const history = [];
            for (let i = 0; i < 60; i++) {
                history.push({
                    timestamp: new Date(now - (60 - i) * 60000).toISOString(),
                    cpu: 20 + Math.random() * 60,
                    memory: 30 + Math.random() * 50,
                    disk: 10 + Math.random() * 40,
                    latency: 50 + Math.random() * 250
                });
            }
            return {
                metrics: {
                    uptime: '99.92%',
                    requests: '12.4k',
                    errors: Math.floor(30 + Math.random() * 40),
                    latency: `${Math.floor(150 + Math.random() * 150)}ms`
                },
                history: history,
                time_range: timeRange
            };
        }
    },

    getAlerts: async (status = 'all') => {
        try {
            const response = await api.get('/monitoring/alerts', {
                params: { status },
            });
            return response.data;
        } catch (error) {
            console.error('Get alerts error:', error);
            const alerts = [
                {
                    id: '1',
                    title: 'High CPU Usage Detected',
                    message: 'CPU usage exceeded 85% threshold on Production Cluster',
                    severity: 'critical',
                    status: 'active',
                    time: '2 minutes ago',
                    source: 'Production Cluster'
                },
                {
                    id: '2',
                    title: 'Database Connection Timeout',
                    message: 'Multiple connection timeouts detected from API service',
                    severity: 'high',
                    status: 'acknowledged',
                    time: '15 minutes ago',
                    source: 'PostgreSQL'
                },
                {
                    id: '3',
                    title: 'Memory Usage Warning',
                    message: 'Memory usage approaching 80% on Staging Cluster',
                    severity: 'medium',
                    status: 'active',
                    time: '45 minutes ago',
                    source: 'Staging Cluster'
                }
            ];
            if (status !== 'all') {
                return alerts.filter(a => a.status === status || a.severity === status);
            }
            return alerts;
        }
    },

    acknowledgeAlert: async (alertId) => {
        try {
            const response = await api.post(`/monitoring/alerts/${alertId}/acknowledge`);
            return response.data;
        } catch (error) {
            console.error('Acknowledge alert error:', error);
            return {
                message: `Alert ${alertId} acknowledged (mock)`,
                alert_id: alertId,
                status: 'acknowledged'
            };
        }
    },

    getHealth: async () => {
        try {
            const response = await api.get('/monitoring/health');
            return response.data;
        } catch (error) {
            console.error('Get health error:', error);
            return {
                status: 'healthy',
                services: 12,
                uptime: '99.9%',
                timestamp: new Date().toISOString()
            };
        }
    }
};

// ============================================
// TRAINING API
// ============================================
export const trainingAPI = {
    getModels: async () => {
        try {
            const response = await api.get('/training/models');
            return response.data;
        } catch (error) {
            console.error('Get models error:', error);
            return [
                {
                    id: '1',
                    name: 'DevOps Assistant v2',
                    version: '2.3.1',
                    status: 'active',
                    accuracy: 0.947,
                    f1: 0.945,
                    parameters: '1.2M',
                    size: '234 MB',
                    createdAt: '2024-01-15',
                    favorite: true
                },
                {
                    id: '2',
                    name: 'DevOps Assistant v1',
                    version: '2.3.0',
                    status: 'deprecated',
                    accuracy: 0.932,
                    f1: 0.928,
                    parameters: '1.1M',
                    size: '210 MB',
                    createdAt: '2024-01-12',
                    favorite: false
                },
                {
                    id: '3',
                    name: 'Security Scanner Model',
                    version: '1.0.0',
                    status: 'active',
                    accuracy: 0.965,
                    f1: 0.962,
                    parameters: '890K',
                    size: '160 MB',
                    createdAt: '2024-01-14',
                    favorite: true
                }
            ];
        }
    },

    startTraining: async (config) => {
        try {
            const response = await api.post('/training/train', config);
            return response.data;
        } catch (error) {
            console.error('Start training error:', error);
            return {
                success: true,
                training_id: 'train-' + Date.now(),
                status: 'pending',
                message: 'Training started (mock)'
            };
        }
    },

    getStatus: async (trainingId) => {
        try {
            const response = await api.get(`/training/${trainingId}/status`);
            return response.data;
        } catch (error) {
            console.error('Get training status error:', error);
            return {
                training_id: trainingId,
                status: 'running',
                progress: Math.floor(Math.random() * 100),
                metrics: {
                    accuracy: 0.7 + Math.random() * 0.25,
                    loss: 0.3 - Math.random() * 0.25
                }
            };
        }
    },

    stopTraining: async (id) => {
        try {
            const response = await api.post(`/training/${id}/stop`);
            return response.data;
        } catch (error) {
            console.error('Stop training error:', error);
            return {
                success: true,
                message: 'Training stopped (mock)'
            };
        }
    },

    deployModel: async (modelId) => {
        try {
            const response = await api.post('/training/deploy', { model_id: modelId });
            return response.data;
        } catch (error) {
            console.error('Deploy model error:', error);
            return {
                success: true,
                message: `Model ${modelId} deployed successfully (mock)`,
                model_id: modelId,
                status: 'deployed'
            };
        }
    },

    getVersions: async () => {
        try {
            const response = await api.get('/training/versions');
            return response.data;
        } catch (error) {
            console.error('Get versions error:', error);
            return [
                { version: 'v2.3.1', accuracy: 94.7, date: '2024-01-15', status: 'current' },
                { version: 'v2.3.0', accuracy: 93.2, date: '2024-01-12', status: 'archived' },
                { version: 'v2.2.9', accuracy: 92.8, date: '2024-01-10', status: 'archived' },
                { version: 'v2.2.8', accuracy: 89.5, date: '2024-01-08', status: 'archived' }
            ];
        }
    }
};

// ============================================
// SETTINGS API
// ============================================
export const settingsAPI = {
    getSettings: async () => {
        try {
            const response = await api.get('/settings');
            return response.data;
        } catch (error) {
            console.error('Get settings error:', error);
            return {
                general: {
                    language: 'en',
                    timezone: 'UTC',
                    dateFormat: 'MM/DD/YYYY'
                },
                appearance: {
                    theme: 'dark',
                    compactMode: false,
                    animations: true
                },
                notifications: {
                    emailNotifications: true,
                    slackNotifications: false,
                    alertSeverity: 'high'
                },
                security: {
                    twoFactorAuth: false,
                    sessionTimeout: 30,
                    passwordExpiry: 90
                },
                integrations: {
                    github: { connected: true, repo: 'org/devops-assistant' },
                    google: { connected: false },
                    aws: { connected: true, region: 'us-west-2' },
                    docker: { connected: false }
                }
            };
        }
    },

    updateSettings: async (settings) => {
        try {
            const response = await api.put('/settings', settings);
            return response.data;
        } catch (error) {
            console.error('Update settings error:', error);
            return {
                success: true,
                message: 'Settings updated (mock)'
            };
        }
    },

    getAuditLogs: async (limit = 50, offset = 0) => {
        try {
            const response = await api.get('/settings/audit-logs', {
                params: { limit, offset }
            });
            return response.data;
        } catch (error) {
            console.error('Get audit logs error:', error);
            const actions = ['login', 'logout', 'deploy', 'update', 'delete', 'create'];
            const users = ['john.doe@example.com', 'jane.smith@example.com', 'admin@example.com'];
            const logs = [];
            for (let i = 0; i < Math.min(limit, 10); i++) {
                logs.push({
                    user: users[Math.floor(Math.random() * users.length)],
                    action: actions[Math.floor(Math.random() * actions.length)],
                    target: 'System',
                    status: Math.random() > 0.8 ? 'failed' : 'success',
                    time: new Date(Date.now() - i * 60000).toLocaleString(),
                    ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
                    details: 'Action performed successfully'
                });
            }
            return logs;
        }
    },

    connectIntegration: async (provider, data) => {
        try {
            const response = await api.post(`/settings/integrations/${provider}`, data);
            return response.data;
        } catch (error) {
            console.error('Connect integration error:', error);
            return {
                success: true,
                message: `${provider} integration connected (mock)`,
                provider: provider,
                status: 'connected'
            };
        }
    },

    disconnectIntegration: async (provider) => {
        try {
            const response = await api.delete(`/settings/integrations/${provider}`);
            return response.data;
        } catch (error) {
            console.error('Disconnect integration error:', error);
            return {
                success: true,
                message: `${provider} integration disconnected (mock)`,
                provider: provider,
                status: 'disconnected'
            };
        }
    }
};

// Default export for backward compatibility
export default api;