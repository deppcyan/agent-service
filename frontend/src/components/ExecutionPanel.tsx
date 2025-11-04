import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { ExecutionTab } from './RightSidebar';

interface ExecutionPanelProps {
  tab: ExecutionTab;
  onUpdateTab: (updates: Partial<ExecutionTab>) => void;
  onSaveHistory: (execution: any) => void;
}

interface WorkflowResult {
  status: 'running' | 'completed' | 'error' | 'cancelled' | 'not_found';
  result: Record<string, any>;
  error?: string;
}

const POLL_INTERVAL = 2000; // 2 seconds

export default function ExecutionPanel({ tab, onUpdateTab, onSaveHistory }: ExecutionPanelProps) {
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  // 执行workflow
  const executeWorkflow = useCallback(async () => {
    if (isExecuting) return;
    
    try {
      setIsExecuting(true);
      setError(null);
      setResult(null);
      
      const response = await api.executeWorkflow({ workflow: tab.workflow });
      onUpdateTab({ 
        taskId: response.task_id, 
        status: 'running' 
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to execute workflow');
      onUpdateTab({ status: 'error' });
    } finally {
      setIsExecuting(false);
    }
  }, [tab.workflow, onUpdateTab, isExecuting]);

  // Poll for results when we have a task ID
  useEffect(() => {
    if (!tab.taskId || tab.status !== 'running') return;

    let mounted = true;
    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getWorkflowStatus(tab.taskId!);
        if (mounted) {
          setResult(prevResult => {
            // If we have an error status, preserve previous results but update status and error
            if (status.status === 'error') {
              return {
                ...status,
                result: prevResult?.result || status.result || {}
              };
            }
            // For other statuses, use the new result normally
            return status;
          });

          // Update tab status
          const tabStatus = status.status === 'not_found' ? 'error' : status.status;
          onUpdateTab({ status: tabStatus });
        }
        
        // Stop polling if workflow is complete or failed
        if (status.status !== 'running') {
          clearInterval(pollInterval);
          
          // Save to history when completed
          if (status.status === 'completed' || status.status === 'error') {
            const historyEntry = {
              id: `history-${Date.now()}`,
              workflowName: tab.workflowName,
              workflow: tab.workflow,
              result: status,
              executedAt: new Date(),
              taskId: tab.taskId,
            };
            onSaveHistory(historyEntry);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to get workflow status');
        onUpdateTab({ status: 'error' });
        clearInterval(pollInterval);
      }
    }, POLL_INTERVAL);

    return () => {
      mounted = false;
      clearInterval(pollInterval);
    };
  }, [tab.taskId, tab.status, tab.workflowName, tab.workflow, onUpdateTab, onSaveHistory]);

  // Handle workflow cancellation
  const handleCancel = async () => {
    if (isCancelling || !tab.taskId) return;
    
    try {
      setIsCancelling(true);
      await api.cancelWorkflow(tab.taskId);
      onUpdateTab({ status: 'cancelled' });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to cancel workflow');
    } finally {
      setIsCancelling(false);
    }
  };

  // Extract only local_urls from results
  const extractUrls = (obj: any): string[] => {
    if (!obj) return [];
    
    if (Array.isArray(obj)) {
      return obj.flatMap(item => extractUrls(item));
    }
    
    if (typeof obj === 'object') {
      // Only extract URLs from local_urls field
      if (obj.hasOwnProperty('local_urls')) {
        return Array.isArray(obj.local_urls) ? obj.local_urls : [];
      }
      // Continue searching in nested objects
      return Object.values(obj).flatMap(value => extractUrls(value));
    }
    
    return [];
  };

  const mediaUrls = result?.result ? extractUrls(result.result) : [];

  return (
    <div className="flex flex-col h-full max-h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-200">{tab.workflowName}</h3>
          <div className="flex items-center gap-2">
            {tab.status === 'idle' && (
              <button
                onClick={executeWorkflow}
                disabled={isExecuting}
                className={`px-3 py-1 rounded text-sm ${
                  isExecuting 
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                }`}
              >
                {isExecuting ? 'Starting...' : 'Execute'}
              </button>
            )}
            {tab.status === 'running' && (
              <button
                onClick={handleCancel}
                disabled={isCancelling}
                className={`px-3 py-1 rounded text-sm ${
                  isCancelling 
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                    : 'bg-red-600 text-white hover:bg-red-700'
                }`}
              >
                {isCancelling ? 'Cancelling...' : 'Cancel'}
              </button>
            )}
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Status:</span>
          <span className={`px-2 py-1 rounded text-xs ${
            tab.status === 'completed' ? 'bg-green-900/50 text-green-400' :
            tab.status === 'running' ? 'bg-blue-900/50 text-blue-400' :
            tab.status === 'error' ? 'bg-red-900/50 text-red-400' :
            tab.status === 'cancelled' ? 'bg-yellow-900/50 text-yellow-400' :
            'bg-gray-900/50 text-gray-400'
          }`}>
            {tab.status}
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-400 px-4 py-3 mx-4 mt-4 rounded flex-shrink-0">
          {error}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {result ? (
          <div className="h-full overflow-y-auto">
            {/* Results section */}
            <div className="p-4">
              {result.error && (
                <div className="bg-red-900/50 border border-red-700 text-red-400 px-4 py-3 rounded mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="font-semibold">Workflow Error</span>
                  </div>
                  <div className="text-sm">{result.error}</div>
                  {Object.keys(result.result || {}).length > 0 && (
                    <div className="mt-2 text-xs text-red-300">
                      ℹ️ Previous node results are preserved below for analysis
                    </div>
                  )}
                </div>
              )}

              {/* Display all result data in a structured way */}
              {Object.entries(result.result || {}).length > 0 && result.status === 'error' && (
                <div className="mb-4 bg-yellow-900/20 border border-yellow-700 text-yellow-400 px-4 py-2 rounded text-sm">
                  📋 Results from completed nodes (before error occurred):
                </div>
              )}
              
              {Object.entries(result.result || {}).map(([key, value]) => (
                <div key={key} className={`mb-4 border rounded-lg p-3 hover:shadow-lg transition-shadow ${
                  result.status === 'error' 
                    ? 'border-yellow-600 bg-yellow-900/10' 
                    : 'border-gray-700 bg-gray-800/50'
                }`}>
                  <h4 className="font-semibold text-sm mb-2 text-gray-200">{key}</h4>
                  {typeof value === 'object' ? (
                    <div className="space-y-2">
                      {Object.entries(value).map(([subKey, subValue]) => {
                        const isUrl = typeof subValue === 'string' && (subValue.startsWith('http') || subValue.startsWith('/files/'));
                        return (
                          <div key={subKey} className="ml-2">
                            <span className="font-medium text-xs text-gray-300">{subKey}: </span>
                            {Array.isArray(subValue) && subValue.every(item => typeof item === 'string' && (item.startsWith('http') || item.startsWith('/files/'))) ? (
                              <div className="space-y-1">
                                {subValue.map((url, idx) => (
                                  <a
                                    key={idx}
                                    href="#"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      const element = document.getElementById(`media-${url}`);
                                      if (element) {
                                        element.scrollIntoView({ behavior: 'smooth' });
                                        element.classList.add('ring-2', 'ring-blue-400');
                                        setTimeout(() => element.classList.remove('ring-2', 'ring-blue-400'), 2000);
                                      }
                                    }}
                                    className="block text-blue-500 hover:text-blue-700 underline text-xs"
                                  >
                                    {url}
                                  </a>
                                ))}
                              </div>
                            ) : typeof subValue === 'object' ? (
                              <pre className="mt-1 bg-gray-900/50 p-2 rounded overflow-x-auto text-xs text-gray-300 border border-gray-700">
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
                                    element.classList.add('ring-2', 'ring-blue-400');
                                    setTimeout(() => element.classList.remove('ring-2', 'ring-blue-400'), 2000);
                                  }
                                }}
                                className="text-blue-500 hover:text-blue-700 underline text-xs"
                              >
                                {String(subValue)}
                              </a>
                            ) : (
                              <span className="whitespace-pre-wrap text-gray-400 text-xs">{String(subValue)}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="ml-2 whitespace-pre-wrap text-gray-400 text-xs">{String(value)}</div>
                  )}
                </div>
              ))}
            </div>

            {/* Media section */}
            {mediaUrls.length > 0 && (
              <div className="border-t border-gray-700 p-4">
                <h4 className="font-semibold text-sm mb-3 text-gray-200">Generated Media</h4>
                <div className="grid grid-cols-1 gap-3">
                  {mediaUrls.map((url, index) => {
                    const isVideo = url.toLowerCase().endsWith('.mp4');
                    return (
                      <div 
                        key={index} 
                        id={`media-${url}`}
                        className="border border-gray-700 rounded-lg p-2 transition-all duration-300 bg-gray-800/50"
                      >
                        <div 
                          className="aspect-video relative overflow-hidden rounded bg-gray-900 cursor-pointer group"
                          onClick={() => window.open(url, '_blank', 'noopener,noreferrer')}
                          title="Click to open in new tab"
                        >
                          {isVideo ? (
                            <video
                              controls
                              className="absolute inset-0 w-full h-full object-contain"
                              src={url}
                              onClick={(e) => e.stopPropagation()} // Prevent parent click when using video controls
                            >
                              Your browser does not support the video tag.
                            </video>
                          ) : (
                            <img
                              src={url}
                              alt={`Result ${index + 1}`}
                              className="absolute inset-0 w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
                            />
                          )}
                          {/* Overlay hint for images */}
                          {!isVideo && (
                            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
                                Click to open
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="mt-2 flex justify-between items-center text-xs">
                          <span className="text-gray-400">Media {index + 1}</span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                window.open(url, '_blank', 'noopener,noreferrer,width=800,height=600');
                              }}
                              className="text-blue-500 hover:text-blue-700 flex items-center gap-1"
                              title="Open in popup window"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            )}
          </div>
        ) : tab.status === 'running' ? (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
              <span className="text-gray-400">Processing...</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8 text-gray-500 text-sm">
            <div className="text-center">
              <div className="mb-2">Ready to execute</div>
              <div className="text-xs">Click "Execute" to start the workflow</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
