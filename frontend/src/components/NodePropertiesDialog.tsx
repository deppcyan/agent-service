import { useState, useEffect, useRef } from 'react';
import { api, type NodeType } from '../services/api';

// Simple tooltip component
const Tooltip = ({ children, content }: { children: React.ReactNode; content?: string }) => {
  if (!content) return <>{children}</>;
  
  return (
    <div className="relative group">
      {children}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 border border-gray-600">
        {content}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
      </div>
    </div>
  );
};

// Auto-resizing textarea component
const AutoResizeTextarea = ({ 
  value, 
  onChange, 
  placeholder, 
  className,
  minRows = 1,
  maxRows = 10
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  className?: string;
  minRows?: number;
  maxRows?: number;
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate the number of lines
    const lineHeight = 24; // Approximate line height in pixels
    const minHeight = minRows * lineHeight;
    const maxHeight = maxRows * lineHeight;
    
    // Set height based on content, but within min/max bounds
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = `${newHeight}px`;
    
    // Enable scrolling if content exceeds max height
    if (textarea.scrollHeight > maxHeight) {
      textarea.style.overflow = 'auto';
    } else {
      textarea.style.overflow = 'hidden';
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  const handleFocus = () => {
    setIsFocused(true);
    // Re-adjust height when focused to ensure proper scrolling
    setTimeout(adjustHeight, 0);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => {
        onChange(e);
        // Adjust height on next tick to ensure value is updated
        setTimeout(adjustHeight, 0);
      }}
      onFocus={handleFocus}
      onBlur={handleBlur}
      placeholder={placeholder}
      className={className}
      style={{ 
        resize: 'none',
        overflow: isFocused ? 'auto' : 'hidden',
        minHeight: `${minRows * 24}px`
      }}
      rows={minRows}
    />
  );
};
import type { Node } from 'reactflow';

interface NodePropertiesDialogProps {
  isOpen: boolean;
  onClose: () => void;
  node: Node;
  onUpdate: (nodeId: string, data: any) => void;
}

const NodePropertiesDialog = ({ isOpen, onClose, node, onUpdate }: NodePropertiesDialogProps) => {
  const [nodeType, setNodeType] = useState<NodeType | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputValues, setInputValues] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadNodeType = async () => {
      try {
        setLoading(true);
        const response = await api.getNodeTypes();
        const type = response.nodes.find(t => t.name === node.data.type);
        if (type) {
          setNodeType(type);
          // Initialize input values with current values or defaults
          const values: Record<string, any> = {};
          Object.entries(type.input_ports).forEach(([key, port]) => {
            // Handle array type default values
            if (port.port_type === 'array' && !node.data.inputs[key]) {
              values[key] = port.default_value || [];
            } else {
              values[key] = node.data.inputs[key] ?? port.default_value;
            }
          });
          setInputValues(values);
        }
      } catch (e) {
        setError('Failed to load node type');
        console.error('Error loading node type:', e);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadNodeType();
    }
  }, [isOpen, node.data.type, node.data.inputs]);

  const handleSave = () => {
    onUpdate(node.id, {
      ...node.data,
      inputs: inputValues,
    });
    onClose();
  };

  if (!isOpen || !nodeType) return null;

  const inputClasses = "w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent";
  const textareaClasses = `${inputClasses} font-mono text-sm h-32`;
  const autoResizeTextareaClasses = `${inputClasses} leading-6`;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
      style={{ zIndex: 9999 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        className="bg-gray-800 rounded-lg p-6 w-[480px] max-h-[80vh] overflow-y-auto border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold mb-4 text-gray-200">Edit Node: {node.data.type}</h2>

        {loading ? (
          <div className="text-center py-4 text-gray-300">Loading...</div>
        ) : error ? (
          <div className="text-red-400 py-4">{error}</div>
        ) : (
          <div className="space-y-4">
            {Object.entries(nodeType.input_ports).map(([key, port]) => (
              <div key={key}>
                <div className="flex items-center gap-2 mb-1">
                  <label className="block text-sm font-medium text-gray-300">
                    {key}
                    {!port.required && ' (optional)'}
                  </label>
                  {port.tooltip && (
                    <Tooltip content={port.tooltip}>
                      <span className="text-gray-400 text-xs cursor-help hover:text-gray-200 transition-colors">
                        ⓘ
                      </span>
                    </Tooltip>
                  )}
                  {port.tooltip && (
                    <span className="text-xs text-gray-400 italic">
                      {port.tooltip}
                    </span>
                  )}
                </div>
                {port.options && port.options.length > 0 ? (
                  <select
                    value={inputValues[key] || ''}
                    onChange={(e) => setInputValues({
                      ...inputValues,
                      [key]: e.target.value
                    })}
                    className={inputClasses}
                  >
                    <option value="">Select {key}</option>
                    {port.options.map((option, index) => (
                      <option key={index} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : port.port_type === 'string' ? (
                  <AutoResizeTextarea
                    value={inputValues[key] || ''}
                    onChange={(e) => setInputValues({
                      ...inputValues,
                      [key]: e.target.value
                    })}
                    className={autoResizeTextareaClasses}
                    placeholder={`Enter ${key}`}
                    minRows={1}
                    maxRows={8}
                  />
                ) : port.port_type === 'number' ? (
                  <input
                    type="number"
                    value={inputValues[key] || ''}
                    onChange={(e) => setInputValues({
                      ...inputValues,
                      [key]: e.target.valueAsNumber || null
                    })}
                    className={inputClasses}
                    placeholder={`Enter ${key}`}
                  />
                ) : port.port_type === 'boolean' ? (
                  <select
                    value={inputValues[key] ? 'true' : 'false'}
                    onChange={(e) => setInputValues({
                      ...inputValues,
                      [key]: e.target.value === 'true'
                    })}
                    className={inputClasses}
                  >
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </select>
                ) : port.port_type === 'array' ? (
                  <div>
                    <textarea
                      value={Array.isArray(inputValues[key]) 
                        ? JSON.stringify(inputValues[key], null, 2)
                        : inputValues[key] || '[]'}
                      onChange={(e) => {
                        try {
                          const value = JSON.parse(e.target.value);
                          if (Array.isArray(value)) {
                            setInputValues({
                              ...inputValues,
                              [key]: value
                            });
                          }
                        } catch {
                          // If not valid JSON array, store as string
                          setInputValues({
                            ...inputValues,
                            [key]: e.target.value
                          });
                        }
                      }}
                      className={textareaClasses}
                      placeholder={`Enter ${key} as JSON array: ["item1", "item2"]`}
                    />
                    <p className="mt-1 text-xs text-gray-400">Enter as JSON array, e.g. ["item1", "item2"]</p>
                  </div>
                ) : port.port_type === 'object' || port.port_type === 'json' ? (
                  <div>
                    <textarea
                      value={typeof inputValues[key] === 'string' 
                        ? inputValues[key] 
                        : JSON.stringify(inputValues[key], null, 2)}
                      onChange={(e) => {
                        try {
                          const value = JSON.parse(e.target.value);
                          setInputValues({
                            ...inputValues,
                            [key]: value
                          });
                        } catch {
                          // If not valid JSON, store as string
                          setInputValues({
                            ...inputValues,
                            [key]: e.target.value
                          });
                        }
                      }}
                      placeholder={`Enter ${key} as JSON object: {}`}
                      className={textareaClasses}
                    />
                    <p className="mt-1 text-xs text-gray-400">Enter as JSON object</p>
                  </div>
                ) : (
                  <AutoResizeTextarea
                    value={inputValues[key] || ''}
                    onChange={(e) => setInputValues({
                      ...inputValues,
                      [key]: e.target.value
                    })}
                    className={autoResizeTextareaClasses}
                    placeholder={`Enter ${key}`}
                    minRows={1}
                    maxRows={8}
                  />
                )}
                {port.required && !inputValues[key] && (
                  <p className="mt-1 text-sm text-red-400">This field is required</p>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-gray-200 bg-gray-700 rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodePropertiesDialog;