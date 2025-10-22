import { useState, useEffect } from 'react';
import { api, type NodeType } from '../services/api';
import type { NodeTypesResponse } from '../services/nodeTypes';

interface NodeTypeSelectorProps {
  onSelect: (nodeType: NodeType) => void;
}

const NodeTypeSelector = ({ onSelect }: NodeTypeSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
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

  const handleSelect = (nodeType: NodeType) => {
    onSelect(nodeType);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Add Node
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 bg-white rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center">Loading...</div>
          ) : (
            <div className="p-2">
              {Object.entries(categories).map(([category, nodes]) => (
                <div key={category} className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-600 mb-2 px-2">
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </h3>
                  {nodes.map((nodeType) => (
                    <button
                      key={nodeType.name}
                      onClick={() => handleSelect(nodeType)}
                      className="block w-full text-left px-4 py-2 hover:bg-gray-100 rounded text-sm"
                    >
                      {nodeType.name}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NodeTypeSelector;
