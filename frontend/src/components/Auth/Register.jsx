import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { FaRobot, FaGoogle, FaGithub } from 'react-icons/fa';
import { FiMail, FiLock, FiUser, FiEye, FiEyeOff, FiArrowRight, FiCheck } from 'react-icons/fi';
import { BsStars } from 'react-icons/bs';
import toast from 'react-hot-toast';

const Register = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [agreeTerms, setAgreeTerms] = useState(false);
    const [focused, setFocused] = useState(null);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!agreeTerms) {
            toast.error('Please agree to the Terms of Service');
            return;
        }
        if (password !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }
        if (password.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }
        setLoading(true);
        const result = await register(name, email, password);
        setLoading(false);
        if (result.success) {
            navigate('/login');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e] relative overflow-hidden">
            {/* Animated Background Orbs */}
            <div className="absolute top-[-30%] right-[-10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 blur-3xl animate-pulse" />
            <div className="absolute bottom-[-30%] left-[-10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 blur-3xl animate-pulse delay-1000" />

            <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="relative z-10 w-full max-w-2xl bg-white/5 backdrop-blur-2xl backdrop-saturate-200 rounded-3xl shadow-2xl shadow-black/50 border border-white/10 overflow-hidden p-8 lg:p-12"
            >
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, duration: 0.5 }}
                    className="text-center mb-8"
                >
                    <div className="flex items-center justify-center gap-3 mb-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                            <FaRobot className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h2 className="text-2xl lg:text-3xl font-bold text-white">
                        Create Account 🚀
                    </h2>
                    <p className="text-white/40 text-sm mt-1">
                        Start your DevOps automation journey
                    </p>
                </motion.div>

                {/* Social Login */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className="grid grid-cols-2 gap-3 mb-6"
                >
                    <button className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
                        <FaGoogle className="w-4 h-4 text-red-400" />
                        <span className="text-sm text-white/60">Google</span>
                    </button>
                    <button className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
                        <FaGithub className="w-4 h-4 text-white/60" />
                        <span className="text-sm text-white/60">GitHub</span>
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
                        transition={{ delay: 0.3, duration: 0.5 }}
                    >
                        <label className="block text-sm font-medium text-white/60 mb-1.5">
                            Full Name
                        </label>
                        <div className={`relative transition-all duration-300 ${focused === 'name' ? 'scale-[1.01]' : ''}`}>
                            <FiUser className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${
                                focused === 'name' ? 'text-purple-400' : 'text-white/30'
                            }`} />
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                onFocus={() => setFocused('name')}
                                onBlur={() => setFocused(null)}
                                className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-purple-500/50 focus:ring-4 focus:ring-purple-500/10 text-white placeholder-white/30 outline-none transition-all duration-300"
                                placeholder="John Doe"
                                required
                            />
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4, duration: 0.5 }}
                    >
                        <label className="block text-sm font-medium text-white/60 mb-1.5">
                            Email Address
                        </label>
                        <div className={`relative transition-all duration-300 ${focused === 'email' ? 'scale-[1.01]' : ''}`}>
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
                        <div className={`relative transition-all duration-300 ${focused === 'password' ? 'scale-[1.01]' : ''}`}>
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
                                placeholder="Min 6 characters"
                                required
                                minLength={6}
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
                    >
                        <label className="block text-sm font-medium text-white/60 mb-1.5">
                            Confirm Password
                        </label>
                        <div className={`relative transition-all duration-300 ${focused === 'confirm' ? 'scale-[1.01]' : ''}`}>
                            <FiLock className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${
                                focused === 'confirm' ? 'text-purple-400' : 'text-white/30'
                            }`} />
                            <input
                                type={showConfirmPassword ? 'text' : 'password'}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                onFocus={() => setFocused('confirm')}
                                onBlur={() => setFocused(null)}
                                className="w-full pl-12 pr-14 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-purple-500/50 focus:ring-4 focus:ring-purple-500/10 text-white placeholder-white/30 outline-none transition-all duration-300"
                                placeholder="Confirm your password"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                            >
                                {showConfirmPassword ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
                            </button>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7, duration: 0.5 }}
                        className="flex items-start gap-3"
                    >
                        <button
                            type="button"
                            onClick={() => setAgreeTerms(!agreeTerms)}
                            className={`mt-0.5 w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all duration-300 flex-shrink-0 ${
                                agreeTerms
                                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 border-purple-500'
                                    : 'border-white/20 hover:border-white/40'
                            }`}
                        >
                            {agreeTerms && <FiCheck className="w-3.5 h-3.5 text-white" />}
                        </button>
                        <p className="text-xs text-white/40">
                            I agree to the{' '}
                            <a href="#" className="text-purple-400 hover:text-purple-300 transition-colors">
                                Terms of Service
                            </a>{' '}
                            and{' '}
                            <a href="#" className="text-purple-400 hover:text-purple-300 transition-colors">
                                Privacy Policy
                            </a>
                        </p>
                    </motion.div>

                    <motion.button
                        type="submit"
                        disabled={loading}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8, duration: 0.5 }}
                        className="relative w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg hover:shadow-purple-500/30 transition-all duration-300 group overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <span className="relative z-10 flex items-center justify-center gap-2 text-sm">
                            {loading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    Create Account
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
                    transition={{ delay: 0.9, duration: 0.5 }}
                    className="text-center text-sm text-white/30 mt-6"
                >
                    Already have an account?{' '}
                    <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium transition-colors">
                        Sign In
                    </Link>
                </motion.p>
            </motion.div>

            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 text-xs text-white/10">
                © 2024 SmartDevOps. All rights reserved.
            </div>
        </div>
    );
};

export default Register;