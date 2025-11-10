import { useState, useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
  ConnectionMode,
  useReactFlow,
  ReactFlowProvider,
} from 'reactflow';
import type { Node, Connection as ReactFlowConnection } from 'reactflow';
import { api, type Connection } from '../services/api';
import { nodesCache } from '../services/nodesCache';
import type { NodeType } from '../services/api';

interface SubWorkflowEditorProps {
  initialSubWorkflow?: {
    nodes: Array<{ type: string; id: string; input_values?: Record<string, any> }>;
    connections: Connection[];
  };
  initialResultNodeId?: string;
  initialResultPortName?: string;
  onSave: (
    subWorkflow: {
      nodes: Array<{ type: string; id: string; input_values?: Record<string, any> }>;
      connections: Connection[];
    },
    resultNodeId: string,
    resultPortName: string
  ) => void;
  onCancel: () => void;
}

// 简单节点组件（用于子工作流）
const SimpleNode = ({ data, id }: { data: any; id: string }) => {
  const isForEachItemNode = data.type === 'ForEachItemNode';
  
  return (
    <div 
      className={`px-4 py-3 rounded-lg shadow-lg ${
        isForEachItemNode 
          ? 'bg-green-700 ring-2 ring-green-500' 
          : data.isResultNode 
          ? 'bg-indigo-700 ring-2 ring-indigo-400' 
          : 'bg-gray-800 ring-1 ring-gray-700'
      }`}
      style={{ minWidth: 200 }}
    >
      {/* 标题 */}
      <div className="font-bold text-sm text-white mb-2">
        {id}
      </div>
      <div className="text-xs text-gray-300 mb-2">
        {data.type}
      </div>
      
      {isForEachItemNode && (
        <div className="text-xs text-green-300 mb-2">
          ⭐ 循环入口
        </div>
      )}
      
      {data.isResultNode && (
        <div className="text-xs text-indigo-300 mb-2">
          🎯 结果节点
        </div>
      )}
      
      {/* 输入端口 */}
      {data.inputPorts?.map((port: string) => (
        <div key={`input-${port}`} className="relative mb-1">
          <Handle
            type="target"
            position={Position.Left}
            id={port}
            className="w-2 h-2 !bg-blue-500"
            style={{ top: '50%' }}
          />
          <div className="ml-3 text-xs text-gray-300">{port}</div>
        </div>
      ))}
      
      {/* 输出端口 */}
      {data.outputPorts?.map((port: string) => (
        <div key={`output-${port}`} className="relative mb-1 text-right">
          <Handle
            type="source"
            position={Position.Right}
            id={port}
            className="w-2 h-2 !bg-blue-500"
            style={{ top: '50%' }}
          />
          <div className="mr-3 text-xs text-gray-300">{port}</div>
        </div>
      ))}
    </div>
  );
};

const nodeTypes = {
  simple: SimpleNode,
};

function SubWorkflowEditorContent({
  initialSubWorkflow,
  initialResultNodeId,
  initialResultPortName,
  onSave,
  onCancel,
}: SubWorkflowEditorProps) {
  const [resultNodeId, setResultNodeId] = useState(initialResultNodeId || '');
  const [resultPortName, setResultPortName] = useState(initialResultPortName || '');
  const [validation, setValidation] = useState<{ valid: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [nodeTypesList, setNodeTypesList] = useState<NodeType[]>([]);
  const { screenToFlowPosition } = useReactFlow();

  // 初始化节点和边
  const initialNodes: Node[] = useMemo(() => {
    if (!initialSubWorkflow) {
      // 默认添加 ForEachItemNode
      return [{
        id: 'foreach_item',
        type: 'simple',
        position: { x: 100, y: 200 },
        data: {
          type: 'ForEachItemNode',
          label: 'ForEach Item',
          inputPorts: [] as string[],
          outputPorts: ['item', 'index'] as string[],
        },
      }];
    }
    
    return initialSubWorkflow.nodes.map((node, index) => ({
      id: node.id,
      type: 'simple',
      position: { x: 100 + index * 300, y: 200 },
      data: {
        type: node.type,
        label: node.type,
        inputPorts: [] as string[],
        outputPorts: [] as string[],
      },
    }));
  }, [initialSubWorkflow]);

  const initialEdges = useMemo(() => {
    if (!initialSubWorkflow) return [];
    
    return initialSubWorkflow.connections.map((conn, i) => ({
      id: `e${i}`,
      source: conn.from_node,
      sourceHandle: conn.from_port,
      target: conn.to_node,
      targetHandle: conn.to_port,
      style: { stroke: '#6366f1', strokeWidth: 2 },
    }));
  }, [initialSubWorkflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // 加载节点类型
  useEffect(() => {
    nodesCache.getNodeTypes().then((response) => {
      setNodeTypesList(response.nodes);
      
      // 更新节点的端口信息
      setNodes((nds) =>
        nds.map((node) => {
          const nodeType = response.nodes.find((t: NodeType) => t.name === node.data.type);
          if (nodeType) {
            return {
              ...node,
              data: {
                ...node.data,
                inputPorts: Object.keys(nodeType.input_ports) as string[],
                outputPorts: Object.keys(nodeType.output_ports) as string[],
              },
            };
          }
          return node;
        })
      );
    });
  }, [setNodes]);

  // 更新结果节点标记
  const nodesWithResultMark = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        isResultNode: node.id === resultNodeId,
      },
    }));
  }, [nodes, resultNodeId]);

  const onConnect = useCallback(
    (params: ReactFlowConnection) => {
      setEdges((eds) => addEdge({ ...params, style: { stroke: '#6366f1', strokeWidth: 2 } }, eds));
    },
    [setEdges]
  );

  // 验证子工作流
  const validateWorkflow = async () => {
    if (!resultNodeId || !resultPortName) {
      setValidation({
        valid: false,
        errors: ['请选择结果节点和输出端口'],
        warnings: [],
      });
      return false;
    }

    try {
      const subWorkflow = {
        nodes: nodes.map((node) => ({
          type: node.data.type,
          id: node.id,
          input_values: {},
        })),
        connections: edges.map((edge) => ({
          from_node: edge.source,
          from_port: edge.sourceHandle || '',
          to_node: edge.target,
          to_port: edge.targetHandle || '',
        })),
      };

      const result = await api.validateSubWorkflow({
        ...subWorkflow,
        result_node_id: resultNodeId,
        result_port_name: resultPortName,
      });

      setValidation(result);
      return result.valid;
    } catch (error: any) {
      setValidation({
        valid: false,
        errors: [error.message || '验证失败'],
        warnings: [],
      });
      return false;
    }
  };

  // 保存并返回
  const handleSave = async () => {
    const isValid = await validateWorkflow();
    if (isValid) {
      const subWorkflow = {
        nodes: nodes.map((node) => ({
          type: node.data.type,
          id: node.id,
          input_values: {},
        })),
        connections: edges.map((edge) => ({
          from_node: edge.source,
          from_port: edge.sourceHandle || '',
          to_node: edge.target,
          to_port: edge.targetHandle || '',
        })),
      };
      onSave(subWorkflow, resultNodeId, resultPortName);
    }
  };

  // 添加节点 - 从节点类型名称
  const handleAddNode = useCallback((nodeTypeName: string) => {
    const nodeType = nodeTypesList.find(t => t.name === nodeTypeName);
    if (!nodeType) {
      console.error('Node type not found:', nodeTypeName);
      return;
    }
    
    // 计算屏幕中心位置对应的画布坐标
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    const flowPosition = screenToFlowPosition({ x: centerX, y: centerY });
    
    const newId = `node_${Date.now()}`;
    const newNode: Node = {
      id: newId,
      type: 'simple',
      position: { 
        x: flowPosition.x - 100,
        y: flowPosition.y - 50
      },
      data: {
        type: nodeType.name,
        label: nodeType.name,
        inputPorts: Object.keys(nodeType.input_ports) as string[],
        outputPorts: Object.keys(nodeType.output_ports) as string[],
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodeTypesList, screenToFlowPosition, setNodes]);

  // 暴露 API 给全局，让主界面的侧边栏可以调用
  useEffect(() => {
    // 保存原有的 API（主工作流的）
    const originalAPI = window.workflowEditorAPI;
    
    // 只覆盖 addNode 方法，其他方法保持不变
    if (originalAPI) {
      window.workflowEditorAPI = {
        ...originalAPI,
        addNode: handleAddNode,
      };
    }
    
    console.log('🎨 SubWorkflowEditor API registered');
    
    // 清理：恢复原有的 API
    return () => {
      if (originalAPI) {
        window.workflowEditorAPI = originalAPI;
      }
      console.log('🎨 SubWorkflowEditor API unregistered');
    };
  }, [handleAddNode]);

  // 获取可选的结果节点（排除 ForEachItemNode）
  const selectableNodes = nodes.filter((node) => node.data.type !== 'ForEachItemNode');

  // 获取结果节点的输出端口
  const resultNodePorts = useMemo(() => {
    const node = nodes.find((n) => n.id === resultNodeId);
    return node?.data.outputPorts || [];
  }, [nodes, resultNodeId]);

  return (
    <div className="h-full w-full flex flex-col bg-gray-900">
        {/* 工具栏 */}
        <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-bold text-white">子工作流编辑器</h3>
          </div>

          <div className="flex items-center gap-4">
          {/* 结果节点选择 */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-300">结果节点:</label>
            <select
              value={resultNodeId}
              onChange={(e) => {
                setResultNodeId(e.target.value);
                setResultPortName('');
              }}
              className="px-2 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
            >
              <option value="">选择...</option>
              {selectableNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.id}
                </option>
              ))}
            </select>
          </div>

          {resultNodeId && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-300">输出端口:</label>
              <select
                value={resultPortName}
                onChange={(e) => setResultPortName(e.target.value)}
                className="px-2 py-1 bg-gray-700 text-white rounded text-sm border border-gray-600"
              >
                <option value="">选择...</option>
                {resultNodePorts.map((port: string) => (
                  <option key={port} value={port}>
                    {port}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={validateWorkflow}
            className="px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
          >
            验证
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-1.5 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={!resultNodeId || !resultPortName}
            className="px-3 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            保存并返回
          </button>
        </div>
      </div>

        {/* 验证结果 */}
        {validation && (
          <div
            className={`px-4 py-2 ${
              validation.valid ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'
            }`}
          >
            {validation.valid ? (
              <span>✓ 子工作流配置有效</span>
            ) : (
              <div>
                {validation.errors.map((error, i) => (
                  <div key={i}>✗ {error}</div>
                ))}
              </div>
            )}
            {validation.warnings.length > 0 && (
              <div className="mt-1 text-yellow-300">
                {validation.warnings.map((warning, i) => (
                  <div key={i}>⚠ {warning}</div>
                ))}
              </div>
            )}
          </div>
        )}

      {/* React Flow 画布 */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodesWithResultMark}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          fitView
        >
          <Background color="#4b5563" gap={16} />
          <Controls className="!bg-gray-800 !border-gray-700 [&>button]:!bg-gray-900 [&>button]:!text-gray-400 [&>button]:!border-gray-700" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default function SubWorkflowEditor(props: SubWorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <SubWorkflowEditorContent {...props} />
    </ReactFlowProvider>
  );
}
