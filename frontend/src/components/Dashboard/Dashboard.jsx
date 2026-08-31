import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import '../../styles/main.css';
import './Dashboard.css';
import {
  FiCpu,
  FiGitBranch,
  FiServer,
  FiActivity,
  FiTrendingUp,
  FiTrendingDown,
  FiClock,
  FiAlertCircle,
  FiCheckCircle,
  FiRefreshCw,
  FiBarChart2,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import toast from 'react-hot-toast';
import { assistantAPI } from '../../api/assistant';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// ============================================
// STATS CARD COMPONENT
// ============================================
const StatsCard = ({ title, value, change, icon: Icon, color, subtitle, loading }) => {
  if (loading) {
    return (
      <div className="dashboard-stats-card dashboard-stats-card-loading">
        <div className="dashboard-stats-card-loading-inner">
          <div className="dashboard-stats-card-loading-title"></div>
          <div className="dashboard-stats-card-loading-value"></div>
        </div>
        <div className="dashboard-stats-card-loading-icon"></div>
      </div>
    );
  }

  const isPositive = change > 0;
  const isNegative = change < 0;

  return (
    <div className="dashboard-stats-card">
      <div className="dashboard-stats-card-content">
        <p className="dashboard-stats-card-title">{title}</p>
        <h3 className="dashboard-stats-card-value">{value}</h3>
        {change !== undefined && change !== null && (
          <div className="dashboard-stats-card-change">
            {isPositive && <FiTrendingUp className="dashboard-stats-card-change-icon dashboard-stats-card-change-icon-positive" />}
            {isNegative && <FiTrendingDown className="dashboard-stats-card-change-icon dashboard-stats-card-change-icon-negative" />}
            {!isPositive && !isNegative && <FiTrendingUp className="dashboard-stats-card-change-icon dashboard-stats-card-change-icon-neutral" />}
            <span className={`dashboard-stats-card-change-text ${
              isPositive ? 'dashboard-stats-card-change-text-positive' : 
              isNegative ? 'dashboard-stats-card-change-text-negative' : 
              'dashboard-stats-card-change-text-neutral'
            }`}>
              {isPositive ? '+' : ''}{change}%
            </span>
            <span className="dashboard-stats-card-change-label">vs last week</span>
          </div>
        )}
        {subtitle && <p className="dashboard-stats-card-subtitle">{subtitle}</p>}
      </div>
      <div className={`dashboard-stats-card-icon-wrapper ${color}`}>
        <Icon className="dashboard-stats-card-icon" />
      </div>
    </div>
  );
};

// ============================================
// MAIN DASHBOARD COMPONENT
// ============================================
const Dashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    deployments: { value: 0, change: 0 },
    pipelines: { value: 0, change: 0 },
    services: { value: 0, change: 0 },
    incidents: { value: 0, change: 0 },
    uptime: '99.9%',
    responseTime: '2.3s',
    activeUsers: 0,
    cost: '$0.00',
  });
  const [deploymentData, setDeploymentData] = useState([12, 19, 3, 5, 2, 3, 7]);
  const [incidentData, setIncidentData] = useState([2, 1, 3, 0]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [quickActions, setQuickActions] = useState([]);

  // ============================================
  // FETCH DATA
  // ============================================
  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      await assistantAPI.getStatus();

      setStats({
        deployments: { value: 1247, change: 12.5 },
        pipelines: { value: 89, change: 8.3 },
        services: { value: 45, change: 3.1 },
        incidents: { value: 3, change: -15.2 },
        uptime: '99.92%',
        responseTime: '1.8s',
        activeUsers: 23,
        cost: '$1,247.00',
      });

      setDeploymentData([12, 19, 3, 5, 2, 3, 7]);
      setIncidentData([2, 1, 3, 0]);

      setRecentActivities([
        { id: 1, type: 'deployment', title: 'Frontend deployed to production', status: 'success', time: '2 minutes ago', user: 'John Doe' },
        { id: 2, type: 'pipeline', title: 'Backend API pipeline failed', status: 'failed', time: '5 minutes ago', user: 'Jane Smith' },
        { id: 3, type: 'training', title: 'Model v2.3.1 training completed', status: 'success', time: '15 minutes ago', user: 'AI System' },
        { id: 4, type: 'monitoring', title: 'High CPU usage detected on Production', status: 'warning', time: '25 minutes ago', user: 'Monitor' },
        { id: 5, type: 'deployment', title: 'Staging environment updated', status: 'success', time: '1 hour ago', user: 'DevOps Team' },
      ]);

      setQuickActions([
        { icon: FiGitBranch, label: 'Deploy Now', color: 'primary', action: 'deploy' },
        { icon: FiBarChart2, label: 'View Metrics', color: 'accent', action: 'metrics' },
        { icon: FiAlertCircle, label: 'Check Alerts', color: 'warning', action: 'alerts' },
        { icon: FaRobot, label: 'AI Assistant', color: 'secondary', action: 'chat' },
      ]);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
      setLoading(false);
    }
  };

  // ============================================
  // HANDLERS
  // ============================================
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    toast.success('Dashboard refreshed');
    setTimeout(() => setRefreshing(false), 500);
  };

  const handleQuickAction = (action) => {
    toast.success(`Quick action: ${action.label}`);
  };

  // ============================================
  // CHART CONFIGURATIONS
  // ============================================
  const deploymentChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Deployments',
      data: deploymentData,
      borderColor: '#3b82f6',
      backgroundColor: (context) => {
        const chart = context.chart;
        const { ctx, chartArea } = chart;
        if (!chartArea) return null;
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');
        return gradient;
      },
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#3b82f6',
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
    }],
  };

  const deploymentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(59, 130, 246, 0.2)',
        borderWidth: 1,
        borderRadius: 8,
        padding: 12,
        callbacks: {
          label: function(context) {
            return `${context.parsed.y} deployments`;
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
          drawBorder: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
        },
      },
      x: {
        grid: { display: false },
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  const incidentChartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: incidentData,
      backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
      borderWidth: 0,
      hoverOffset: 8,
    }],
  };

  const incidentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 16,
          usePointStyle: true,
          pointStyle: 'circle',
          font: { size: 11 },
          color: '#94a3b8',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        borderRadius: 8,
        padding: 12,
        callbacks: {
          label: function(context) {
            return `${context.parsed} incidents`;
          }
        }
      },
    },
    cutout: '70%',
  };

  // ============================================
  // HELPERS
  // ============================================
  const statsCards = [
    { title: 'Total Deployments', value: stats.deployments.value.toLocaleString(), change: stats.deployments.change, icon: FiGitBranch, color: 'color-primary', subtitle: `${stats.uptime} uptime` },
    { title: 'Active Pipelines', value: stats.pipelines.value, change: stats.pipelines.change, icon: FiActivity, color: 'color-accent', subtitle: '8 running now' },
    { title: 'Services', value: stats.services.value, change: stats.services.change, icon: FiServer, color: 'color-success', subtitle: '45 healthy' },
    { title: 'Incidents', value: stats.incidents.value, change: stats.incidents.change, icon: FiAlertCircle, color: 'color-error', subtitle: '2 critical' },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'status-success';
      case 'failed': return 'status-error';
      case 'warning': return 'status-warning';
      default: return 'status-info';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <FiCheckCircle className="dashboard-status-icon" />;
      case 'failed': return <FiAlertCircle className="dashboard-status-icon" />;
      case 'warning': return <FiAlertCircle className="dashboard-status-icon" />;
      default: return <FiActivity className="dashboard-status-icon" />;
    }
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h2 className="dashboard-title">Welcome back, {user?.name || 'User'}! 👋</h2>
          <p className="dashboard-subtitle">Here's what's happening with your infrastructure</p>
        </div>
        <div className="dashboard-header-actions">
          <button onClick={handleRefresh} disabled={refreshing} className="dashboard-refresh-btn">
            <FiRefreshCw className={`dashboard-refresh-icon ${refreshing ? 'dashboard-refresh-icon-spinning' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          <div className="dashboard-status-badge">
            <span className="dashboard-status-dot"></span>
            <span>All systems {stats.uptime}</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="dashboard-stats-grid">
        {statsCards.map((stat, index) => (
          <StatsCard
            key={index}
            title={stat.title}
            value={stat.value}
            change={stat.change}
            icon={stat.icon}
            color={stat.color}
            subtitle={stat.subtitle}
            loading={loading}
          />
        ))}
      </div>

      {/* Charts Section */}
      <div className="dashboard-charts-grid">
        <div className="dashboard-chart-card dashboard-chart-card-large">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Deployment Activity</h3>
              <p className="dashboard-chart-subtitle">Last 7 days</p>
            </div>
            <div className="dashboard-chart-legend">
              <span className="dashboard-chart-legend-item">
                <span className="dashboard-chart-legend-color"></span>
                Deployments
              </span>
            </div>
          </div>
          <div className="dashboard-chart-wrapper">
            <Line data={deploymentChartData} options={deploymentChartOptions} />
          </div>
        </div>

        <div className="dashboard-chart-card">
          <div className="dashboard-chart-header">
            <div>
              <h3 className="dashboard-chart-title">Incident Distribution</h3>
              <p className="dashboard-chart-subtitle">By severity</p>
            </div>
          </div>
          <div className="dashboard-chart-wrapper dashboard-chart-doughnut-wrapper">
            <Doughnut data={incidentChartData} options={incidentChartOptions} />
          </div>
        </div>
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="dashboard-two-column-grid">
        {/* Quick Actions */}
        <div className="dashboard-card">
          <h3 className="dashboard-card-title">Quick Actions</h3>
          <div className="dashboard-quick-actions-grid">
            {quickActions.map((action, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleQuickAction(action)}
                className={`dashboard-quick-action-btn dashboard-quick-action-btn-${action.color}`}
              >
                <div className={`dashboard-quick-action-icon dashboard-quick-action-icon-${action.color}`}>
                  <action.icon className="dashboard-quick-action-icon-svg" />
                </div>
                <span className="dashboard-quick-action-label">{action.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3 className="dashboard-card-title">Recent Activity</h3>
            <button className="dashboard-card-view-all">View All</button>
          </div>
          <div className="dashboard-activity-list">
            {recentActivities.map((activity) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`dashboard-activity-item ${getStatusColor(activity.status)}`}
              >
                <div className="dashboard-activity-icon">
                  {getStatusIcon(activity.status)}
                </div>
                <div className="dashboard-activity-content">
                  <p className="dashboard-activity-title">{activity.title}</p>
                  <div className="dashboard-activity-meta">
                    <span>{activity.user}</span>
                    <span className="dashboard-activity-dot"></span>
                    <span>{activity.time}</span>
                  </div>
                </div>
                <span className="dashboard-activity-status">{activity.status}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* System Stats */}
      <div className="dashboard-card">
        <h3 className="dashboard-card-title">System Overview</h3>
        <div className="dashboard-system-stats-grid">
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">CPU Usage</p>
            <p className="dashboard-system-stat-value">34%</p>
            <div className="dashboard-system-stat-bar">
              <div className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-primary" style={{ width: '34%' }}></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Memory Usage</p>
            <p className="dashboard-system-stat-value">67%</p>
            <div className="dashboard-system-stat-bar">
              <div className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-warning" style={{ width: '67%' }}></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Disk Usage</p>
            <p className="dashboard-system-stat-value">45%</p>
            <div className="dashboard-system-stat-bar">
              <div className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-info" style={{ width: '45%' }}></div>
            </div>
          </div>
          <div className="dashboard-system-stat">
            <p className="dashboard-system-stat-label">Network</p>
            <p className="dashboard-system-stat-value">12.3 MB/s</p>
            <div className="dashboard-system-stat-bar">
              <div className="dashboard-system-stat-bar-fill dashboard-system-stat-bar-fill-success" style={{ width: '62%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Version Info */}
      <div className="dashboard-version-info">
        Smart DevOps Assistant v2.3.1 • Auto-upgrade enabled • {new Date().getFullYear()}
      </div>
    </div>
  );
};

export default Dashboard;