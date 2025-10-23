import { useState } from 'react';
import { api, type WorkflowData } from '../services/api';

interface ExecuteWorkflowButtonProps {
  workflow: WorkflowData;
}

const ExecuteWorkflowButton = ({ workflow }: ExecuteWorkflowButtonProps) => {
  const [executing, setExecuting] = useState(false);

  const handleExecute = async () => {
    try {
      setExecuting(true);
      await api.executeWorkflow({
        workflow,
        webhook_url: '',
      });
    } catch (e) {
      console.error('Failed to execute workflow:', e);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <button
      onClick={handleExecute}
      disabled={executing}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
    >
      {executing ? 'Executing...' : 'Execute'}
    </button>
  );
};

export default ExecuteWorkflowButton;
