import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
  FiHome,
  FiMessageSquare,
  FiUpload,
  FiGitBranch,
  FiActivity,
  FiCpu,
  FiSettings,
  FiLogOut,
  FiServer,
  FiBarChart2,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { logout } = useAuth();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: FiHome },
    { path: '/chat', label: 'AI Assistant', icon: FaRobot },
    { path: '/pipelines', label: 'Pipelines', icon: FiGitBranch },
    { path: '/infrastructure', label: 'Infrastructure', icon: FiServer },
    { path: '/monitoring', label: 'Monitoring', icon: FiActivity },
    { path: '/logs', label: 'Log Analysis', icon: FiBarChart2 },
    { path: '/training', label: 'Model Training', icon: FiCpu },
    { path: '/settings', label: 'Settings', icon: FiSettings },
  ];

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    onClose();
  };

  const isActive = (path) => location.pathname === path;

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:relative z-50 h-full w-[280px] bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl backdrop-saturate-150 border-r border-slate-200/50 dark:border-slate-700/50 shadow-xl shadow-slate-200/20 dark:shadow-slate-900/30 flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 p-4 border-b border-slate-200/50 dark:border-slate-700/50">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30 flex-shrink-0">
            <FaRobot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
              Smart DevOps
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">AI-Powered Assistant</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  active
                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/30'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-white' : ''}`} />
                <span className="font-medium text-sm">{item.label}</span>
                {active && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="ml-auto w-1.5 h-8 bg-white rounded-full"
                    initial={false}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="p-4 border-t border-slate-200/50 dark:border-slate-700/50">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <FiLogOut className="w-5 h-5" />
            <span className="font-medium text-sm">Logout</span>
          </button>
          
          <div className="mt-3 p-3 rounded-xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 border border-primary-500/20 dark:border-primary-400/20">
            <p className="text-xs text-slate-600 dark:text-slate-300">
              <span className="font-semibold">v2.3.1</span> • Auto-upgrade enabled
            </p>
            <div className="flex items-center gap-1 mt-1">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
              <span className="text-xs text-slate-500 dark:text-slate-400">All systems operational</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;