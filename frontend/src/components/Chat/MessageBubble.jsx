import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiCopy, FiCheck, FiRefreshCw, FiDownload, FiThumbsUp, FiThumbsDown, FiShare2 } from 'react-icons/fi';
import { FaRobot, FaUser, FaSpinner } from 'react-icons/fa';
import toast from 'react-hot-toast';

const MessageBubble = ({ 
  message, 
  isUser, 
  timestamp, 
  tools = [], 
  isWelcome = false,
  isStreaming = false,
  metadata = {},
}) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const contentRef = useRef(null);
  const [isOverflowing, setIsOverflowing] = useState(false);

  useEffect(() => {
    if (contentRef.current) {
      setIsOverflowing(contentRef.current.scrollHeight > 300);
    }
  }, [message]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([message], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `message-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Downloaded');
  };

  const handleFeedback = (type) => {
    setFeedback(type);
    toast.success(`Feedback: ${type === 'positive' ? '👍 Helpful' : '👎 Not helpful'}`);
  };

  const handleShare = async () => {
    try {
      await navigator.share({
        title: 'AI Assistant Message',
        text: message,
      });
    } catch (error) {
      // Fallback to clipboard
      await navigator.clipboard.writeText(message);
      toast.success('Copied to clipboard for sharing');
    }
  };

  const renderContent = () => {
    if (isStreaming) {
      return (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <div className="relative">
                    <div className="absolute top-2 right-2 flex gap-1 z-10">
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                          toast.success('Code copied');
                        }}
                        className="p-1 rounded bg-slate-700/50 hover:bg-slate-600/50 transition-colors text-white/70 hover:text-white"
                      >
                        <FiCopy className="w-3 h-3" />
                      </button>
                    </div>
                    <SyntaxHighlighter
                      style={atomDark}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-xl !mt-0"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className="bg-slate-100 dark:bg-slate-700 rounded px-1.5 py-0.5 text-sm" {...props}>
                    {children}
                  </code>
                );
              },
              table({ children }) {
                return (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                      {children}
                    </table>
                  </div>
                );
              },
              th({ children }) {
                return (
                  <th className="px-3 py-2 bg-slate-50 dark:bg-slate-800 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    {children}
                  </th>
                );
              },
              td({ children }) {
                return (
                  <td className="px-3 py-2 text-sm text-slate-700 dark:text-slate-300 border-t border-slate-200 dark:border-slate-700">
                    {children}
                  </td>
                );
              },
            }}
          >
            {message + ' ▊'}
          </ReactMarkdown>
        </div>
      );
    }

    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <div className="relative group">
                  <div className="absolute top-2 right-2 flex gap-1 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                        toast.success('Code copied');
                      }}
                      className="p-1 rounded bg-slate-700/50 hover:bg-slate-600/50 transition-colors text-white/70 hover:text-white"
                    >
                      <FiCopy className="w-3 h-3" />
                    </button>
                  </div>
                  <SyntaxHighlighter
                    style={atomDark}
                    language={match[1]}
                    PreTag="div"
                    className="rounded-xl !mt-0"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <code className="bg-slate-100 dark:bg-slate-700 rounded px-1.5 py-0.5 text-sm" {...props}>
                  {children}
                </code>
              );
            },
            blockquote({ children }) {
              return (
                <blockquote className="border-l-4 border-primary-500 pl-4 py-1 my-2 text-slate-600 dark:text-slate-400 italic">
                  {children}
                </blockquote>
              );
            },
            ul({ children }) {
              return <ul className="list-disc pl-4 space-y-1">{children}</ul>;
            },
            ol({ children }) {
              return <ol className="list-decimal pl-4 space-y-1">{children}</ol>;
            },
            h1({ children }) {
              return <h1 className="text-xl font-bold mt-3 mb-2">{children}</h1>;
            },
            h2({ children }) {
              return <h2 className="text-lg font-bold mt-2 mb-1.5">{children}</h2>;
            },
            h3({ children }) {
              return <h3 className="text-base font-semibold mt-2 mb-1">{children}</h3>;
            },
            table({ children }) {
              return (
                <div className="overflow-x-auto my-2">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    {children}
                  </table>
                </div>
              );
            },
            th({ children }) {
              return (
                <th className="px-3 py-2 bg-slate-50 dark:bg-slate-800 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {children}
                </th>
              );
            },
            td({ children }) {
              return (
                <td className="px-3 py-2 text-sm text-slate-700 dark:text-slate-300 border-t border-slate-200 dark:border-slate-700">
                  {children}
                </td>
              );
            },
          }}
        >
          {message}
        </ReactMarkdown>
      </div>
    );
  };

  // If streaming, show different layout
  if (isStreaming) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[85%]">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-500 to-secondary-500 flex items-center justify-center flex-shrink-0">
              <FaRobot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-bl-none px-4 py-3 shadow-lg shadow-slate-200/50 dark:shadow-slate-900/50 min-w-[100px]">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <div className="relative">
                          <SyntaxHighlighter
                            style={atomDark}
                            language={match[1]}
                            PreTag="div"
                            className="rounded-xl !mt-0"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code className="bg-slate-100 dark:bg-slate-700 rounded px-1.5 py-0.5 text-sm" {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message}
                </ReactMarkdown>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <FaSpinner className="w-3 h-3 text-primary-500 animate-spin" />
                <span className="text-xs text-slate-400">Generating...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`max-w-[85%] ${isUser ? 'order-1' : ''}`}>
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
          {/* Avatar */}
          <div
            className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
              isUser
                ? 'bg-gradient-to-br from-primary-500 to-primary-600'
                : 'bg-gradient-to-br from-accent-500 to-secondary-500'
            }`}
          >
            {isUser ? (
              <FaUser className="w-4 h-4 text-white" />
            ) : (
              <FaRobot className="w-4 h-4 text-white" />
            )}
          </div>

          {/* Content */}
          <div
            className={`relative rounded-2xl px-4 py-3 ${
              isUser
                ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-none'
                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-none shadow-lg shadow-slate-200/50 dark:shadow-slate-900/50'
            }`}
          >
            {/* Main Content */}
            <div ref={contentRef}>
              {isUser ? (
                <p className="text-sm whitespace-pre-wrap break-words">{message}</p>
              ) : (
                renderContent()
              )}
            </div>

            {/* Expand/Collapse for long messages */}
            {!isUser && isOverflowing && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-primary-500 hover:text-primary-600 mt-1"
              >
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}

            {/* Actions */}
            <div className={`flex flex-wrap items-center gap-2 mt-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && !isWelcome && (
                <>
                  <button
                    onClick={handleCopy}
                    className={`text-xs flex items-center gap-1 transition-colors ${
                      isUser
                        ? 'text-primary-100 hover:text-white'
                        : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                    }`}
                  >
                    {copied ? <FiCheck className="w-3 h-3" /> : <FiCopy className="w-3 h-3" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                  <button
                    onClick={handleDownload}
                    className={`text-xs flex items-center gap-1 transition-colors ${
                      isUser
                        ? 'text-primary-100 hover:text-white'
                        : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                    }`}
                  >
                    <FiDownload className="w-3 h-3" />
                    Save
                  </button>
                  <button
                    onClick={handleShare}
                    className={`text-xs flex items-center gap-1 transition-colors ${
                      isUser
                        ? 'text-primary-100 hover:text-white'
                        : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                    }`}
                  >
                    <FiShare2 className="w-3 h-3" />
                    Share
                  </button>
                  <div className="flex items-center gap-0.5">
                    <button
                      onClick={() => handleFeedback('positive')}
                      className={`p-0.5 rounded transition-colors ${
                        feedback === 'positive'
                          ? 'text-success'
                          : 'text-slate-400 hover:text-success'
                      }`}
                      title="Helpful"
                    >
                      <FiThumbsUp className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => handleFeedback('negative')}
                      className={`p-0.5 rounded transition-colors ${
                        feedback === 'negative'
                          ? 'text-error'
                          : 'text-slate-400 hover:text-error'
                      }`}
                      title="Not helpful"
                    >
                      <FiThumbsDown className="w-3 h-3" />
                    </button>
                  </div>
                </>
              )}
              {tools && tools.length > 0 && (
                <span className={`text-xs flex items-center gap-1 ${
                  isUser ? 'text-primary-100' : 'text-slate-400'
                }`}>
                  <FiRefreshCw className="w-3 h-3" />
                  Tools: {tools.join(', ')}
                </span>
              )}
            </div>

            {/* Timestamp */}
            <div className={`text-xs mt-1 ${isUser ? 'text-primary-100' : 'text-slate-400'}`}>
              {timestamp || new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;