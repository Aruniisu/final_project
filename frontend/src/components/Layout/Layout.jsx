import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import Footer from './Footer';
import './Layout.css';
import {
  FiHome,
  FiMessageSquare,
  FiGitBranch,
  FiServer,
  FiActivity,
  FiCpu,
  FiSettings,
  FiLogOut,
  FiSun,
  FiMoon,
  FiMenu,
  FiX,
  FiBell,
  FiUser,
} from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import toast from 'react-hot-toast';

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: FiHome },
    { path: '/chat', label: 'AI Assistant', icon: FaRobot },
    { path: '/pipelines', label: 'Pipelines', icon: FiGitBranch },
    { path: '/infrastructure', label: 'Infrastructure', icon: FiServer },
    { path: '/monitoring', label: 'Monitoring', icon: FiActivity },
    { path: '/training', label: 'Model Training', icon: FiCpu },
    { path: '/settings', label: 'Settings', icon: FiSettings },
  ];

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) setIsSidebarOpen(false);
  };

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="layout-container">
      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {isSidebarOpen && (
          <motion.aside
            initial={isMobile ? { x: -280 } : { x: 0 }}
            animate={{ x: 0 }}
            exit={isMobile ? { x: -280 } : { x: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className={`layout-sidebar ${isSidebarOpen ? 'layout-sidebar-open' : ''}`}
          >
            {/* Logo */}
            <div className="layout-sidebar-header">
              <div className="layout-sidebar-logo">
                <div className="layout-sidebar-logo-icon">
                  <FaRobot />
                </div>
                <div>
                  <h1 className="layout-sidebar-logo-title">Smart DevOps</h1>
                  <p className="layout-sidebar-logo-subtitle">AI Assistant</p>
                </div>
              </div>
              {isMobile && (
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  className="layout-sidebar-close-btn"
                >
                  <FiX />
                </button>
              )}
            </div>

            {/* Navigation */}
            <nav className="layout-sidebar-nav">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                return (
                  <button
                    key={item.path}
                    onClick={() => handleNavigation(item.path)}
                    className={`layout-sidebar-nav-item ${active ? 'layout-sidebar-nav-item-active' : ''}`}
                  >
                    <Icon className="layout-sidebar-nav-item-icon" />
                    <span className="layout-sidebar-nav-item-label">{item.label}</span>
                    {active && <span className="layout-sidebar-nav-item-indicator" />}
                  </button>
                );
              })}
            </nav>

            {/* Sidebar Footer */}
            <div className="layout-sidebar-footer">
              <div className="layout-sidebar-user">
                <div className="layout-sidebar-user-avatar">
                  {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div className="layout-sidebar-user-info">
                  <p className="layout-sidebar-user-name">{user?.name || 'User'}</p>
                  <p className="layout-sidebar-user-role">{user?.role || 'DevOps Engineer'}</p>
                </div>
                <button
                  onClick={toggleTheme}
                  className="layout-sidebar-user-theme-btn"
                >
                  {theme === 'dark' ? <FiSun /> : <FiMoon />}
                </button>
              </div>
              <button onClick={handleLogout} className="layout-sidebar-logout-btn">
                <FiLogOut />
                Logout
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="layout-main">
        {/* Header */}
        <header className="layout-header">
          <div className="layout-header-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="layout-header-menu-btn"
            >
              {isSidebarOpen ? <FiX /> : <FiMenu />}
            </button>
            <h2 className="layout-header-title">
              {navItems.find(item => isActive(item.path))?.label || 'Dashboard'}
            </h2>
          </div>
          <div className="layout-header-right">
            <button className="layout-header-btn">
              <FiBell />
              <span className="layout-header-btn-badge"></span>
            </button>
            <button className="layout-header-btn">
              <FiUser />
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="layout-content">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="layout-content-scroll"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Footer - Now at bottom */}
        <div className="layout-footer">
          <Footer />
        </div>
      </div>

      {/* Mobile Overlay */}
      {isMobile && isSidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setIsSidebarOpen(false)}
          className="layout-overlay"
        />
      )}
    </div>
  );
};

export default Layout;