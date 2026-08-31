import React from 'react';
import { FaHeart, FaGithub, FaTwitter, FaLinkedin, FaYoutube } from 'react-icons/fa';
import { FiMail } from 'react-icons/fi';
import './Footer.css';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  const { user } = useAuth();
  const { theme } = useTheme();

  return (
    <footer className="footer-container">
      <div className="footer-content">
        {/* Left Section - Copyright */}
        <div className="footer-left">
          <div className="footer-copyright">
            <span>© {currentYear}</span>
            <span className="footer-copyright-separator">•</span>
            <span className="footer-copyright-separator">Smart DevOps Assistant</span>
            <span className="footer-copyright-separator">•</span>
            <span className="footer-heart-text">
              Made with <FaHeart className="footer-heart" /> for developers
            </span>
          </div>
        </div>

        {/* Center Section - Status */}
        <div className="footer-center">
          <div className="footer-status-item">
            <span className="footer-status-dot footer-status-dot-online"></span>
            <span className="footer-status-label">All systems go</span>
          </div>
          <div className="footer-status-item">
            <span className="footer-status-dot footer-status-dot-primary"></span>
            <span className="footer-status-label">v2.3.1</span>
          </div>
          <div className="footer-status-item">
            <span className="footer-status-dot footer-status-dot-accent"></span>
            <span className="footer-status-label">AI Ready</span>
          </div>
        </div>

        {/* Right Section - Social Links */}
        <div className="footer-right">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-social-link"
            aria-label="GitHub"
          >
            <FaGithub />
          </a>
          <a
            href="https://twitter.com"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-social-link"
            aria-label="Twitter"
          >
            <FaTwitter />
          </a>
          <a
            href="https://linkedin.com"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-social-link"
            aria-label="LinkedIn"
          >
            <FaLinkedin />
          </a>
          <a
            href="https://youtube.com"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-social-link"
            aria-label="YouTube"
          >
            <FaYoutube />
          </a>
          <a
            href="mailto:support@smartdevops.com"
            className="footer-social-link"
            aria-label="Email"
          >
            <FiMail />
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;