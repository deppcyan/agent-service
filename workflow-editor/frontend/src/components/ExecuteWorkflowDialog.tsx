import { useState } from 'react';
import { api, type WorkflowData } from '../services/api';

interface ExecuteWorkflowDialogProps {
  isOpen: boolean;
  onClose: () => void;
  workflow: WorkflowData;
}

const ExecuteWorkflowDialog = ({ isOpen, onClose, workflow }: ExecuteWorkflowDialogProps) => {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [inputData, setInputData] = useState('{}');
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleExecute = async () => {
    try {
      setExecuting(true);
      setError(null);

      let parsedInputData;
      try {
        parsedInputData = JSON.parse(inputData);
      } catch (e) {
        setError('Invalid JSON in input data');
        return;
      }

      const response = await api.executeWorkflow({
        workflow,
        input_data: parsedInputData,
        webhook_url: webhookUrl,
      });

      setTaskId(response.task_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to execute workflow');
    } finally {
      setExecuting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-xl font-bold mb-4">Execute Workflow</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Webhook URL
          </label>
          <input
            type="text"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="https://..."
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Input Data (JSON)
          </label>
          <textarea
            value={inputData}
            onChange={(e) => setInputData(e.target.value)}
            className="w-full px-3 py-2 border rounded-md h-32 font-mono text-sm"
            placeholder="{}"
          />
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {taskId && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-md text-sm">
            Workflow started! Task ID: {taskId}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Close
          </button>
          <button
            onClick={handleExecute}
            disabled={executing}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {executing ? 'Executing...' : 'Execute'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExecuteWorkflowDialog;
