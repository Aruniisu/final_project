import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FaUpload, 
  FaGithub, 
  FaGoogleDrive, 
  FaLink, 
  FaTimes,
  FaSpinner,
  FaCheckCircle,
  FaFolder,
  FaFile
} from 'react-icons/fa';
import { uploadAPI } from '../../api/assistant';
import toast from 'react-hot-toast';

const UploadModal = ({ isOpen, onClose, onUpload }) => {
  const [uploadType, setUploadType] = useState('file');
  const [files, setFiles] = useState([]);
  const [githubUrl, setGithubUrl] = useState('');
  const [driveUrl, setDriveUrl] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [analysis, setAnalysis] = useState(null);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleSubmit = async () => {
    setUploading(true);
    setProgress(0);
    setAnalysis(null);

    try {
      let project;
      
      if (uploadType === 'file' && files.length === 0) {
        toast.error('Please select files');
        setUploading(false);
        return;
      }

      if (uploadType === 'github' && !githubUrl) {
        toast.error('Please enter GitHub URL');
        setUploading(false);
        return;
      }

      if (uploadType === 'drive' && !driveUrl) {
        toast.error('Please enter Google Drive URL');
        setUploading(false);
        return;
      }

      if (uploadType === 'link' && !linkUrl) {
        toast.error('Please enter URL');
        setUploading(false);
        return;
      }

      // Upload
      if (uploadType === 'file') {
        const response = await uploadAPI.uploadFiles(files, (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        });
        project = response;
      } else if (uploadType === 'github') {
        project = await uploadAPI.uploadGitHub(githubUrl);
      } else if (uploadType === 'drive') {
        project = await uploadAPI.uploadDrive(driveUrl);
      } else if (uploadType === 'link') {
        project = await uploadAPI.uploadLink(linkUrl);
      }

      // Get analysis
      if (project && project.projectId) {
        const analysisResult = await uploadAPI.getAnalysis(project.projectId);
        project.analysis = analysisResult;
        setAnalysis(analysisResult);
      }

      toast.success('Project uploaded and analyzed!');
      onUpload(project);
      resetForm();

    } catch (error) {
      toast.error('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setFiles([]);
    setGithubUrl('');
    setDriveUrl('');
    setLinkUrl('');
    setProgress(0);
    setAnalysis(null);
  };

  if (!isOpen) return null;

  const uploadOptions = [
    { id: 'file', icon: FaFile, label: 'Files' },
    { id: 'github', icon: FaGithub, label: 'GitHub' },
    { id: 'drive', icon: FaGoogleDrive, label: 'Drive' },
    { id: 'link', icon: FaLink, label: 'Link' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">
            <FaUpload className="inline mr-2 text-primary-500" />
            Upload Project
          </h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            <FaTimes className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Upload Type Selector */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {uploadOptions.map((option) => {
            const Icon = option.icon;
            return (
              <button
                key={option.id}
                onClick={() => setUploadType(option.id)}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl transition-all ${
                  uploadType === option.id
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs font-medium">{option.label}</span>
              </button>
            );
          })}
        </div>

        {/* Upload Content */}
        <div className="mb-4">
          {uploadType === 'file' && (
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl p-6 text-center hover:border-primary-500 transition-colors">
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer block"
              >
                <FaFolder className="w-12 h-12 mx-auto text-slate-400 mb-2" />
                <p className="text-slate-500 dark:text-slate-400">
                  {files.length > 0 ? `${files.length} files selected` : 'Click to select files'}
                </p>
                <p className="text-xs text-slate-400">or drag and drop</p>
              </label>
              {files.length > 0 && (
                <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                  {files.map(f => f.name).join(', ')}
                </div>
              )}
            </div>
          )}

          {uploadType === 'github' && (
            <input
              type="text"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
              className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          )}

          {uploadType === 'drive' && (
            <input
              type="text"
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
              placeholder="https://drive.google.com/file/d/..."
              className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          )}

          {uploadType === 'link' && (
            <input
              type="text"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              placeholder="https://example.com/project.zip"
              className="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          )}
        </div>

        {/* Progress */}
        {uploading && (
          <div className="mb-4">
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
              <span>Uploading...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Analysis Result */}
        {analysis && (
          <div className="mb-4 p-3 rounded-xl bg-success-500/10 border border-success-500/20">
            <div className="flex items-center gap-2 mb-1">
              <FaCheckCircle className="w-4 h-4 text-success-500" />
              <span className="text-sm font-medium text-success-500">Analysis Complete</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300">
              <span>Health: {analysis.healthScore}%</span>
              <span>Issues: {analysis.issues || 0}</span>
              <span>Security: {analysis.securityScore}%</span>
              <span>Recommendations: {analysis.recommendations || 0}</span>
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={uploading}
          className="w-full py-2.5 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <FaSpinner className="w-5 h-5 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <FaUpload className="w-4 h-4" />
              Upload & Analyze
            </>
          )}
        </button>
      </motion.div>
    </motion.div>
  );
};

export default UploadModal;