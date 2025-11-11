import React, { useState, useCallback } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import WorkflowEditor from './WorkflowEditor';
import type { WorkflowData } from '../services/api';

export interface WorkflowTab {
  id: string;
  name: string;
  workflowData: WorkflowData | null;
  isDirty: boolean;
  isNew: boolean;
}

interface WorkflowTabsProps {
  onExecuteWorkflow: (workflowName: string, workflow: WorkflowData) => void;
}

export default function WorkflowTabs({ onExecuteWorkflow }: WorkflowTabsProps) {
  const [tabs, setTabs] = useState<WorkflowTab[]>([
    {
      id: 'tab-1',
      name: 'Untitled Workflow',
      workflowData: null,
      isDirty: false,
      isNew: true,
    }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('tab-1');

  // 创建新的workflow tab
  const createNewTab = useCallback(() => {
    const newTab: WorkflowTab = {
      id: `tab-${Date.now()}`,
      name: 'Untitled Workflow',
      workflowData: null,
      isDirty: false,
      isNew: true,
    };
    
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newTab.id);
  }, []);

  // 关闭tab
  const closeTab = useCallback((tabId: string) => {
    setTabs(prev => {
      const newTabs = prev.filter(tab => tab.id !== tabId);
      
      // 如果没有tab了，创建一个新的
      if (newTabs.length === 0) {
        const defaultTab: WorkflowTab = {
          id: `tab-${Date.now()}`,
          name: 'Untitled Workflow',
          workflowData: null,
          isDirty: false,
          isNew: true,
        };
        newTabs.push(defaultTab);
        setActiveTabId(defaultTab.id);
      } else {
        // 如果关闭的是当前活动tab，切换到其他tab
        if (activeTabId === tabId) {
          const currentIndex = prev.findIndex(tab => tab.id === tabId);
          const nextIndex = Math.min(currentIndex, newTabs.length - 1);
          setActiveTabId(newTabs[nextIndex].id);
        }
      }
      
      return newTabs;
    });
  }, [activeTabId]);

  // 更新tab信息
  const updateTab = useCallback((tabId: string, updates: Partial<WorkflowTab>) => {
    setTabs(prev => prev.map(tab => 
      tab.id === tabId ? { ...tab, ...updates } : tab
    ));
  }, []);

  // 加载workflow到当前tab
  const loadWorkflowToCurrentTab = useCallback((name: string, workflowData: WorkflowData) => {
    updateTab(activeTabId, {
      name,
      workflowData,
      isDirty: false,
      isNew: false,
    });
  }, [activeTabId, updateTab]);

  // 导入workflow到新tab
  const importWorkflowToNewTab = useCallback((name: string, workflowData: WorkflowData) => {
    const newTab: WorkflowTab = {
      id: `tab-${Date.now()}`,
      name,
      workflowData,
      isDirty: false,
      isNew: false,
    };
    
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newTab.id);
  }, []);

  // 获取当前活动tab
  const activeTab = tabs.find(tab => tab.id === activeTabId);

  // Add keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if the focus is on a text input, textarea, or contenteditable element
      const activeElement = document.activeElement;
      const isTextInput = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.getAttribute('contenteditable') === 'true'
      );

      // Don't intercept keyboard events when user is typing in text inputs
      if (isTextInput) {
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'n':
            e.preventDefault();
            createNewTab();
            break;
          case 't':
            e.preventDefault();
            createNewTab();
            break;
          case 'w':
            if (tabs.length > 1) {
              e.preventDefault();
              closeTab(activeTabId);
            }
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [tabs.length, activeTabId, createNewTab, closeTab]);

  // 暴露给WorkflowEditor的API
  const workflowTabsAPI = {
    updateCurrentTab: (updates: Partial<WorkflowTab>) => updateTab(activeTabId, updates),
    loadWorkflowToCurrentTab,
    importWorkflowToNewTab,
    getCurrentTab: () => activeTab,
    createNewTab,
  };

  // 暴露给全局的API
  const globalAPI = {
    createNewTab,
    importWorkflowToNewTab,
    saveCurrentWorkflow: () => {
      if (window.workflowEditorAPI && window.workflowEditorAPI.saveWorkflow) {
        window.workflowEditorAPI.saveWorkflow();
      }
    },
    saveAsCurrentWorkflow: () => {
      if (window.workflowEditorAPI && window.workflowEditorAPI.saveAsWorkflow) {
        window.workflowEditorAPI.saveAsWorkflow();
      }
    },
    exportCurrentWorkflow: () => {
      if (window.workflowEditorAPI && window.workflowEditorAPI.exportWorkflow) {
        window.workflowEditorAPI.exportWorkflow();
      }
    },
    canSave: () => {
      const currentTab = activeTab;
      return Boolean(currentTab && !currentTab.isNew);
    },
    getCurrentWorkflowName: () => {
      return activeTab?.name || '';
    },
  };

  // 将API暴露给全局
  React.useEffect(() => {
    window.workflowTabsAPI = globalAPI;
    return () => {
      delete window.workflowTabsAPI;
    };
  }, [globalAPI]);

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Tab Bar */}
      <div className="flex items-center bg-gray-800 border-b border-gray-700">
        <div className="flex flex-1 overflow-x-auto">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={`flex items-center gap-2 px-4 py-3 border-r border-gray-700 cursor-pointer min-w-0 max-w-[200px] ${
                activeTabId === tab.id
                  ? 'bg-gray-900 text-indigo-400 border-b-2 border-indigo-500'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
              }`}
              onClick={() => setActiveTabId(tab.id)}
            >
              <span className="truncate flex-1" title={tab.name}>
                {tab.name}
                {tab.isDirty && '*'}
              </span>
              {tabs.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                  className="flex-shrink-0 p-1 hover:bg-gray-600 rounded text-gray-500 hover:text-gray-300"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
        
        {/* New Tab Button */}
        <button
          onClick={createNewTab}
          className="flex items-center gap-1 px-3 py-3 text-gray-400 hover:text-gray-200 hover:bg-gray-700"
          title="New Workflow"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab && (
          <WorkflowEditor
            key={activeTab.id}
            tabId={activeTab.id}
            initialWorkflowData={activeTab.workflowData}
            workflowName={activeTab.name}
            onExecuteWorkflow={onExecuteWorkflow}
            workflowTabsAPI={workflowTabsAPI}
          />
        )}
      </div>
    </div>
  );
}
