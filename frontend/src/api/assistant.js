/**
 * Assistant API Client — Full Premium + Agentic AI
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';
export const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5000';
export const API_BASE = API_BASE_URL;
const DEVOPS_BASE = process.env.REACT_APP_WS_URL || 'http://localhost:5000';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
});

const devopsApi = axios.create({
    baseURL: DEVOPS_BASE,
    timeout: 600000,
    headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
    },
    (error) => Promise.reject(error)
);

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
// HELPERS
// ============================================
function isPublicUrl(url) {
    if (!url) return false;
    if (typeof url !== 'string') return false;
    if (url.includes('localhost')) return false;
    if (url.includes('127.0.0.1')) return false;
    if (url.includes('192.168.')) return false;
    if (url.includes('10.')) return false;
    if (!url.startsWith('http://') && !url.startsWith('https://')) return false;
    return true;
}

function deploymentToPipeline(d) {
    const hasPublicUrl = isPublicUrl(d.url);
    const isDeployed = d.frontend_ready || d.backend_ready;
    let status;
    if (d.status === 'stopped') status = 'cancelled';
    else if (d.status === 'deploying') status = 'running';
    else if (d.status === 'failed') status = 'failed';
    else if (isDeployed && hasPublicUrl) status = 'success';
    else if (isDeployed && !hasPublicUrl) status = 'running';
    else status = 'failed';

    let progress = 0;
    if (status === 'success') progress = 100;
    else if (status === 'running') progress = 50;
    else if (status === 'cancelled') progress = 100;

    return {
        id: d.id || d.deploy_id,
        name: `${d.owner || 'user'}/${d.repo || 'app'}`,
        repo: `${d.owner || 'user'}/${d.repo || 'app'}`,
        owner: d.owner,
        repoName: d.repo,
        url: hasPublicUrl ? d.url : null,
        rawUrl: d.url,
        status,
        deployType: d.deploy_type || 'auto',
        frontendReady: d.frontend_ready || false,
        backendReady: d.backend_ready || false,
        progress,
        duration: d.duration || '—',
        createdAt: d.deployed_at ? new Date(d.deployed_at * 1000).toISOString() : new Date().toISOString(),
        steps: [
            { name: 'Clone', status: 'completed', duration: '3s' },
            { name: 'Build', status: 'completed', duration: '25s' },
            { name: 'Deploy', status: 'completed', duration: '5s' },
            { name: 'Live', status: status === 'success' ? 'completed' : 'running', duration: '2s' },
        ],
    };
}

// ============================================
// AUTH API
// ============================================
export const authAPI = {
    register: async (userData) => (await api.post('/auth/register', userData)).data,
    login: async (credentials) => (await api.post('/auth/login', credentials)).data,
    getMe: async () => (await api.get('/auth/me')).data,
    logout: async () => {
        try { await api.post('/auth/logout'); } catch (e) {}
        localStorage.removeItem('token');
    },
    updateProfile: async (data) => (await api.put('/auth/profile', data)).data,
    changePassword: async (data) => (await api.post('/auth/change-password', data)).data,
};

// ============================================
// ASSISTANT API
// ============================================
export const assistantAPI = {
    sendQuery: async (query, context = {}) => {
        try { return (await api.post('/assistant/query', { query, context })).data; }
        catch { return { response: `Received: "${query}"`, message: 'Mock' }; }
    },
    chat: async (payload) => {
        try { return (await api.post('/assistant/chat', payload)).data; }
        catch { return { message: 'Mock chat', execution: { status: 'completed', progress: 100 } }; }
    },
    getHistory: async (limit = 50, offset = 0) => {
        try { return (await api.get('/assistant/history', { params: { limit, offset } })).data; }
        catch { return []; }
    },
    clearHistory: async (userId) => {
        try { return (await api.delete(`/assistant/history/${userId}`)).data; }
        catch { return { success: true }; }
    },
    sendFeedback: async (messageId, feedback) => {
        try { return (await api.post('/assistant/feedback', { messageId, feedback })).data; }
        catch { return { success: false }; }
    },
    getSuggestions: async (context = '') => {
        try { return (await api.get('/assistant/suggestions', { params: { context } })).data; }
        catch { return ['Deploy app', 'Check pipeline', 'Monitor system']; }
    },
    getStatus: async () => {
        try { return (await api.get('/assistant/status')).data; }
        catch { return { status: 'online', version: '3.0.0' }; }
    },
};

// ============================================
// UPLOAD API
// ============================================
export const uploadAPI = {
    uploadFiles: async (files, onProgress) => {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        try {
            return (await api.post('/upload/files', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: onProgress,
            })).data;
        } catch { return { projectId: 'mock-' + Date.now(), projectName: files[0]?.name || 'Project' }; }
    },
    uploadProject: async (file, onProgress) => {
        const formData = new FormData();
        formData.append('project', file);
        try {
            return (await api.post('/upload/project', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: onProgress,
            })).data;
        } catch { return { projectId: 'mock-' + Date.now(), projectName: file?.name || 'Project' }; }
    },
    uploadGitHub: async (url) => {
        try { return (await api.post('/upload/github', { url })).data; }
        catch { return { projectId: 'github-' + Date.now(), projectName: url.split('/').pop() }; }
    },
    uploadDrive: async (url) => {
        try { return (await api.post('/upload/drive', { url })).data; }
        catch { return { projectId: 'drive-' + Date.now(), projectName: 'Drive Project' }; }
    },
    uploadLink: async (url) => {
        try { return (await api.post('/upload/link', { url })).data; }
        catch { return { projectId: 'link-' + Date.now(), projectName: 'Link Project' }; }
    },
    getAnalysis: async (projectId) => {
        try { return (await api.get(`/upload/${projectId}/analyze`)).data; }
        catch { return { healthScore: 85 }; }
    },
    getHistory: async () => {
        try { return (await api.get('/upload/history')).data; }
        catch { return []; }
    },
    deleteProject: async (projectId) => {
        try { return (await api.delete(`/upload/${projectId}`)).data; }
        catch { return { success: true }; }
    },
};

// ============================================
// PIPELINE API — UPDATED with auto_deploy + run_pipeline
// ============================================
export const pipelineAPI = {
    getAll: async () => {
        try {
            const response = await devopsApi.get('/api/devops/deployments');
            const data = response.data;
            if (!data.success) return [];
            const deployments = data.deployments || {};
            const latestByRepo = {};
            Object.values(deployments).forEach(d => {
                const key = `${d.owner || 'user'}/${d.repo || 'app'}`;
                const existing = latestByRepo[key];
                const currentTime = d.deployed_at || 0;
                const existingTime = existing?.deployed_at || 0;
                if (!existing || currentTime > existingTime) latestByRepo[key] = d;
            });
            return Object.values(latestByRepo)
                .map(deploymentToPipeline)
                .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        } catch { return []; }
    },
    getDetails: async (id) => {
        try {
            const all = await pipelineAPI.getAll();
            return all.find(p => p.id === id) || null;
        } catch { return null; }
    },
    // ⭐ UPDATED: Same logic as chat — ci-cd+deploy mode
    create: async (data) => {
        try {
            const mode = data.mode || 'ci-cd+deploy';
            const autoDeploy = data.autoDeploy !== false && data.auto_deploy !== false;
            const shouldDeploy = autoDeploy && mode.includes('deploy');
            const shouldRunPipeline = mode.includes('ci-cd');

            return (await devopsApi.post('/api/devops/pipeline', {
                repo_url: data.repoUrl || data.repo_url,
                mode: mode,
                deploy_method: data.deployMethod || data.deploy_method || 'self-host',
                provider: data.provider || 'self-host',
                max_fix_attempts: data.maxAttempts || data.max_fix_attempts || 50,
                auto_deploy: shouldDeploy,
                run_pipeline: data.run_pipeline !== false ? shouldRunPipeline : false,
            })).data;
        } catch (error) {
            return { success: false, error: error.response?.data?.error || error.message };
        }
    },
    trigger: async (pipelineId, params = {}) => {
        try {
            const url = pipelineId.startsWith('http') ? pipelineId : params.repoUrl;
            if (!url) return { success: false, error: 'No repo URL' };
            return (await devopsApi.post('/api/devops/deploy', { repo_url: url })).data;
        } catch (error) { return { success: false, error: error.message }; }
    },
    retry: async (id) => pipelineAPI.trigger(id),
    cancel: async (id) => {
        try { return (await devopsApi.post(`/api/devops/stop-deploy/${id}`)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
    delete: async (id) => {
        try { return (await devopsApi.post(`/api/devops/delete-deploy/${id}`)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
    getLogs: async () => [],
};

// ============================================
// INFRASTRUCTURE API (legacy)
// ============================================
export const infrastructureAPI = {
    getClusters: async () => {
        try { return (await api.get('/infrastructure/clusters')).data; }
        catch { return []; }
    },
    scaleCluster: async (data) => {
        try { return (await api.post('/infrastructure/scale', data)).data; }
        catch { return { message: 'Scaled' }; }
    },
    getResources: async () => {
        try { return (await api.get('/infrastructure/resources')).data; }
        catch { return { cpu: 45, memory: 62, disk: 34 }; }
    },
};

// ============================================
// MONITORING API
// ============================================
export const monitoringAPI = {
    getMetrics: async (timeRange = '1h') => {
        try { return (await devopsApi.get('/api/monitoring/metrics', { params: { timeRange } })).data; }
        catch { return { success: false, metrics: {}, monitors: [] }; }
    },
    getAlerts: async (status = 'all') => {
        try { return (await devopsApi.get('/api/monitoring/alerts', { params: { status } })).data.alerts || []; }
        catch { return []; }
    },
    acknowledgeAlert: async (alertId) => {
        try { return (await devopsApi.post(`/api/monitoring/alerts/${alertId}/acknowledge`)).data; }
        catch { return { status: 'acknowledged' }; }
    },
    getHealth: async () => {
        try { return (await devopsApi.get('/api/monitoring/health')).data; }
        catch { return { status: 'healthy', services: { total: 0, healthy: 0 } }; }
    },
    getMonitors: async () => {
        try { return (await devopsApi.get('/api/monitoring/monitors')).data.monitors || []; }
        catch { return []; }
    },
    getMonitor: async (id) => {
        try { return (await devopsApi.get(`/api/monitoring/monitors/${id}`)).data.monitor; }
        catch { return null; }
    },
    stopMonitor: async (id) => {
        try { return (await devopsApi.post(`/api/monitoring/monitors/${id}/stop`)).data; }
        catch { return { success: false }; }
    },
    deleteMonitor: async (id) => {
        try { return (await devopsApi.delete(`/api/monitoring/monitors/${id}`)).data; }
        catch { return { success: false }; }
    },
    getInfrastructure: async () => {
        try { return (await devopsApi.get('/api/monitoring/infrastructure')).data.infrastructure || { services: [] }; }
        catch { return { services: [] }; }
    },
};

// ============================================
// 🏗️ INFRA API — Premium + Agentic AI
// ============================================
export const infraAPI = {
    getUnified: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/unified')).data; }
        catch {
            return {
                success: false, services: [],
                stats: { total_services: 0, total_replicas: 0, avg_cpu: 0, avg_memory: 0 },
                health: { score: 100, status: 'excellent', details: {} },
                high_performance: {}, agent: null,
            };
        }
    },
    getNodes: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/nodes')).data.nodes || []; }
        catch { return []; }
    },
    getContainers: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/containers')).data.containers || []; }
        catch { return []; }
    },
    getMetrics: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/metrics')).data.metrics || {}; }
        catch { return {}; }
    },
    getInsights: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/insights')).data.insights || []; }
        catch { return []; }
    },
    applyInsight: async (insightId) => {
        try { return (await devopsApi.post('/api/monitoring/infra/apply-insight', { insight_id: insightId })).data; }
        catch (e) { return { success: false, error: e.message }; }
    },
    dismissInsight: async (insightId) => {
        try { return (await devopsApi.post('/api/monitoring/infra/dismiss-insight', { insight_id: insightId })).data; }
        catch { return { success: false }; }
    },
    getPredictions: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/predictions')).data.predictions || []; }
        catch { return []; }
    },
    getCostSavings: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/cost-savings')).data.cost_savings || []; }
        catch { return []; }
    },
    getActionLog: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/action-log')).data.actions || []; }
        catch { return []; }
    },
    getEvents: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/events')).data.events || []; }
        catch { return []; }
    },
    chat: async (message) => {
        try { return (await devopsApi.post('/api/monitoring/infra/chat', { message })).data; }
        catch (e) { return { success: false, error: e.message }; }
    },
    rootCause: async (service, error) => {
        try { return (await devopsApi.post('/api/monitoring/infra/rca', { service, error })).data; }
        catch { return { success: false }; }
    },
    getAutoScale: async (service = null) => {
        try {
            const params = service ? { service } : {};
            return (await devopsApi.get('/api/monitoring/infra/auto-scale', { params })).data.rules || {};
        } catch { return {}; }
    },
    setAutoScale: async (data) => {
        try { return (await devopsApi.post('/api/monitoring/infra/auto-scale', data)).data; }
        catch { return { success: false }; }
    },

    getAgentState: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/agent/state')).data; }
        catch {
            return {
                mode: 'off', running: false, total_decisions: 0, total_actions: 0,
                success_rate: 0, confidence_threshold: 0.75, pending_count: 0,
                tools_count: 0, safety: {},
            };
        }
    },
    setAgentMode: async (mode) => {
        try { return (await devopsApi.post('/api/monitoring/infra/agent/mode', { mode })).data; }
        catch { return { success: false }; }
    },
    setConfidenceThreshold: async (threshold) => {
        try { return (await devopsApi.post('/api/monitoring/infra/agent/confidence', { threshold })).data; }
        catch { return { success: false }; }
    },
    getDecisions: async (limit = 30) => {
        try { return (await devopsApi.get('/api/monitoring/infra/agent/decisions', { params: { limit } })).data.decisions || []; }
        catch { return []; }
    },
    executeDecision: async (decisionId) => {
        try { return (await devopsApi.post('/api/monitoring/infra/agent/execute', { decision_id: decisionId })).data; }
        catch { return { success: false }; }
    },
    getTools: async () => {
        try { return (await devopsApi.get('/api/monitoring/infra/agent/tools')).data.tools || []; }
        catch { return []; }
    },
};

// ============================================
// TRAINING API
// ============================================
export const trainingAPI = {
    getModels: async () => {
        try { return (await api.get('/training/models')).data; }
        catch { return []; }
    },
    startTraining: async (config) => {
        try { return (await api.post('/training/train', config)).data; }
        catch { return { success: true, training_id: 'train-' + Date.now() }; }
    },
    getStatus: async (trainingId) => {
        try { return (await api.get(`/training/${trainingId}/status`)).data; }
        catch { return { status: 'running', progress: 50 }; }
    },
    stopTraining: async (id) => {
        try { return (await api.post(`/training/${id}/stop`)).data; }
        catch { return { success: true }; }
    },
    deployModel: async (modelId) => {
        try { return (await api.post('/training/deploy', { model_id: modelId })).data; }
        catch { return { success: true }; }
    },
    getVersions: async () => {
        try { return (await api.get('/training/versions')).data; }
        catch { return []; }
    },
};

// ============================================
// SETTINGS API
// ============================================
export const settingsAPI = {
    getSettings: async () => {
        try { return (await api.get('/settings')).data; }
        catch {
            return {
                general: { language: 'en', timezone: 'UTC' },
                appearance: { theme: 'dark' },
                notifications: { emailNotifications: true },
                security: { twoFactorAuth: false },
                integrations: {},
            };
        }
    },
    updateSettings: async (settings) => {
        try { return (await api.put('/settings', settings)).data; }
        catch { return { success: true }; }
    },
    getAuditLogs: async (limit = 50, offset = 0) => {
        try { return (await api.get('/settings/audit-logs', { params: { limit, offset } })).data; }
        catch { return []; }
    },
    connectIntegration: async (provider, data) => {
        try { return (await api.post(`/settings/integrations/${provider}`, data)).data; }
        catch { return { success: true }; }
    },
    disconnectIntegration: async (provider) => {
        try { return (await api.delete(`/settings/integrations/${provider}`)).data; }
        catch { return { success: true }; }
    },
};

// ============================================
// ACTION API
// ============================================
export const actionAPI = {
    getAll: async (type = null, status = null) => {
        try {
            const params = {};
            if (type) params.type = type;
            if (status) params.status = status;
            return (await devopsApi.get('/api/devops/actions', { params })).data.actions || [];
        } catch { return []; }
    },
    getOne: async (actionId) => {
        try { return (await devopsApi.get(`/api/devops/actions/${actionId}`)).data.action; }
        catch { return null; }
    },
    delete: async (actionId) => {
        try { return (await devopsApi.delete(`/api/devops/actions/${actionId}`)).data; }
        catch { return { success: false }; }
    },
    monitor: async (payload) => {
        try { return (await devopsApi.post('/api/devops/action/monitor', payload)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
    scale: async (payload) => {
        try { return (await devopsApi.post('/api/devops/action/scale', payload)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
    security: async (payload) => {
        try { return (await devopsApi.post('/api/devops/action/security', payload)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
    fixCode: async (payload) => {
        try { return (await devopsApi.post('/api/devops/action/fix-code', payload)).data; }
        catch (error) { return { success: false, error: error.message }; }
    },
};

// ============================================
// DEPLOY API
// ============================================
export const deployAPI = {
    deploy: async (payload) => {
        try {
            return (await devopsApi.post('/api/devops/deploy', {
                repo_url: payload.repoUrl || payload.repo_url,
                deploy_type: payload.deployType || 'auto',
                provider: payload.provider || 'self-host',
                user_id: payload.user_id || 'demo_user',
                project_id: payload.project_id || 'default',
                project_name: payload.project_name || 'Unknown',
            })).data;
        } catch (error) { return { success: false, error: error.message }; }
    },
    listDeployments: async () => {
        try { return (await devopsApi.get('/api/devops/deployments')).data; }
        catch { return { success: false, deployments: {} }; }
    },
    stop: async (deployId) => {
        try { return (await devopsApi.post(`/api/devops/stop-deploy/${deployId}`)).data; }
        catch { return { success: false }; }
    },
    delete: async (deployId) => {
        try { return (await devopsApi.post(`/api/devops/delete-deploy/${deployId}`)).data; }
        catch { return { success: false }; }
    },
};

// ============================================
// GITHUB API
// ============================================
export const githubAPI = {
    connect: async (payload) => {
        try { return (await api.post('/github/connect', payload)).data; }
        catch { return { success: true }; }
    },
    listRepos: async () => {
        try { return (await api.get('/github/repos')).data; }
        catch { return []; }
    },
    analyzeRepo: async (repoFullName) => {
        try { return (await api.post(`/github/analyze/${repoFullName}`)).data; }
        catch { return { healthScore: 78 }; }
    },
    autoFix: async (payload) => {
        try { return (await api.post('/github/autofix', payload)).data; }
        catch { return { success: true }; }
    },
    createPR: async (payload) => {
        try { return (await api.post('/github/pr', payload)).data; }
        catch { return { success: true }; }
    },
};

export default api;