import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './LeftSidebar.css';
import { 
  FaRobot, 
  FaFolder, 
  FaCodeBranch,
  FaServer, 
  FaDatabase,
  FaCheckCircle,
  FaExclamationTriangle,
  FaClock,
  FaCode,
  FaDocker,
  FaKubernetes,
  FaCloud,
  FaShieldAlt,
  FaCog,
  FaTerminal,
  FaNetworkWired,
  FaMemory,
  FaMicrochip,
  FaHardDrive,
  FaGlobe
} from 'react-icons/fa';
import { FiActivity, FiCpu, FiServer as FiServerIcon, FiZap } from 'react-icons/fi';
import { BsLightningCharge, BsShieldCheck } from 'react-icons/bs';

const LeftSidebar = ({ 
  selectedProject, 
  uploadedProjects, 
  systemHealth,
  executionStatus,
  onSelectProject 
}) => {
  const [expanded, setExpanded] = useState('context');

  const healthItems = [
    { label: 'Flask Server', status: systemHealth?.flask || 'Online', icon: FaServer },
    { label: 'MongoDB', status: systemHealth?.mongodb || 'Connected', icon: FaDatabase },
    { label: 'WebSocket', status: systemHealth?.websocket || 'Connected', icon: FaNetworkWired },
    { label: 'AI Agents', status: systemHealth?.agents || 'Ready', icon: FaRobot },
  ];

  const getStatusColor = (status) => {
    if (status === 'Online' || status === 'Connected' || status === 'Ready') return 'text-success-500';
    if (status === 'Warning' || status === 'Degraded') return 'text-warning-500';
    return 'text-error-500';
  };

  const getStatusDot = (status) => {
    if (status === 'Online' || status === 'Connected' || status === 'Ready') return 'bg-success-500';
    if (status === 'Warning' || status === 'Degraded') return 'bg-warning-500';
    return 'bg-error-500';
  };

  return (
    <div className="w-[280px] h-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-700/50 flex flex-col flex-shrink-0 overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <FaRobot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">Smart DevOps</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Agentic AI Platform</p>
          </div>
        </div>
      </div>

      {/* Active Context */}
      <div className="p-4 border-b border-slate-200/50 dark:border-slate-700/50">
        <button
          onClick={() => setExpanded(expanded === 'context' ? '' : 'context')}
          className="flex items-center justify-between w-full"
        >
          <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Active Context
          </h3>
          <span className="text-slate-400">{expanded === 'context' ? '▼' : '▶'}</span>
        </button>
        
        <AnimatePresence>
          {expanded === 'context' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-3 space-y-2"
            >
              {selectedProject ? (
                <>
                  <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-slate-700/50">
                    <div className="flex items-center gap-2">
                      <FaFolder className="w-4 h-4 text-primary-500" />
                      <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
                        {selectedProject.projectName}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <FaCodeBranch className="w-3 h-3" />
                        {selectedProject.branch || 'main'}
                      </span>
                      <span className="flex items-center gap-1">
                        <FaCode className="w-3 h-3" />
                        {selectedProject.language || 'JavaScript'}
                      </span>
                      {selectedProject.analysis && (
                        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                          selectedProject.analysis.healthScore >= 80 ? 'bg-success-500/20 text-success-500' :
                          selectedProject.analysis.healthScore >= 60 ? 'bg-warning-500/20 text-warning-500' :
                          'bg-error-500/20 text-error-500'
                        }`}>
                          Health: {selectedProject.analysis.healthScore}%
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {selectedProject.analysis && (
                    <div className="grid grid-cols-2 gap-1.5 text-xs">
                      <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-center">
                        <span className="text-slate-500 dark:text-slate-400">Issues</span>
                        <p className="font-bold text-slate-900 dark:text-white">
                          {selectedProject.analysis.issues || 0}
                        </p>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-center">
                        <span className="text-slate-500 dark:text-slate-400">Security</span>
                        <p className="font-bold text-slate-900 dark:text-white">
                          {selectedProject.analysis.securityScore || 0}%
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-4 text-sm text-slate-400">
                  <FaFolder className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No project selected</p>
                  <p className="text-xs text-slate-500">Upload a project to get started</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* System Health */}
      <div className="p-4 border-b border-slate-200/50 dark:border-slate-700/50">
        <button
          onClick={() => setExpanded(expanded === 'health' ? '' : 'health')}
          className="flex items-center justify-between w-full"
        >
          <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            System Health
          </h3>
          <span className="text-slate-400">{expanded === 'health' ? '▼' : '▶'}</span>
        </button>
        
        <AnimatePresence>
          {expanded === 'health' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-3 space-y-1.5"
            >
              {healthItems.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center gap-2">
                    <item.icon className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                    <span className="text-sm text-slate-700 dark:text-slate-300">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${getStatusDot(item.status)}`} />
                    <span className={`text-xs font-medium ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
              
              <div className="mt-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Uptime</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">
                    {systemHealth?.uptime || '99.9%'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs mt-1">
                  <span className="text-slate-500 dark:text-slate-400">Agents</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">
                    {systemHealth?.agentsCount || '4'} Active
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Projects List */}
      <div className="flex-1 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
          Projects ({uploadedProjects.length})
        </h3>
        <div className="space-y-1.5">
          {uploadedProjects.length === 0 ? (
            <div className="text-center py-4 text-sm text-slate-400">
              <p>No projects uploaded</p>
            </div>
          ) : (
            uploadedProjects.map((project) => (
              <button
                key={project.projectId}
                onClick={() => onSelectProject(project)}
                className={`w-full text-left p-2.5 rounded-xl transition-all ${
                  selectedProject?.projectId === project.projectId
                    ? 'bg-primary-500/10 border border-primary-500/30'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FaFolder className="w-4 h-4 text-primary-500" />
                  <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {project.projectName}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                  <span>{project.source || 'file'}</span>
                  {project.analysis && (
                    <>
                      <span>•</span>
                      <span>Health: {project.analysis.healthScore}%</span>
                    </>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200/50 dark:border-slate-700/50">
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <BsLightningCharge className="w-3 h-3 text-primary-500" />
          <span>v2.3.1 • Agentic AI</span>
          <span className="w-px h-3 bg-slate-300 dark:bg-slate-600"></span>
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${executionStatus === 'running' ? 'bg-primary-500 animate-pulse' : 'bg-slate-400'}`} />
            {executionStatus === 'running' ? 'Executing' : 'Idle'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LeftSidebar;