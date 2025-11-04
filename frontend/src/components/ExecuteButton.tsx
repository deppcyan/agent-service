import { useState } from 'react';
import type { WorkflowData } from '../services/api';

interface ExecuteButtonProps {
  workflow: WorkflowData;
  workflowName?: string;
  onExecute?: (workflowName: string, workflow: WorkflowData) => void;
}

export default function ExecuteButton({ 
  workflow, 
  workflowName = 'Untitled Workflow',
  onExecute 
}: ExecuteButtonProps) {
  const [isExecuting, setIsExecuting] = useState(false);

  const handleExecute = async () => {
    if (isExecuting) return;
    
    try {
      setIsExecuting(true);
      
      // 直接执行workflow，而不是创建执行tab
      if (onExecute) {
        // 创建执行tab并立即开始执行
        onExecute(workflowName, workflow);
      } else {
        console.error('No execution handler available');
      }
    } catch (e) {
      console.error('Failed to execute workflow:', e);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <button
      onClick={handleExecute}
      disabled={isExecuting}
      className={`px-4 py-2 rounded text-white ${
        isExecuting 
          ? 'bg-gray-600 cursor-not-allowed' 
          : 'bg-indigo-600 hover:bg-indigo-700'
      }`}
    >
      {isExecuting ? 'Starting...' : 'Execute'}
    </button>
  );
}
