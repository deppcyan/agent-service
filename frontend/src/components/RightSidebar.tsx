import { useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import ExecutionPanel from './ExecutionPanel';
import type { WorkflowData } from '../services/api';

export interface ExecutionTab {
  id: string;
  workflowName: string;
  workflow: WorkflowData;
  taskId: string | null;
  status: 'idle' | 'running' | 'completed' | 'error' | 'cancelled';
  createdAt: Date;
}

interface RightSidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onSaveHistory: (execution: any) => void;
}

export interface RightSidebarRef {
  createExecutionTab: (workflowName: string, workflow: WorkflowData) => string;
  updateTab: (tabId: string, updates: Partial<ExecutionTab>) => void;
  closeTab: (tabId: string) => void;
}

const RightSidebar = forwardRef<RightSidebarRef, RightSidebarProps>(({ 
  isCollapsed, 
  onToggleCollapse, 
  onSaveHistory 
}, ref) => {
  const [tabs, setTabs] = useState<ExecutionTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);

  // 创建新的执行tab
  const createExecutionTab = useCallback((workflowName: string, workflow: WorkflowData) => {
    const newTab: ExecutionTab = {
      id: `tab-${Date.now()}`,
      workflowName,
      workflow,
      taskId: null,
      status: 'idle',
      createdAt: new Date(),
    };
    
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newTab.id);
    
    return newTab.id;
  }, []);

  // 更新tab状态
  const updateTab = useCallback((tabId: string, updates: Partial<ExecutionTab>) => {
    setTabs(prev => prev.map(tab => 
      tab.id === tabId ? { ...tab, ...updates } : tab
    ));
  }, []);

  // 关闭tab
  const closeTab = useCallback((tabId: string) => {
    setTabs(prev => {
      const newTabs = prev.filter(tab => tab.id !== tabId);
      
      // 如果关闭的是当前活动tab，切换到其他tab
      if (activeTabId === tabId) {
        const currentIndex = prev.findIndex(tab => tab.id === tabId);
        if (newTabs.length > 0) {
          const nextIndex = Math.min(currentIndex, newTabs.length - 1);
          setActiveTabId(newTabs[nextIndex].id);
        } else {
          setActiveTabId(null);
        }
      }
      
      return newTabs;
    });
  }, [activeTabId]);

  // 获取当前活动tab
  const activeTab = tabs.find(tab => tab.id === activeTabId);

  // 使用useImperativeHandle暴露API给父组件
  useImperativeHandle(ref, () => ({
    createExecutionTab,
    updateTab,
    closeTab,
  }), [createExecutionTab, updateTab, closeTab]);

  return (
    <div className={`bg-gray-800 border-l border-gray-700 flex flex-col h-full w-full transition-all duration-300`}>
      {/* Header with collapse button */}
      <div className="flex items-center justify-between p-2 border-b border-gray-700">
        {!isCollapsed && (
          <h3 className="text-sm font-medium text-gray-300">Workflow Execution</h3>
        )}
        <button
          onClick={onToggleCollapse}
          className="p-1 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded"
        >
          {isCollapsed ? (
            <ChevronLeftIcon className="w-4 h-4" />
          ) : (
            <ChevronRightIcon className="w-4 h-4" />
          )}
        </button>
      </div>

      {!isCollapsed && (
        <>
          {/* Tabs */}
          {tabs.length > 0 && (
            <div className="flex flex-wrap border-b border-gray-700 bg-gray-900">
              {tabs.map((tab) => (
                <div
                  key={tab.id}
                  className={`flex items-center gap-1 px-3 py-2 text-xs cursor-pointer border-r border-gray-700 max-w-[120px] ${
                    activeTabId === tab.id
                      ? 'bg-gray-800 text-indigo-400 border-b-2 border-indigo-500'
                      : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                  }`}
                  onClick={() => setActiveTabId(tab.id)}
                >
                  <div className="flex items-center gap-1 flex-1 min-w-0">
                    <div 
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        tab.status === 'running' ? 'bg-blue-500 animate-pulse' :
                        tab.status === 'completed' ? 'bg-green-500' :
                        tab.status === 'error' ? 'bg-red-500' :
                        tab.status === 'cancelled' ? 'bg-yellow-500' :
                        'bg-gray-500'
                      }`}
                    />
                    <span className="truncate" title={tab.workflowName}>
                      {tab.workflowName}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeTab(tab.id);
                    }}
                    className="flex-shrink-0 p-0.5 hover:bg-gray-600 rounded"
                  >
                    <XMarkIcon className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto min-h-0 max-h-full">
            {activeTab ? (
              <ExecutionPanel
                key={activeTab.id}
                tab={activeTab}
                onUpdateTab={(updates) => updateTab(activeTab.id, updates)}
                onSaveHistory={onSaveHistory}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                <div className="text-center">
                  <div className="mb-2">No workflow execution</div>
                  <div className="text-xs">Click "Execute" to start a workflow</div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
});

RightSidebar.displayName = 'RightSidebar';

export default RightSidebar;
