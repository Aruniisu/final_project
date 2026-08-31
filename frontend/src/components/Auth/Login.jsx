import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { FaRobot, FaGoogle, FaGithub, FaApple } from 'react-icons/fa';
import { FiMail, FiLock, FiEye, FiEyeOff, FiArrowRight, FiCheck, FiTrendingUp, FiShield, FiZap } from 'react-icons/fi';
import { BsStars } from 'react-icons/bs';
import '../../styles/main.css';
import './Login.css';

const Login = () => {
    const [email, setEmail] = useState('demo@example.com');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [focused, setFocused] = useState(null);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const result = await login(email, password);
        setLoading(false);
        if (result.success) {
            navigate('/dashboard');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] relative overflow-hidden">
            {/* Animated Background Orbs */}
            <div className="absolute top-[-30%] right-[-10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 blur-3xl animate-pulse" />
            <div className="absolute bottom-[-30%] left-[-10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 blur-3xl animate-pulse delay-1000" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-purple-500/5 to-pink-500/5 blur-3xl" />

            {/* Main Card */}
            <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="relative z-10 w-full max-w-5xl grid lg:grid-cols-5 gap-0 bg-white/5 backdrop-blur-2xl backdrop-saturate-200 rounded-3xl shadow-2xl shadow-black/50 border border-white/10 overflow-hidden"
            >
                {/* Left Section - Form (3 columns) */}
                <div className="lg:col-span-3 p-8 lg:p-12">
                    {/* Header with Logo */}
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1, duration: 0.5 }}
                        className="flex items-center justify-between mb-10"
                    >
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                                <FaRobot className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-white">
                                    Smart<span className="text-purple-400">DevOps</span>
                                </h1>
                                <p className="text-xs text-white/40">AI-Powered Platform</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                            <BsStars className="w-3.5 h-3.5 text-purple-400" />
                            <span className="text-xs text-white/50">v2.3.1</span>
                        </div>
                    </motion.div>

                    {/* Welcome Section */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                        className="mb-8"
                    >
                        <h2 className="text-3xl lg:text-4xl font-bold text-white mb-2">
                            Welcome Back 👋
                        </h2>
                        <p className="text-white/50 text-sm">
                            Sign in to continue managing your infrastructure
                        </p>
                    </motion.div>

                    {/* Social Login */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3, duration: 0.5 }}
                        className="grid grid-cols-3 gap-3 mb-6"
                    >
                        <button className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group">
                            <FaGoogle className="w-4 h-4 text-red-400" />
                            <span className="text-sm text-white/60 group-hover:text-white transition-colors hidden sm:inline">Google</span>
                        </button>
                        <button className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group">
                            <FaGithub className="w-4 h-4 text-white/60" />
                            <span className="text-sm text-white/60 group-hover:text-white transition-colors hidden sm:inline">GitHub</span>
                        </button>
                        <button className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group">
                            <FaApple className="w-4 h-4 text-white/60" />
                            <span className="text-sm text-white/60 group-hover:text-white transition-colors hidden sm:inline">Apple</span>
                        </button>
                    </motion.div>

                    {/* Divider */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-white/10"></div>
                        </div>
                        <div className="relative flex justify-center">
                            <span className="px-4 bg-transparent text-xs text-white/30">or continue with email</span>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4, duration: 0.5 }}
                        >
                            <label className="block text-sm font-medium text-white/60 mb-1.5">
                                Email Address
                            </label>
                            <div className={`relative group transition-all duration-300 ${focused === 'email' ? 'scale-[1.01]' : ''}`}>
                                <FiMail className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${
                                    focused === 'email' ? 'text-purple-400' : 'text-white/30'
                                }`} />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    onFocus={() => setFocused('email')}
                                    onBlur={() => setFocused(null)}
                                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-purple-500/50 focus:ring-4 focus:ring-purple-500/10 text-white placeholder-white/30 outline-none transition-all duration-300"
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5, duration: 0.5 }}
                        >
                            <label className="block text-sm font-medium text-white/60 mb-1.5">
                                Password
                            </label>
                            <div className={`relative group transition-all duration-300 ${focused === 'password' ? 'scale-[1.01]' : ''}`}>
                                <FiLock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${
                                    focused === 'password' ? 'text-purple-400' : 'text-white/30'
                                }`} />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    onFocus={() => setFocused('password')}
                                    onBlur={() => setFocused(null)}
                                    className="w-full pl-12 pr-14 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-purple-500/50 focus:ring-4 focus:ring-purple-500/10 text-white placeholder-white/30 outline-none transition-all duration-300"
                                    placeholder="Enter your password"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                                >
                                    {showPassword ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
                                </button>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6, duration: 0.5 }}
                            className="flex items-center justify-between"
                        >
                            <label className="flex items-center gap-2 cursor-pointer group">
                                <div className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all duration-300 ${
                                    rememberMe 
                                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 border-purple-500' 
                                        : 'border-white/20 hover:border-white/40'
                                }`}>
                                    {rememberMe && <FiCheck className="w-3.5 h-3.5 text-white" />}
                                </div>
                                <input
                                    type="checkbox"
                                    checked={rememberMe}
                                    onChange={(e) => setRememberMe(e.target.checked)}
                                    className="hidden"
                                />
                                <span className="text-sm text-white/40 group-hover:text-white/60 transition-colors">
                                    Remember me
                                </span>
                            </label>
                            <Link to="/forgot-password" className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                                Forgot password?
                            </Link>
                        </motion.div>

                        <motion.button
                            type="submit"
                            disabled={loading}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.7, duration: 0.5 }}
                            className="relative w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg hover:shadow-purple-500/30 transition-all duration-300 group overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span className="relative z-10 flex items-center justify-center gap-2 text-sm">
                                {loading ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Signing in...
                                    </>
                                ) : (
                                    <>
                                        Sign In
                                        <FiArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </span>
                            <div className="absolute inset-0 bg-gradient-to-r from-pink-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        </motion.button>
                    </form>

                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.8, duration: 0.5 }}
                        className="text-center text-sm text-white/30 mt-6"
                    >
                        Don't have an account?{' '}
                        <Link to="/register" className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
                            Sign Up
                        </Link>
                    </motion.p>
                </div>

                {/* Right Section - Branding (2 columns) */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3, duration: 0.6 }}
                    className="hidden lg:flex lg:col-span-2 flex-col justify-between p-10 bg-gradient-to-br from-purple-500/10 via-pink-500/5 to-transparent border-l border-white/5 relative overflow-hidden"
                >
                    {/* Decorative elements */}
                    <div className="absolute top-[-50%] right-[-50%] w-[400px] h-[400px] rounded-full bg-purple-500/10 blur-3xl" />
                    <div className="absolute bottom-[-50%] left-[-50%] w-[400px] h-[400px] rounded-full bg-pink-500/10 blur-3xl" />

                    <div className="relative z-10">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-500/30">
                            <FaRobot className="w-8 h-8 text-white" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mt-6">
                            Smart DevOps Assistant
                        </h3>
                        <p className="text-white/40 text-sm mt-2 leading-relaxed">
                            AI-powered automation for modern DevOps workflows. Deploy, monitor, and scale with confidence.
                        </p>
                    </div>

                    <div className="relative z-10 space-y-4">
                        {/* Stats */}
                        <div className="grid grid-cols-3 gap-3">
                            <div className="text-center p-3 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-xl font-bold text-white">99.9%</p>
                                <p className="text-xs text-white/30">Uptime</p>
                            </div>
                            <div className="text-center p-3 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-xl font-bold text-white">1.2k</p>
                                <p className="text-xs text-white/30">Deployments</p>
                            </div>
                            <div className="text-center p-3 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-xl font-bold text-white">45</p>
                                <p className="text-xs text-white/30">Services</p>
                            </div>
                        </div>

                        {/* Features */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all duration-300">
                                <div className="p-1.5 rounded-lg bg-purple-500/20">
                                    <FiZap className="w-3.5 h-3.5 text-purple-400" />
                                </div>
                                <span className="text-sm text-white/60">AI-Powered Automation</span>
                            </div>
                            <div className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all duration-300">
                                <div className="p-1.5 rounded-lg bg-green-500/20">
                                    <FiShield className="w-3.5 h-3.5 text-green-400" />
                                </div>
                                <span className="text-sm text-white/60">Enterprise Security</span>
                            </div>
                            <div className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all duration-300">
                                <div className="p-1.5 rounded-lg bg-blue-500/20">
                                    <FiTrendingUp className="w-3.5 h-3.5 text-blue-400" />
                                </div>
                                <span className="text-sm text-white/60">Real-time Monitoring</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-white/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
                            <span>All systems operational</span>
                            <span className="w-px h-3 bg-white/10"></span>
                            <span>Auto-upgrade enabled</span>
                        </div>
                    </div>
                </motion.div>
            </motion.div>

            {/* Footer */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 text-xs text-white/10">
                © 2024 SmartDevOps. All rights reserved.
            </div>
        </div>
    );
};

export default Login;