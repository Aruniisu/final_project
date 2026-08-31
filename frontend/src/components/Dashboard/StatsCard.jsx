import React from 'react';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';

const StatsCard = ({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  color = 'bg-primary-500/10',
  subtitle = null,
  loading = false,
  onClick = null,
}) => {
  if (loading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-3 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
          <div className="h-12 w-12 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const isPositive = change > 0;
  const isNeutral = change === 0;
  const isNegative = change < 0;

  const getChangeColor = () => {
    if (isPositive) return 'text-success';
    if (isNegative) return 'text-error';
    return 'text-slate-400';
  };

  const getChangeIcon = () => {
    if (isPositive) return <FiTrendingUp className="w-3 h-3" />;
    if (isNegative) return <FiTrendingDown className="w-3 h-3" />;
    return null;
  };

  const formattedChange = change !== null && change !== undefined ? `${isPositive ? '+' : ''}${change}%` : null;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      onClick={onClick}
      className={`glass-card glass-card-hover p-6 ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400 truncate">
            {title}
          </p>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1 truncate">
            {value}
          </h3>
          
          {change !== null && change !== undefined && (
            <div className="flex items-center gap-1 mt-1">
              {getChangeIcon()}
              <span className={`text-xs font-medium ${getChangeColor()}`}>
                {formattedChange}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                vs last week
              </span>
            </div>
          )}
          
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
              {subtitle}
            </p>
          )}
        </div>
        
        <div className={`p-3 rounded-xl flex-shrink-0 ${color}`}>
          <Icon className={`w-6 h-6 text-${color.replace('bg-', '').replace('/10', '') || 'primary-500'}`} />
        </div>
      </div>
    </motion.div>
  );
};

export default StatsCard;