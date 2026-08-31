import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [token, setToken] = useState(localStorage.getItem('token'));

    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            setUser({ name: 'Demo User', email: 'demo@example.com', role: 'engineer' });
        }
        setLoading(false);
    }, [token]);

    const login = async (email, password) => {
        // Demo login - always succeeds
        setUser({ name: 'Demo User', email, role: 'engineer' });
        localStorage.setItem('token', 'demo-token');
        toast.success('Welcome back! 🎉');
        return { success: true };
    };

    const register = async (name, email, password) => {
        toast.success('Account created! Please login.');
        return { success: true };
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        toast.success('Logged out');
    };

    const value = {
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;