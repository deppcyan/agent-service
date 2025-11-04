import { XMarkIcon } from '@heroicons/react/24/outline';
import type { HistoryEntry } from './HistorySidebar';

interface HistoryDetailModalProps {
  history: HistoryEntry;
  onClose: () => void;
}

export default function HistoryDetailModal({ history, onClose }: HistoryDetailModalProps) {
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

  const mediaUrls = history.result?.result ? extractUrls(history.result.result) : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg max-w-[95vw] w-full max-h-[95vh] flex flex-col border border-gray-700 m-4">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-gray-200">{history.workflowName}</h2>
            <div className="flex items-center gap-3 mt-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Status:</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  history.result.status === 'completed' ? 'bg-green-900/50 text-green-400' :
                  history.result.status === 'error' ? 'bg-red-900/50 text-red-400' :
                  'bg-gray-900/50 text-gray-400'
                }`}>
                  {history.result.status}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Executed:</span>
                <span className="text-sm text-gray-300">
                  {new Date(history.executedAt).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-xl p-1"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex gap-6 min-h-0 p-6">
          {/* Left Panel - Results */}
          <div className="w-1/2 overflow-y-auto pr-3 border-r border-gray-700">
            {history.result.error && (
              <div className="bg-red-900/50 border border-red-700 text-red-400 px-4 py-3 rounded mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">Workflow Error</span>
                </div>
                <div className="text-sm">{history.result.error}</div>
                {Object.keys(history.result.result || {}).length > 0 && (
                  <div className="mt-2 text-xs text-red-300">
                    ℹ️ Previous node results are preserved below for analysis
                  </div>
                )}
              </div>
            )}

            {/* Display all result data in a structured way */}
            {Object.entries(history.result?.result || {}).length > 0 && history.result.status === 'error' && (
              <div className="mb-4 bg-yellow-900/20 border border-yellow-700 text-yellow-400 px-4 py-2 rounded text-sm">
                📋 Results from completed nodes (before error occurred):
              </div>
            )}
            
            {Object.entries(history.result?.result || {}).map(([key, value]) => (
              <div key={key} className={`mb-6 border rounded-lg p-4 hover:shadow-lg transition-shadow ${
                history.result.status === 'error' 
                  ? 'border-yellow-600 bg-yellow-900/10' 
                  : 'border-gray-700 bg-gray-800/50'
              }`}>
                <h3 className="font-semibold text-lg mb-3 text-gray-200">{key}</h3>
                {typeof value === 'object' && value !== null ? (
                  <div className="space-y-3">
                    {Object.entries(value).map(([subKey, subValue]) => {
                      const isUrl = typeof subValue === 'string' && (subValue.startsWith('http') || subValue.startsWith('/files/'));
                      return (
                        <div key={subKey} className="ml-4">
                          <span className="font-medium text-gray-300">{subKey}: </span>
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
                            <pre className="mt-2 bg-gray-900/50 p-3 rounded overflow-x-auto text-sm text-gray-300 border border-gray-700">
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
                            <span className="whitespace-pre-wrap text-gray-400">{String(subValue)}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="ml-4 whitespace-pre-wrap text-gray-400">{String(value)}</div>
                )}
              </div>
            ))}
          </div>

          {/* Right Panel - Media */}
          <div className="w-1/2 overflow-y-auto pl-3">
            <h3 className="font-semibold text-xl mb-4 sticky top-0 bg-gray-800 py-2 z-10 border-b border-gray-700 text-gray-200">Generated Media</h3>
            <div className="grid grid-cols-2 gap-4">
              {mediaUrls.map((url, index) => {
                const isVideo = url.toLowerCase().endsWith('.mp4');
                return (
                  <div 
                    key={index} 
                    id={`media-${url}`}
                    className="border border-gray-700 rounded-lg p-3 transition-all duration-300 bg-gray-800/50"
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
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black bg-opacity-70 text-white px-3 py-1 rounded text-sm">
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
      </div>
    </div>
  );
}
