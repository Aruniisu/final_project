import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FiCpu,
  FiHardDrive,
  FiActivity,
  FiTrendingUp,
  FiTrendingDown,
  FiBarChart2,
} from 'react-icons/fi';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MetricCard = ({ title, value, change, icon: Icon, color, maxValue, unit }) => {
  const isPositive = change > 0;

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-xl font-bold text-slate-900 dark:text-white mt-1">
            {value}{unit}
          </p>
          {change !== undefined && (
            <div className={`flex items-center gap-0.5 mt-0.5 text-xs ${isPositive ? 'text-success' : 'text-error'}`}>
              {isPositive ? <FiTrendingUp className="w-3 h-3" /> : <FiTrendingDown className="w-3 h-3" />}
              <span>{isPositive ? '+' : ''}{change}%</span>
            </div>
          )}
        </div>
        <div className={`p-2.5 rounded-xl ${color} bg-opacity-10`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
      </div>
      {maxValue && (
        <div className="mt-2">
          <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${color}`}
              style={{ width: `${(value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const ResourceMetrics = ({ clusters = [] }) => {
  const [metrics, setMetrics] = useState({
    cpu: { value: 0, change: 0, max: 100 },
    memory: { value: 0, change: 0, max: 100 },
    disk: { value: 0, change: 0, max: 100 },
    network: { value: 0, change: 0 },
  });
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    if (clusters.length > 0) {
      // Calculate average metrics
      const avgCpu = clusters.reduce((acc, c) => acc + (c.cpuUsage || 0), 0) / clusters.length;
      const avgMemory = clusters.reduce((acc, c) => acc + (c.memoryUsage || 0), 0) / clusters.length;
      const avgDisk = clusters.reduce((acc, c) => acc + (c.diskUsage || 0), 0) / clusters.length;

      setMetrics({
        cpu: { value: Math.round(avgCpu), change: 5.2, max: 100 },
        memory: { value: Math.round(avgMemory), change: -2.1, max: 100 },
        disk: { value: Math.round(avgDisk), change: 3.8, max: 100 },
        network: { value: 12.3, change: 8.5 },
      });
    }
  }, [clusters]);

  useEffect(() => {
    // Generate mock history data
    const generateHistory = () => {
      const data = [];
      const now = Date.now();
      for (let i = 30; i >= 0; i--) {
        data.push({
          timestamp: now - i * 60000,
          cpu: 30 + Math.random() * 40,
          memory: 40 + Math.random() * 35,
          disk: 20 + Math.random() * 30,
        });
      }
      setHistoryData(data);
    };
    generateHistory();
  }, []);

  const chartData = {
    labels: historyData.map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'CPU Usage',
        data: historyData.map(d => d.cpu),
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
        pointRadius: 2,
        pointHoverRadius: 4,
      },
      {
        label: 'Memory Usage',
        data: historyData.map(d => d.memory),
        borderColor: '#d946ef',
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return null;
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(217, 70, 239, 0.3)');
          gradient.addColorStop(1, 'rgba(217, 70, 239, 0.02)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      },
      {
        label: 'Disk Usage',
        data: historyData.map(d => d.disk),
        borderColor: '#10b981',
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return null;
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
          gradient.addColorStop(1, 'rgba(16, 185, 129, 0.02)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'line',
          padding: 20,
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
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
          }
        }
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
          drawBorder: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 10 },
          callback: function(value) { return value + '%'; },
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#94a3b8',
          font: { size: 10 },
          maxTicksLimit: 6,
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
        <FiBarChart2 className="text-primary-500" />
        Resource Metrics
      </h3>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          title="CPU Usage"
          value={metrics.cpu.value}
          change={metrics.cpu.change}
          icon={FiCpu}
          color="text-primary-500"
          maxValue={metrics.cpu.max}
          unit="%"
        />
        <MetricCard
          title="Memory Usage"
          value={metrics.memory.value}
          change={metrics.memory.change}
          icon={FiActivity}
          color="text-accent-500"
          maxValue={metrics.memory.max}
          unit="%"
        />
        <MetricCard
          title="Disk Usage"
          value={metrics.disk.value}
          change={metrics.disk.change}
          icon={FiHardDrive}
          color="text-success-500"
          maxValue={metrics.disk.max}
          unit="%"
        />
        <MetricCard
          title="Network I/O"
          value={metrics.network.value}
          change={metrics.network.change}
          icon={FiTrendingUp}
          color="text-warning-500"
          unit=" MB/s"
        />
      </div>

      {/* History Chart */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Resource Usage History
          </h4>
          <span className="text-xs text-slate-500 dark:text-slate-400">Last 30 minutes</span>
        </div>
        <div className="h-48">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>

      {/* Cluster Health Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass-card p-3 text-center">
          <div className="flex items-center justify-center gap-1">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Healthy</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white">
            {clusters.filter(c => c.status === 'healthy').length}
          </p>
        </div>
        <div className="glass-card p-3 text-center">
          <div className="flex items-center justify-center gap-1">
            <span className="w-2 h-2 rounded-full bg-warning animate-pulse"></span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Warning</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white">
            {clusters.filter(c => c.status === 'warning').length}
          </p>
        </div>
        <div className="glass-card p-3 text-center">
          <div className="flex items-center justify-center gap-1">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse"></span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Error</span>
          </div>
          <p className="text-lg font-bold text-slate-900 dark:text-white">
            {clusters.filter(c => c.status === 'error').length}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResourceMetrics;