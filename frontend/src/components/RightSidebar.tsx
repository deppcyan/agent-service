import { useState, useCallback, useImperativeHandle, forwardRef, useEffect } from 'react';
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
  result?: any; // 保存执行结果
  error?: string; // 保存错误信息
  completedAt?: Date; // 完成时间
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

// 本地存储键名
const STORAGE_KEY = 'workflow-execution-tabs';

// 本地存储辅助函数
const saveTabsToStorage = (tabs: ExecutionTab[]) => {
  try {
    // 只保存有结果的tabs
    const tabsWithResults = tabs.filter(tab => 
      tab.result || tab.status === 'completed' || tab.status === 'error'
    );
    
    // 序列化时处理Date对象
    const serializedTabs = tabsWithResults.map(tab => ({
      ...tab,
      createdAt: tab.createdAt.toISOString(),
      completedAt: tab.completedAt?.toISOString(),
    }));
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializedTabs));
  } catch (error) {
    console.error('Failed to save tabs to localStorage:', error);
  }
};

const loadTabsFromStorage = (): ExecutionTab[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    
    const parsed = JSON.parse(stored);
    
    // 反序列化时恢复Date对象
    return parsed.map((tab: any) => ({
      ...tab,
      createdAt: new Date(tab.createdAt),
      completedAt: tab.completedAt ? new Date(tab.completedAt) : undefined,
    }));
  } catch (error) {
    console.error('Failed to load tabs from localStorage:', error);
    return [];
  }
};

const RightSidebar = forwardRef<RightSidebarRef, RightSidebarProps>(({ 
  isCollapsed, 
  onToggleCollapse, 
  onSaveHistory 
}, ref) => {
  const [tabs, setTabs] = useState<ExecutionTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);

  // 组件初始化时从本地存储加载tabs
  useEffect(() => {
    const savedTabs = loadTabsFromStorage();
    if (savedTabs.length > 0) {
      setTabs(savedTabs);
      // 设置最后一个有结果的tab为活动tab
      const lastTabWithResult = savedTabs[savedTabs.length - 1];
      if (lastTabWithResult) {
        setActiveTabId(lastTabWithResult.id);
      }
    }
  }, []);

  // 当tabs变化时保存到本地存储
  useEffect(() => {
    if (tabs.length > 0) {
      saveTabsToStorage(tabs);
    }
  }, [tabs]);

  // 创建新的执行tab并立即开始执行
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
    
    // 立即触发执行 - 通过设置一个标记来让ExecutionPanel自动开始执行
    setTimeout(() => {
      // 使用setTimeout确保tab已经被创建并渲染
      const event = new CustomEvent('auto-execute-workflow', { 
        detail: { tabId: newTab.id } 
      });
      window.dispatchEvent(event);
    }, 100);
    
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
              {tabs.map((tab) => {
                const hasResults = tab.result || tab.status === 'completed' || tab.status === 'error';
                return (
                  <div
                    key={tab.id}
                    className={`flex items-center gap-1 px-3 py-2 text-xs cursor-pointer border-r border-gray-700 max-w-[140px] relative ${
                      activeTabId === tab.id
                        ? 'bg-gray-800 text-indigo-400 border-b-2 border-indigo-500'
                        : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                    } ${hasResults ? 'bg-opacity-90' : ''}`}
                    onClick={() => setActiveTabId(tab.id)}
                    title={`${tab.workflowName}${hasResults ? ' (has results)' : ''}`}
                  >
                    {/* 有结果的tab显示一个小图标 */}
                    {hasResults && (
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full border border-gray-800"></div>
                    )}
                    
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
                      <span className={`truncate ${hasResults ? 'font-medium' : ''}`}>
                        {tab.workflowName}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        closeTab(tab.id);
                      }}
                      className={`flex-shrink-0 p-0.5 hover:bg-gray-600 rounded ${
                        hasResults ? 'text-orange-400 hover:text-orange-300' : ''
                      }`}
                      title={hasResults ? 'Close tab (results will be lost)' : 'Close tab'}
                    >
                      <XMarkIcon className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
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
