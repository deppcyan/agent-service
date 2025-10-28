import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import NodeTypeSelector from './NodeTypeSelector';
import WorkflowList from './WorkflowList.tsx';

interface SidebarProps {
  onNodeAdd: (nodeType: string) => void;
  onWorkflowLoad: (workflowName: string) => void;
}

export default function Sidebar({ onNodeAdd, onWorkflowLoad }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<'nodes' | 'workflows'>('nodes');

  return (
    <div className={`bg-gray-800 border-r border-gray-700 flex flex-col transition-all duration-300 ${isCollapsed ? 'w-12' : 'w-64'}`}>
      {/* Collapse button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="p-2 hover:bg-gray-700 self-end text-gray-400 hover:text-gray-200"
      >
        {isCollapsed ? (
          <ChevronRightIcon className="w-5 h-5" />
        ) : (
          <ChevronLeftIcon className="w-5 h-5" />
        )}
      </button>

      {/* Tabs */}
      {!isCollapsed && (
        <div className="flex border-b border-gray-700">
          <button
            className={`flex-1 py-2 px-4 ${
              activeTab === 'nodes' 
                ? 'bg-gray-900 border-b-2 border-indigo-500 text-indigo-400' 
                : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
            }`}
            onClick={() => setActiveTab('nodes')}
          >
            Nodes
          </button>
          <button
            className={`flex-1 py-2 px-4 ${
              activeTab === 'workflows' 
                ? 'bg-gray-900 border-b-2 border-indigo-500 text-indigo-400' 
                : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
            }`}
            onClick={() => setActiveTab('workflows')}
          >
            Workflows
          </button>
        </div>
      )}

      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'nodes' ? (
            <NodeTypeSelector onNodeAdd={onNodeAdd} />
          ) : (
            <WorkflowList onWorkflowLoad={onWorkflowLoad} />
          )}
        </div>
      )}
    </div>
  );
}
