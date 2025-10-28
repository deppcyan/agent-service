import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SavedWorkflow } from '../services/api';

interface WorkflowListProps {
  onWorkflowLoad: (workflowName: string) => void;
}

export default function WorkflowList({ onWorkflowLoad }: WorkflowListProps) {
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.listWorkflows();
      setWorkflows(response.workflows);
    } catch (err) {
      setError('Failed to load workflows');
      console.error('Error loading workflows:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center text-gray-400">
        Loading workflows...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        {error}
        <button
          onClick={loadWorkflows}
          className="block mx-auto mt-2 text-blue-500 hover:text-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        No saved workflows found
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-700">
      {workflows.map((workflow) => (
        <button
          key={workflow.name}
          onClick={() => onWorkflowLoad(workflow.name)}
          className="w-full p-4 text-left text-gray-300 hover:bg-gray-700 hover:text-white focus:outline-none focus:bg-gray-700"
        >
          <div className="font-medium">{workflow.name}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {new Date(workflow.last_modified * 1000).toLocaleString()}
          </div>
        </button>
      ))}
    </div>
  );
}