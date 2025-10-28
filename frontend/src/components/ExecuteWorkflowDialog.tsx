import { useState, useEffect } from 'react';
import { api, type WorkflowData } from '../services/api';

interface ExecuteWorkflowButtonProps {
  workflow: WorkflowData;
}

interface ExecuteWorkflowDialogProps {
  workflow: WorkflowData;
  onClose: () => void;
}

interface WorkflowResult {
  status: 'running' | 'completed' | 'error' | 'cancelled' | 'not_found';
  result: Record<string, any>;
  error?: string;
}

const POLL_INTERVAL = 2000; // 2 seconds

const ExecuteWorkflowDialog = ({ workflow, onClose }: ExecuteWorkflowDialogProps) => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);

  // Start workflow execution when dialog opens
  useEffect(() => {
    const startExecution = async () => {
      try {
        const response = await api.executeWorkflow({
          workflow
        });
        setTaskId(response.task_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to start workflow');
      }
    };
    startExecution();
  }, [workflow]);

  // Poll for results when we have a task ID
  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getWorkflowStatus(taskId);
        setResult(status);
        
        // Stop polling if workflow is complete or failed
        if (status.status !== 'running') {
          clearInterval(pollInterval);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to get workflow status');
        clearInterval(pollInterval);
      }
    }, POLL_INTERVAL);

    return () => clearInterval(pollInterval);
  }, [taskId]);

  // Handle workflow cancellation
  const handleCancel = async () => {
    if (!taskId || isCancelling) return;
    
    try {
      setIsCancelling(true);
      await api.cancelWorkflow(taskId);
      // Status will be updated in the next poll
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to cancel workflow');
    } finally {
      setIsCancelling(false);
    }
  };

  // Extract media URLs from results
  // Extract media URLs from results, including URLs in arrays
  const extractUrls = (obj: any): string[] => {
    if (!obj) return [];
    if (typeof obj === 'string' && (obj.startsWith('http') || obj.startsWith('/files/'))) {
      return [obj];
    }
    if (Array.isArray(obj)) {
      return obj.flatMap(item => extractUrls(item));
    }
    if (typeof obj === 'object') {
      return Object.values(obj).flatMap(value => extractUrls(value));
    }
    return [];
  };

  const mediaUrls = result?.result ? extractUrls(result.result) : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-[95vw] w-full max-h-[95vh] flex flex-col">
        <div className="flex justify-between items-center mb-4 flex-shrink-0">
          <h2 className="text-2xl font-bold">Workflow Execution</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 flex-shrink-0">
            {error}
          </div>
        )}

        {result && (
          <div className="flex-1 flex gap-6 min-h-0">
            {/* Left Panel - Results */}
            <div className="w-1/2 overflow-y-auto pr-3 border-r">
              <div className="flex items-center gap-2 mb-4 sticky top-0 bg-white py-2 z-10 border-b">
                <span className="font-semibold">Status:</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  result.status === 'completed' ? 'bg-green-100 text-green-800' :
                  result.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {result.status}
                </span>
              </div>

              {result.error && (
                <div className="text-red-600 mb-4">
                  Error: {result.error}
                </div>
              )}

              {/* Display all result data in a structured way */}
              {Object.entries(result.result || {}).map(([key, value]) => (
                <div key={key} className="mb-6 border rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <h3 className="font-semibold text-lg mb-3 text-gray-800">{key}</h3>
                  {typeof value === 'object' ? (
                    <div className="space-y-3">
                      {Object.entries(value).map(([subKey, subValue]) => {
                        const isUrl = typeof subValue === 'string' && (subValue.startsWith('http') || subValue.startsWith('/files/'));
                        return (
                          <div key={subKey} className="ml-4">
                            <span className="font-medium text-gray-700">{subKey}: </span>
                            {Array.isArray(subValue) && subValue.every(item => typeof item === 'string' && (item.startsWith('http') || item.startsWith('/files/'))) ? (
                              <div className="space-y-2">
                                {subValue.map((url, idx) => (
                                  <a
                                    key={idx}
                                    href="#"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      const element = document.getElementById(`media-${url}`);
                                      if (element) {
                                        element.scrollIntoView({ behavior: 'smooth' });
                                        element.classList.add('ring-4', 'ring-blue-400');
                                        setTimeout(() => element.classList.remove('ring-4', 'ring-blue-400'), 2000);
                                      }
                                    }}
                                    className="block text-blue-500 hover:text-blue-700 underline"
                                  >
                                    {url}
                                  </a>
                                ))}
                              </div>
                            ) : typeof subValue === 'object' ? (
                              <pre className="mt-2 bg-gray-50 p-3 rounded overflow-x-auto text-sm">
                                {JSON.stringify(subValue, null, 2)}
                              </pre>
                            ) : isUrl ? (
                              <a
                                href="#"
                                onClick={(e) => {
                                  e.preventDefault();
                                  const element = document.getElementById(`media-${subValue}`);
                                  if (element) {
                                    element.scrollIntoView({ behavior: 'smooth' });
                                    element.classList.add('ring-4', 'ring-blue-400');
                                    setTimeout(() => element.classList.remove('ring-4', 'ring-blue-400'), 2000);
                                  }
                                }}
                                className="text-blue-500 hover:text-blue-700 underline"
                              >
                                {String(subValue)}
                              </a>
                            ) : (
                              <span className="whitespace-pre-wrap text-gray-600">{String(subValue)}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="ml-4 whitespace-pre-wrap text-gray-600">{String(value)}</div>
                  )}
                </div>
              ))}
            </div>

            {/* Right Panel - Media */}
            <div className="w-1/2 overflow-y-auto pl-3">
              <h3 className="font-semibold text-xl mb-4 sticky top-0 bg-white py-2 z-10 border-b">Generated Media</h3>
              <div className="grid grid-cols-2 gap-4">
                {mediaUrls.map((url, index) => {
                  const isVideo = url.toLowerCase().endsWith('.mp4');
                  return (
                    <div 
                      key={index} 
                      id={`media-${url}`}
                      className="border rounded-lg p-3 transition-all duration-300 bg-gray-50"
                    >
                      <div className="aspect-video relative overflow-hidden rounded bg-gray-100">
                        {isVideo ? (
                          <video
                            controls
                            className="absolute inset-0 w-full h-full object-contain"
                            src={url}
                          >
                            Your browser does not support the video tag.
                          </video>
                        ) : (
                          <img
                            src={url}
                            alt={`Result ${index + 1}`}
                            className="absolute inset-0 w-full h-full object-contain"
                          />
                        )}
                      </div>
                      <div className="mt-2 flex justify-between items-center text-xs">
                        <span className="text-gray-500">Media {index + 1}</span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              window.open(url, '_blank', 'noopener,noreferrer,width=800,height=600');
                            }}
                            className="text-blue-500 hover:text-blue-700 flex items-center gap-1"
                            title="Open in popup window"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-700 flex items-center gap-1"
                            title="Open in new tab"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {!result?.status || result.status === 'running' ? (
          <div className="flex items-center justify-center py-6 flex-shrink-0 gap-4">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-3 text-gray-600">Processing...</span>
            </div>
            <button
              onClick={handleCancel}
              disabled={isCancelling}
              className={`px-4 py-2 rounded text-white ${
                isCancelling 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {isCancelling ? 'Cancelling...' : 'Cancel'}
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
};

const ExecuteWorkflowButton = ({ workflow }: ExecuteWorkflowButtonProps) => {
  const [showDialog, setShowDialog] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowDialog(true)}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        Execute
      </button>

      {showDialog && (
        <ExecuteWorkflowDialog
          workflow={workflow}
          onClose={() => setShowDialog(false)}
        />
      )}
    </>
  );
};

export default ExecuteWorkflowButton;
