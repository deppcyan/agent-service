import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import HistoryDetailModal from './HistoryDetailModal';

export interface HistoryEntry {
  id: string;
  workflowName: string;
  workflow: any;
  result: any;
  executedAt: Date;
  taskId: string;
}

interface HistorySidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  history: HistoryEntry[];
  onDeleteHistory: (id: string) => void;
  onClearAllHistory: () => void;
}

export default function HistorySidebar({ 
  isCollapsed, 
  onToggleCollapse, 
  history, 
  onDeleteHistory, 
  onClearAllHistory 
}: HistorySidebarProps) {
  const [selectedHistory, setSelectedHistory] = useState<HistoryEntry | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'error'>('all');

  // 过滤历史记录
  const filteredHistory = history.filter(entry => {
    const matchesSearch = entry.workflowName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'completed' && entry.result.status === 'completed') ||
      (statusFilter === 'error' && entry.result.status === 'error');
    
    return matchesSearch && matchesStatus;
  });

  // 按时间排序（最新的在前）
  const sortedHistory = filteredHistory.sort((a, b) => 
    new Date(b.executedAt).getTime() - new Date(a.executedAt).getTime()
  );

  // 格式化时间
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return new Date(date).toLocaleDateString();
  };

  return (
    <>
      <div className={`bg-gray-800 border-r border-gray-700 flex flex-col transition-all duration-300 ${
        isCollapsed ? 'w-12' : 'w-80'
      }`}>
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-700">
          {!isCollapsed && (
            <h3 className="text-sm font-medium text-gray-300">Execution History</h3>
          )}
          <button
            onClick={onToggleCollapse}
            className="p-1 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded"
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-4 h-4" />
            ) : (
              <ChevronLeftIcon className="w-4 h-4" />
            )}
          </button>
        </div>

        {!isCollapsed && (
          <>
            {/* Search and filters */}
            <div className="p-3 border-b border-gray-700 space-y-3">
              <input
                type="text"
                placeholder="Search workflows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
              
              <div className="flex gap-2">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="flex-1 px-2 py-1 bg-gray-900 border border-gray-600 rounded text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="error">Error</option>
                </select>
                
                {history.length > 0 && (
                  <button
                    onClick={onClearAllHistory}
                    className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs"
                    title="Clear all history"
                  >
                    Clear All
                  </button>
                )}
              </div>
            </div>

            {/* History list */}
            <div className="flex-1 overflow-y-auto">
              {sortedHistory.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
                  <div className="text-center">
                    <div className="mb-2">No execution history</div>
                    <div className="text-xs">
                      {searchTerm || statusFilter !== 'all' 
                        ? 'No results match your filters' 
                        : 'Execute workflows to see history'
                      }
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-2 space-y-2">
                  {sortedHistory.map((entry) => (
                    <div
                      key={entry.id}
                      className="bg-gray-900 rounded-lg p-3 hover:bg-gray-700 transition-colors cursor-pointer border border-gray-700"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm text-gray-200 truncate" title={entry.workflowName}>
                            {entry.workflowName}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <div 
                              className={`w-2 h-2 rounded-full ${
                                entry.result.status === 'completed' ? 'bg-green-500' :
                                entry.result.status === 'error' ? 'bg-red-500' :
                                'bg-gray-500'
                              }`}
                            />
                            <span className="text-xs text-gray-400">
                              {formatTime(entry.executedAt)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-1 ml-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedHistory(entry);
                            }}
                            className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-gray-200"
                            title="View details"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteHistory(entry.id);
                            }}
                            className="p-1 hover:bg-gray-600 rounded text-gray-400 hover:text-red-400"
                            title="Delete"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Status and summary */}
                      <div className="text-xs text-gray-500">
                        <div className={`inline-block px-2 py-1 rounded ${
                          entry.result.status === 'completed' ? 'bg-green-900/50 text-green-400' :
                          entry.result.status === 'error' ? 'bg-red-900/50 text-red-400' :
                          'bg-gray-900/50 text-gray-400'
                        }`}>
                          {entry.result.status}
                        </div>
                        
                        {entry.result.error && (
                          <div className="mt-1 text-red-400 truncate" title={entry.result.error}>
                            Error: {entry.result.error}
                          </div>
                        )}
                        
                        {entry.result.result && Object.keys(entry.result.result).length > 0 && (
                          <div className="mt-1 text-gray-400">
                            {Object.keys(entry.result.result).length} result{Object.keys(entry.result.result).length !== 1 ? 's' : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer stats */}
            {history.length > 0 && (
              <div className="p-3 border-t border-gray-700 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Total: {history.length}</span>
                  <span>
                    Completed: {history.filter(h => h.result.status === 'completed').length} | 
                    Errors: {history.filter(h => h.result.status === 'error').length}
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* History detail modal */}
      {selectedHistory && (
        <HistoryDetailModal
          history={selectedHistory}
          onClose={() => setSelectedHistory(null)}
        />
      )}
    </>
  );
}
