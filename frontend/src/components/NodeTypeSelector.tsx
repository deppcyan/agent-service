import { useState, useEffect } from 'react';
import { type NodeType } from '../services/api';
import type { NodeTypesResponse } from '../services/nodeTypes';
import { nodesCache } from '../services/nodesCache';

interface NodeTypeSelectorProps {
  onNodeAdd: (nodeType: string) => void;
}

const NodeTypeSelector = ({ onNodeAdd }: NodeTypeSelectorProps) => {
  const [categories, setCategories] = useState<Record<string, NodeType[]>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const loadNodeTypes = async () => {
      try {
        const response: NodeTypesResponse = await nodesCache.getNodeTypes();

        // Group node types by category using the categories from response
        const grouped = Object.entries(response.categories).reduce((acc, [category, nodeNames]) => {
          acc[category] = nodeNames
            .map(name => response.nodes.find(node => node.name === name))
            .filter((node): node is NodeType => node !== undefined);
          return acc;
        }, {} as Record<string, NodeType[]>);

        setCategories(grouped);
      } catch (error) {
        console.error('Failed to load node types:', error);
      } finally {
        setLoading(false);
      }
    };

    loadNodeTypes();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const response: NodeTypesResponse = await nodesCache.refreshCache();
      
      // Group node types by category using the categories from response
      const grouped = Object.entries(response.categories).reduce((acc, [category, nodeNames]) => {
        acc[category] = nodeNames
          .map(name => response.nodes.find(node => node.name === name))
          .filter((node): node is NodeType => node !== undefined);
        return acc;
      }, {} as Record<string, NodeType[]>);

      setCategories(grouped);
    } catch (error) {
      console.error('Failed to refresh node types:', error);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-400">
        Loading nodes...
      </div>
    );
  }

  return (
    <div className="p-2">
      <div className="flex justify-between items-center mb-3 px-2">
        <h2 className="text-sm font-semibold text-indigo-400">Node Types</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-xs text-gray-400 hover:text-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Refresh node types"
        >
          {refreshing ? '⟳' : '↻'}
        </button>
      </div>
      {Object.entries(categories).map(([category, nodes]) => (
        <div key={category} className="mb-4">
          <h3 className="text-sm font-semibold text-indigo-400 mb-2 px-2">
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </h3>
          <div className="space-y-1">
            {nodes.map((nodeType) => (
              <button
                key={nodeType.name}
                onClick={() => onNodeAdd(nodeType.name)}
                className="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white rounded text-sm"
              >
                {nodeType.name}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default NodeTypeSelector;