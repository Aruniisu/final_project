import React, { createContext, useState, useContext, useEffect } from 'react';

// Create Theme Context
const ThemeContext = createContext();

// Custom hook to use theme context
export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

// Theme Provider Component
export const ThemeProvider = ({ children }) => {
    // Get initial theme from localStorage or system preference
    const getInitialTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    };

    const [theme, setTheme] = useState(getInitialTheme);
    const [mounted, setMounted] = useState(false);

    // Available themes
    const themes = {
        light: {
            name: 'Light',
            icon: '☀️',
            colors: {
                background: 'bg-white',
                text: 'text-slate-900',
                card: 'bg-white/80',
                border: 'border-slate-200',
                hover: 'hover:bg-slate-50',
            },
        },
        dark: {
            name: 'Dark',
            icon: '🌙',
            colors: {
                background: 'bg-slate-900',
                text: 'text-white',
                card: 'bg-slate-800/80',
                border: 'border-slate-700',
                hover: 'hover:bg-slate-800',
            },
        },
        cupcake: {
            name: 'Cupcake',
            icon: '🧁',
            colors: {
                background: 'bg-pink-50',
                text: 'text-pink-900',
                card: 'bg-pink-100/80',
                border: 'border-pink-200',
                hover: 'hover:bg-pink-100',
            },
        },
        dracula: {
            name: 'Dracula',
            icon: '🧛',
            colors: {
                background: 'bg-[#282a36]',
                text: 'text-[#f8f8f2]',
                card: 'bg-[#44475a]/80',
                border: 'border-[#6272a4]',
                hover: 'hover:bg-[#44475a]',
            },
        },
        night: {
            name: 'Night',
            icon: '🌃',
            colors: {
                background: 'bg-[#0f172a]',
                text: 'text-[#e2e8f0]',
                card: 'bg-[#1e293b]/80',
                border: 'border-[#334155]',
                hover: 'hover:bg-[#1e293b]',
            },
        },
        forest: {
            name: 'Forest',
            icon: '🌲',
            colors: {
                background: 'bg-[#1a2e1a]',
                text: 'text-[#c8e6c9]',
                card: 'bg-[#2e4a2e]/80',
                border: 'border-[#4a6a4a]',
                hover: 'hover:bg-[#2e4a2e]',
            },
        },
        ocean: {
            name: 'Ocean',
            icon: '🌊',
            colors: {
                background: 'bg-[#0c1929]',
                text: 'text-[#b3d4fc]',
                card: 'bg-[#1a2e4a]/80',
                border: 'border-[#2a4a6a]',
                hover: 'hover:bg-[#1a2e4a]',
            },
        },
        sunset: {
            name: 'Sunset',
            icon: '🌅',
            colors: {
                background: 'bg-[#1a0a0a]',
                text: 'text-[#ffd4b3]',
                card: 'bg-[#2a1a1a]/80',
                border: 'border-[#4a2a2a]',
                hover: 'hover:bg-[#2a1a1a]',
            },
        },
    };

    // Apply theme to document
    useEffect(() => {
        setMounted(true);
        // Set data-theme attribute on html element
        document.documentElement.setAttribute('data-theme', theme);
        // Store in localStorage
        localStorage.setItem('theme', theme);

        // Update meta theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const colors = {
                light: '#ffffff',
                dark: '#0f172a',
                cupcake: '#fce7f3',
                dracula: '#282a36',
                night: '#0f172a',
                forest: '#1a2e1a',
                ocean: '#0c1929',
                sunset: '#1a0a0a',
            };
            metaThemeColor.content = colors[theme] || '#ffffff';
        }

        // Toggle dark class for Tailwind dark mode
        if (theme === 'dark' || theme === 'night' || theme === 'forest' || 
            theme === 'ocean' || theme === 'sunset') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [theme]);

    // Listen for system theme changes
    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = (e) => {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        };
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, []);

    // Toggle between light and dark
    const toggleTheme = () => {
        setTheme(prev => prev === 'light' ? 'dark' : 'light');
    };

    // Set specific theme
    const setThemeByName = (themeName) => {
        if (themes[themeName]) {
            setTheme(themeName);
        }
    };

    // Get current theme object
    const currentTheme = themes[theme] || themes.light;

    const value = {
        theme,
        setTheme: setThemeByName,
        toggleTheme,
        themes,
        currentTheme,
        isDark: theme === 'dark' || theme === 'night' || theme === 'forest' || 
                theme === 'ocean' || theme === 'sunset',
        isLight: theme === 'light' || theme === 'cupcake',
        mounted,
    };

    // Prevent flash of wrong theme
    if (!mounted) {
        return <div style={{ visibility: 'hidden' }}>{children}</div>;
    }

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
};

export default ThemeContext;