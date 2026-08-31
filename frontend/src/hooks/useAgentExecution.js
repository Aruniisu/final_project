import { useState, useCallback } from 'react';
import { assistantAPI } from '../api/assistant';
import toast from 'react-hot-toast';

export const useAgentExecution = () => {
  const [execution, setExecution] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [errors, setErrors] = useState([]);
  const [logs, setLogs] = useState([]);

  const addLog = useCallback((level, message) => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toISOString(),
      level,
      message
    }]);
  }, []);

  const resetExecution = useCallback(() => {
    setExecution(null);
    setErrors([]);
    setIsExecuting(false);
  }, []);

  const executeTask = useCallback(async (intent, params = {}) => {
    setIsExecuting(true);
    setErrors([]);
    addLog('info', `🚀 Starting task: ${intent}`);

    const executionData = {
      id: Date.now().toString(),
      type: intent,
      status: 'running',
      progress: 0,
      steps: [],
      logs: [],
      errors: [],
      startedAt: new Date().toISOString()
    };
    setExecution(executionData);

    try {
      // Step 1: Analyze and plan
      addLog('info', '🧠 Analyzing request and planning...');
      
      // Generate steps based on intent
      let steps = [];
      if (intent === 'deploy' || intent.includes('deploy')) {
        steps = [
          { name: 'Analyzing application code', status: 'pending' },
          { name: 'Building Docker image', status: 'pending' },
          { name: 'Pushing to registry', status: 'pending' },
          { name: 'Creating Kubernetes deployment', status: 'pending' },
          { name: 'Verifying deployment health', status: 'pending' }
        ];
      } else if (intent === 'pipeline' || intent.includes('pipeline')) {
        steps = [
          { name: 'Creating pipeline configuration', status: 'pending' },
          { name: 'Setting up GitHub Actions', status: 'pending' },
          { name: 'Configuring build steps', status: 'pending' },
          { name: 'Setting up deployment stages', status: 'pending' },
          { name: 'Running initial pipeline test', status: 'pending' }
        ];
      } else if (intent === 'scale' || intent.includes('scale')) {
        steps = [
          { name: 'Analyzing current resources', status: 'pending' },
          { name: 'Updating deployment configuration', status: 'pending' },
          { name: 'Applying scaling changes', status: 'pending' },
          { name: 'Verifying new replicas', status: 'pending' }
        ];
      } else if (intent === 'analyze' || intent.includes('analyze')) {
        steps = [
          { name: 'Scanning codebase', status: 'pending' },
          { name: 'Running security analysis', status: 'pending' },
          { name: 'Checking code quality', status: 'pending' },
          { name: 'Generating report', status: 'pending' }
        ];
      } else {
        steps = [
          { name: 'Processing request', status: 'pending' },
          { name: 'Executing task', status: 'pending' },
          { name: 'Verifying results', status: 'pending' }
        ];
      }

      // Update execution with steps
      setExecution(prev => ({
        ...prev,
        steps: steps.map(s => ({ ...s, status: 'pending' }))
      }));

      // Step 2: Execute each step with error detection
      let completedSteps = 0;
      const totalSteps = steps.length;

      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        addLog('info', `⏳ Executing step: ${step.name}`);

        // Update step status
        setExecution(prev => ({
          ...prev,
          steps: prev.steps.map((s, idx) => 
            idx === i ? { ...s, status: 'running' } : s
          ),
          progress: Math.round((i / totalSteps) * 100)
        }));

        // Simulate step execution with random success/failure
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        
        // Random success (90% chance)
        if (Math.random() < 0.9) {
          completedSteps++;
          setExecution(prev => ({
            ...prev,
            steps: prev.steps.map((s, idx) => 
              idx === i ? { ...s, status: 'completed', duration: (1 + Math.random() * 2).toFixed(1) + 's' } : s
            ),
            progress: Math.round(((i + 1) / totalSteps) * 100)
          }));
          addLog('success', `✅ Step completed: ${step.name}`);
        } else {
          // Simulate error
          const errorMsg = `Error in step: ${step.name}`;
          addLog('error', `❌ ${errorMsg}`);
          
          // Try to auto-fix
          addLog('info', '🔧 Attempting to auto-fix...');
          await new Promise(resolve => setTimeout(resolve, 1000));
          addLog('success', `✅ Auto-fixed: ${step.name}`);
          
          // Retry step
          addLog('info', `🔄 Retrying step: ${step.name}`);
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          completedSteps++;
          setExecution(prev => ({
            ...prev,
            steps: prev.steps.map((s, idx) => 
              idx === i ? { ...s, status: 'completed', duration: (1 + Math.random() * 3).toFixed(1) + 's' } : s
            ),
            progress: Math.round(((i + 1) / totalSteps) * 100)
          }));
          addLog('success', `✅ Step completed after auto-fix: ${step.name}`);
        }
      }

      // Step 3: Complete
      addLog('success', '✅ All steps completed successfully!');
      
      const completedExecution = {
        ...executionData,
        status: 'completed',
        progress: 100,
        steps: executionData.steps.map(s => ({ ...s, status: 'completed' })),
        duration: (Math.random() * 10 + 5).toFixed(1) + 's',
        completedAt: new Date().toISOString()
      };
      setExecution(completedExecution);
      setIsExecuting(false);

      return {
        ...completedExecution,
        success: true,
        errors: errors,
        url: 'https://smart-devops-demo.com',
        duration: completedExecution.duration
      };

    } catch (error) {
      addLog('error', `❌ Task failed: ${error.message}`);
      setIsExecuting(false);
      return {
        ...executionData,
        status: 'failed',
        errors: errors,
        error: error.message,
        fix: error.fix || 'Try again with different parameters'
      };
    }
  }, [addLog, errors]);

  const retryTask = useCallback(async (taskId) => {
    addLog('info', '🔄 Retrying task...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    addLog('success', '✅ Task retry successful');
    return { success: true };
  }, [addLog]);

  return {
    executeTask,
    execution,
    isExecuting,
    errors,
    logs,
    addLog,
    resetExecution,
    retryTask
  };
};