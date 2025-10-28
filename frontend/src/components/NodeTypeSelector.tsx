import { useState, useEffect } from 'react';
import { api, type NodeType } from '../services/api';
import type { NodeTypesResponse } from '../services/nodeTypes';

interface NodeTypeSelectorProps {
  onNodeAdd: (nodeType: string) => void;
}

const NodeTypeSelector = ({ onNodeAdd }: NodeTypeSelectorProps) => {
  const [categories, setCategories] = useState<Record<string, NodeType[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadNodeTypes = async () => {
      try {
        const response: NodeTypesResponse = await api.getNodeTypes();

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

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        Loading nodes...
      </div>
    );
  }

  return (
    <div className="p-2">
      {Object.entries(categories).map(([category, nodes]) => (
        <div key={category} className="mb-4">
          <h3 className="text-sm font-semibold text-gray-600 mb-2 px-2">
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </h3>
          <div className="space-y-1">
            {nodes.map((nodeType) => (
              <button
                key={nodeType.name}
                onClick={() => onNodeAdd(nodeType.name)}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100 rounded text-sm"
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