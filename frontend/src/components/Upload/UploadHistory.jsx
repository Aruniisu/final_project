import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import {
  FiFile,
  FiFolder,
  FiGithub,
  FiLink,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiTrash2,
  FiDownload,
  FiEye,
  FiSearch,
  FiRefreshCw,
  FiFilter,
} from 'react-icons/fi';
import { FaGoogleDrive } from 'react-icons/fa';
import { uploadAPI } from '../../api/assistant';
import toast from 'react-hot-toast';

const UploadHistory = ({ onSelect, onDelete }) => {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUpload, setSelectedUpload] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await uploadAPI.getHistory();
      setUploads(response || []);
    } catch (error) {
      console.error('Error fetching upload history:', error);
      toast.error('Failed to load upload history');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (uploadId) => {
    if (!window.confirm('Are you sure you want to delete this upload?')) return;
    
    try {
      await uploadAPI.deleteProject(uploadId);
      setUploads(uploads.filter(u => u.projectId !== uploadId));
      toast.success('Upload deleted');
      if (onDelete) onDelete(uploadId);
    } catch (error) {
      toast.error('Failed to delete upload');
    }
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case 'github': return FiGithub;
      case 'drive': return FaGoogleDrive;
      case 'link': return FiLink;
      case 'folder': return FiFolder;
      default: return FiFile;
    }
  };

  const getSourceLabel = (source) => {
    switch (source) {
      case 'github': return 'GitHub';
      case 'drive': return 'Google Drive';
      case 'link': return 'Direct Link';
      case 'folder': return 'Folder';
      default: return 'File';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success bg-success/10';
      case 'processing': return 'text-warning bg-warning/10';
      case 'failed': return 'text-error bg-error/10';
      default: return 'text-slate-500 bg-slate-100 dark:bg-slate-700/50';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <FiCheckCircle className="w-4 h-4" />;
      case 'processing': return <FiClock className="w-4 h-4 animate-spin" />;
      case 'failed': return <FiXCircle className="w-4 h-4" />;
      default: return <FiClock className="w-4 h-4" />;
    }
  };

  const formatDate = (date) => {
    if (!date) return 'Unknown';
    const d = new Date(date);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
  };

  const filteredUploads = uploads.filter(upload => {
    const matchesFilter = filter === 'all' || upload.source === filter || upload.status === filter;
    const matchesSearch = searchTerm === '' || 
      upload.projectName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      upload.source?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-card p-4">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
              <div className="flex-1">
                <div className="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div className="h-3 w-24 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
              </div>
              <div className="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === 'all'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('file')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === 'file'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <FiFile className="inline w-3 h-3 mr-1" />
            Files
          </button>
          <button
            onClick={() => setFilter('github')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === 'github'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <FiGithub className="inline w-3 h-3 mr-1" />
            GitHub
          </button>
          <button
            onClick={() => setFilter('drive')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === 'drive'
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <FaGoogleDrive className="inline w-3 h-3 mr-1" />
            Drive
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === 'completed'
                ? 'bg-success-500 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <FiCheckCircle className="inline w-3 h-3 mr-1" />
            Completed
          </button>
        </div>

        <div className="flex items-center gap-2 ml-auto w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-none">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search uploads..."
              className="w-full sm:w-48 pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            />
          </div>
          <button
            onClick={fetchHistory}
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            title="Refresh"
          >
            <FiRefreshCw className="w-4 h-4 text-slate-600 dark:text-slate-400" />
          </button>
        </div>
      </div>

      {/* Upload List */}
      <div className="space-y-2">
        <AnimatePresence>
          {filteredUploads.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto">
                <FiFile className="w-8 h-8 text-slate-400" />
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                No uploads found
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500">
                Try changing your filters or upload a new project
              </p>
            </div>
          ) : (
            filteredUploads.map((upload, index) => {
              const SourceIcon = getSourceIcon(upload.source);
              return (
                <motion.div
                  key={upload.projectId || index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className={`glass-card p-4 hover:shadow-lg transition-all cursor-pointer ${
                    selectedUpload === upload.projectId ? 'border-primary-500' : ''
                  }`}
                  onClick={() => {
                    setSelectedUpload(upload.projectId);
                    if (onSelect) onSelect(upload);
                  }}
                >
                  <div className="flex items-center gap-4">
                    {/* Icon */}
                    <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800">
                      <SourceIcon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {upload.projectName || 'Untitled Project'}
                        </h4>
                        <span className="text-xs text-slate-400">
                          {getSourceLabel(upload.source)}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        <span>{formatDate(upload.createdAt)}</span>
                        {upload.metadata?.analysis?.healthScore && (
                          <>
                            <span className="w-px h-3 bg-slate-300 dark:bg-slate-600"></span>
                            <span>Health: {upload.metadata.analysis.healthScore}%</span>
                          </>
                        )}
                        {upload.metadata?.analysis?.issues !== undefined && (
                          <>
                            <span className="w-px h-3 bg-slate-300 dark:bg-slate-600"></span>
                            <span>Issues: {upload.metadata.analysis.issues}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Status */}
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(upload.status)}`}>
                      {getStatusIcon(upload.status)}
                      <span className="capitalize">{upload.status || 'pending'}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(upload.projectId);
                        }}
                        className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-error transition-colors"
                        title="Delete"
                      >
                        <FiTrash2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onSelect) onSelect(upload);
                        }}
                        className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 transition-colors"
                        title="View Details"
                      >
                        <FiEye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>

      {/* Stats */}
      {uploads.length > 0 && (
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-200 dark:border-slate-700">
          <span>{filteredUploads.length} of {uploads.length} uploads</span>
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  );
};

export default UploadHistory;