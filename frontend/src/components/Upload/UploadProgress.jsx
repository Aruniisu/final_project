import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiX, FiCheckCircle, FiAlertCircle, FiClock, FiFile } from 'react-icons/fi';

const UploadProgress = ({ 
  isOpen, 
  onClose, 
  progress, 
  status = 'uploading',
  fileName = '',
  fileSize = '',
  error = null,
  onRetry = null,
}) => {
  if (!isOpen) return null;

  const getStatusConfig = () => {
    switch (status) {
      case 'uploading':
        return {
          icon: FiClock,
          color: 'text-primary-500',
          bgColor: 'bg-primary-500/10',
          title: 'Uploading...',
          description: 'Your project is being uploaded',
        };
      case 'processing':
        return {
          icon: FiClock,
          color: 'text-warning-500',
          bgColor: 'bg-warning-500/10',
          title: 'Processing...',
          description: 'Analyzing your project',
        };
      case 'complete':
        return {
          icon: FiCheckCircle,
          color: 'text-success-500',
          bgColor: 'bg-success-500/10',
          title: 'Upload Complete!',
          description: 'Project uploaded successfully',
        };
      case 'error':
        return {
          icon: FiAlertCircle,
          color: 'text-error-500',
          bgColor: 'bg-error-500/10',
          title: 'Upload Failed',
          description: error || 'An error occurred',
        };
      default:
        return {
          icon: FiClock,
          color: 'text-slate-500',
          bgColor: 'bg-slate-500/10',
          title: 'Uploading...',
          description: 'Please wait',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;
  const isComplete = status === 'complete';
  const isError = status === 'error';
  const isActive = status === 'uploading' || status === 'processing';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="fixed bottom-6 right-6 z-50 w-80"
      >
        <div className="glass-card p-4 shadow-2xl">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${config.bgColor} ${config.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                  {config.title}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {fileName || 'Uploading project...'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-600"
            >
              <FiX className="w-4 h-4" />
            </button>
          </div>

          {/* Progress Bar */}
          {isActive && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                <span>{progress}%</span>
                <span>{fileSize}</span>
              </div>
              <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                  className={`h-full rounded-full ${
                    status === 'uploading'
                      ? 'bg-gradient-to-r from-primary-500 to-accent-500'
                      : status === 'processing'
                      ? 'bg-warning-500'
                      : 'bg-success-500'
                  }`}
                />
              </div>
            </div>
          )}

          {/* File Details */}
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <FiFile className="w-3 h-3" />
            <span className="truncate">{fileName || 'No file selected'}</span>
            {fileSize && (
              <>
                <span className="w-px h-3 bg-slate-300 dark:bg-slate-600"></span>
                <span>{fileSize}</span>
              </>
            )}
          </div>

          {/* Error Message */}
          {isError && error && (
            <div className="mt-2 p-2 rounded-lg bg-error/10 text-error text-xs">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-3 flex items-center gap-2">
            {isError && onRetry && (
              <button
                onClick={onRetry}
                className="px-3 py-1 text-xs bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Retry
              </button>
            )}
            {isComplete && (
              <button
                onClick={onClose}
                className="px-3 py-1 text-xs bg-success-500 text-white rounded-lg hover:bg-success-600 transition-colors"
              >
                Done
              </button>
            )}
            {!isComplete && !isError && (
              <button
                onClick={onClose}
                className="px-3 py-1 text-xs bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
              >
                Hide
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default UploadProgress;