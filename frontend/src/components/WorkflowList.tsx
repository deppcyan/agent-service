import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SavedWorkflow } from '../services/api';

interface WorkflowListProps {
  onWorkflowLoad: (workflowName: string) => void;
}

interface ContextMenu {
  x: number;
  y: number;
  workflowName: string;
}

export default function WorkflowList({ onWorkflowLoad }: WorkflowListProps) {
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

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

  const handleDeleteWorkflow = async (workflowName: string) => {
    if (!confirm(`Are you sure you want to delete workflow "${workflowName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setIsDeleting(workflowName);
      await api.deleteWorkflow(workflowName);
      
      // Remove the workflow from the list
      setWorkflows(prev => prev.filter(w => w.name !== workflowName));
      setContextMenu(null);
    } catch (err) {
      console.error('Error deleting workflow:', err);
      alert('Failed to delete workflow. Please try again.');
    } finally {
      setIsDeleting(null);
    }
  };

  const handleContextMenu = (e: React.MouseEvent, workflowName: string) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      workflowName
    });
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu(null);
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenu]);

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
    <div className="divide-y divide-gray-700 relative">
      {workflows.map((workflow) => (
        <button
          key={workflow.name}
          onClick={() => onWorkflowLoad(workflow.name)}
          onContextMenu={(e) => handleContextMenu(e, workflow.name)}
          className={`w-full p-4 text-left text-gray-300 hover:bg-gray-700 hover:text-white focus:outline-none focus:bg-gray-700 relative ${
            isDeleting === workflow.name ? 'opacity-50 pointer-events-none' : ''
          }`}
          disabled={isDeleting === workflow.name}
        >
          <div className="font-medium">{workflow.name}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {new Date(workflow.last_modified * 1000).toLocaleString()}
          </div>
          {isDeleting === workflow.name && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-sm text-gray-400">Deleting...</div>
            </div>
          )}
        </button>
      ))}

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-gray-800 rounded-lg shadow-lg py-2 z-50 border border-gray-700 min-w-[120px]"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white"
            onClick={() => {
              onWorkflowLoad(contextMenu.workflowName);
              handleCloseContextMenu();
            }}
          >
            Load Workflow
          </button>
          <button
            className="w-full px-4 py-2 text-left text-red-400 hover:bg-gray-700 hover:text-red-300"
            onClick={() => handleDeleteWorkflow(contextMenu.workflowName)}
          >
            Delete Workflow
          </button>
        </div>
      )}
    </div>
  );
}