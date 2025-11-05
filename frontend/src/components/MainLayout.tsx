import { useState, useCallback, useRef } from 'react';
import WorkflowTabs from './WorkflowTabs';
import Sidebar from './Sidebar';
import RightSidebar, { type RightSidebarRef } from './RightSidebar';
import type { WorkflowData } from '../services/api';
import { api } from '../services/api';

export default function MainLayout() {
  const [isRightSidebarCollapsed, setIsRightSidebarCollapsed] = useState(true);
  const [rightSidebarWidth, setRightSidebarWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [isLeftSidebarCollapsed, setIsLeftSidebarCollapsed] = useState(false);
  const rightSidebarRef = useRef<RightSidebarRef>(null);

  // 处理workflow执行
  const handleExecuteWorkflow = useCallback((workflowName: string, workflow: WorkflowData) => {
    if (rightSidebarRef.current) {
      rightSidebarRef.current.createExecutionTab(workflowName, workflow);
      // 如果右侧边栏是折叠的，展开它
      if (isRightSidebarCollapsed) {
        setIsRightSidebarCollapsed(false);
      }
    } else {
      console.error('Right sidebar ref not available');
    }
  }, [isRightSidebarCollapsed]);

  // 保存执行历史
  const handleSaveHistory = useCallback((execution: any) => {
    console.log('Execution completed:', execution);
  }, []);

  // 处理拖拽调整右侧边栏宽度
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 300;
      const maxWidth = window.innerWidth * 0.6;
      
      setRightSidebarWidth(Math.max(minWidth, Math.min(maxWidth, newWidth)));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  // 全局菜单操作
  const handleNewWorkflow = useCallback(() => {
    // 这个将通过WorkflowTabs的API来处理
    if (window.workflowTabsAPI) {
      window.workflowTabsAPI.createNewTab();
    }
  }, []);

  const handleImportWorkflow = useCallback(async () => {
    try {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.json';
      
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
          try {
            const data = JSON.parse(e.target?.result as string);
            const fileName = file.name.replace('.json', '');
            if (window.workflowTabsAPI) {
              window.workflowTabsAPI.importWorkflowToNewTab(fileName, data);
            }
          } catch (error) {
            console.error('Failed to parse workflow file:', error);
            alert('Failed to parse workflow file. Please make sure it is a valid JSON file.');
          }
        };
        reader.readAsText(file);
      };

      input.click();
    } catch (error) {
      console.error('Failed to import workflow:', error);
    }
  }, []);

  const handleSaveWorkflow = useCallback(() => {
    if (window.workflowTabsAPI) {
      window.workflowTabsAPI.saveCurrentWorkflow();
    }
  }, []);

  const handleSaveAsWorkflow = useCallback(() => {
    if (window.workflowTabsAPI) {
      window.workflowTabsAPI.saveAsCurrentWorkflow();
    }
  }, []);

  const handleExportWorkflow = useCallback(() => {
    if (window.workflowTabsAPI) {
      window.workflowTabsAPI.exportCurrentWorkflow();
    }
  }, []);

  const canSave = window.workflowTabsAPI?.canSave() ?? false;

  // 获取当前workflow数据
  const getCurrentWorkflow = useCallback((): WorkflowData => {
    if (window.workflowEditorAPI && window.workflowEditorAPI.getCurrentWorkflow) {
      return window.workflowEditorAPI.getCurrentWorkflow();
    }
    return { nodes: {}, connections: [] };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Top Menu Bar */}
      <div className="flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700 z-10">
        <div className="flex items-center gap-2">
          {/* Individual menu buttons */}
          <button
            onClick={handleNewWorkflow}
            className="px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white rounded transition-colors text-sm"
            title="New Workflow (Ctrl+N)"
          >
            New
          </button>
          
          <button
            onClick={handleImportWorkflow}
            className="px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white rounded transition-colors text-sm"
            title="Import Workflow (Ctrl+O)"
          >
            Import
          </button>
          
          <button
            onClick={handleSaveWorkflow}
            disabled={!canSave}
            className={`px-3 py-2 rounded transition-colors text-sm ${
              canSave 
                ? 'text-gray-300 hover:bg-gray-700 hover:text-white' 
                : 'text-gray-500 cursor-not-allowed'
            }`}
            title="Save Workflow (Ctrl+S)"
          >
            Save
          </button>
          
          <button
            onClick={handleSaveAsWorkflow}
            className="px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white rounded transition-colors text-sm"
            title="Save As (Ctrl+Shift+S)"
          >
            Save As
          </button>
          
          <button
            onClick={handleExportWorkflow}
            className="px-3 py-2 text-gray-300 hover:bg-gray-700 hover:text-white rounded transition-colors text-sm"
            title="Export Workflow (Ctrl+E)"
          >
            Export
          </button>

          {/* Separator */}
          <div className="w-px h-6 bg-gray-600 mx-2"></div>

          {/* Execute button - always show when there's a workflow */}
          <button
            onClick={() => {
              const workflow = getCurrentWorkflow();
              const workflowName = window.workflowTabsAPI?.getCurrentWorkflowName() || 'Untitled Workflow';
              handleExecuteWorkflow(workflowName, workflow);
            }}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors text-sm"
            title="Execute Workflow"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            <span>Execute</span>
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-sm text-gray-400">
            Workflow Editor
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <div className={`bg-gray-800 border-r border-gray-700 flex-shrink-0 transition-all duration-300 ${
          isLeftSidebarCollapsed ? 'w-12' : 'w-64'
        }`}>
          <Sidebar
            onNodeAdd={(nodeType: string) => {
              // This will be handled by the active WorkflowEditor
              if (window.workflowEditorAPI) {
                window.workflowEditorAPI.addNode(nodeType);
              }
            }}
            onWorkflowLoad={async (name: string) => {
              // Load workflow data and create new tab
              try {
                const workflowData = await api.getWorkflow(name);
                if (window.workflowTabsAPI) {
                  window.workflowTabsAPI.importWorkflowToNewTab(name, workflowData);
                }
              } catch (error) {
                console.error('Failed to load workflow:', error);
                alert('Failed to load workflow. Please try again.');
              }
            }}
            isCollapsed={isLeftSidebarCollapsed}
            onToggleCollapse={() => setIsLeftSidebarCollapsed(!isLeftSidebarCollapsed)}
          />
        </div>

        {/* Middle Content - Workflow Tabs */}
        <div 
          className="flex-1 flex flex-col overflow-hidden"
          style={{ 
            width: isRightSidebarCollapsed 
              ? `calc(100% - ${isLeftSidebarCollapsed ? 48 : 256}px)` 
              : `calc(100% - ${isLeftSidebarCollapsed ? 48 : 256}px - ${rightSidebarWidth}px)` 
          }}
        >
          <WorkflowTabs onExecuteWorkflow={handleExecuteWorkflow} />
        </div>

        {/* Resize Handle */}
        {!isRightSidebarCollapsed && (
          <div
            className={`w-1 bg-gray-600 hover:bg-gray-500 cursor-col-resize flex-shrink-0 ${
              isDragging ? 'bg-gray-400' : ''
            }`}
            onMouseDown={handleMouseDown}
          />
        )}

        {/* Right Sidebar - Execution Results */}
        <div 
          className={`bg-gray-800 border-l border-gray-700 flex-shrink-0 transition-all duration-300 ${
            isRightSidebarCollapsed ? 'w-12' : ''
          }`}
          style={{ 
            width: isRightSidebarCollapsed ? '48px' : `${rightSidebarWidth}px` 
          }}
        >
          <RightSidebar
            ref={rightSidebarRef}
            isCollapsed={isRightSidebarCollapsed}
            onToggleCollapse={() => setIsRightSidebarCollapsed(!isRightSidebarCollapsed)}
            onSaveHistory={handleSaveHistory}
          />
        </div>
      </div>
    </div>
  );
}

// 声明全局类型
declare global {
  interface Window {
    workflowTabsAPI?: {
      createNewTab: () => void;
      importWorkflowToNewTab: (name: string, data: WorkflowData) => void;
      saveCurrentWorkflow: () => void;
      saveAsCurrentWorkflow: () => void;
      exportCurrentWorkflow: () => void;
      canSave: () => boolean;
      getCurrentWorkflowName: () => string;
    };
    workflowEditorAPI?: {
      addNode: (nodeType: string) => void;
      loadWorkflow: (name: string) => void;
      saveWorkflow?: () => void;
      saveAsWorkflow?: () => void;
      exportWorkflow?: () => void;
      getCurrentWorkflow?: () => WorkflowData;
    };
  }
}
