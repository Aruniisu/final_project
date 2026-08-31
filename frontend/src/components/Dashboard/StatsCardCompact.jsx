import React from 'react';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';

const StatsCardCompact = ({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  color = 'primary',
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="bg-white/50 dark:bg-slate-800/50 rounded-xl p-4 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-200 dark:bg-slate-700"></div>
          <div className="flex-1">
            <div className="h-3 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-5 w-12 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
          </div>
        </div>
      </div>
    );
  }

  const isPositive = change > 0;
  const isNegative = change < 0;

  const colorMap = {
    primary: 'bg-primary-500/10 text-primary-500',
    accent: 'bg-accent-500/10 text-accent-500',
    success: 'bg-success/10 text-success',
    warning: 'bg-warning/10 text-warning',
    error: 'bg-error/10 text-error',
    info: 'bg-info/10 text-info',
  };

  const iconColor = colorMap[color] || colorMap.primary;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white/50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200/50 dark:border-slate-700/50 hover:border-primary-500/30 transition-all duration-300"
    >
      <div className="flex items-center gap-3">
        <div className={`p-2.5 rounded-lg ${iconColor}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 truncate">
            {title}
          </p>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              {value}
            </span>
            {change !== null && change !== undefined && (
              <span className={`text-xs font-medium flex items-center gap-0.5 ${
                isPositive ? 'text-success' : isNegative ? 'text-error' : 'text-slate-400'
              }`}>
                {isPositive ? <FiTrendingUp className="w-3 h-3" /> : <FiTrendingDown className="w-3 h-3" />}
                {isPositive ? '+' : ''}{change}%
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default StatsCardCompact;