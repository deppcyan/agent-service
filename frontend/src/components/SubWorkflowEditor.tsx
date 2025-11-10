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
import type { Node, Connection as ReactFlowConnection, Edge } from 'reactflow';
import { api, type Connection } from '../services/api';
import { nodesCache } from '../services/nodesCache';
import type { NodeType } from '../services/api';
import NodePropertiesDialog from './NodePropertiesDialog';

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

// 简单节点组件（用于子工作流）- 与主编辑器保持一致的样式
const SimpleNode = ({ data, id }: { data: any; id: string }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(id);
  const isForEachItemNode = data.type === 'ForEachItemNode';
  
  // 处理双击节点ID
  const handleIdDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
    setEditValue(id);
  };

  // 处理编辑完成
  const handleEditComplete = () => {
    if (editValue.trim() && editValue !== id && data.onNodeIdChange) {
      data.onNodeIdChange(id, editValue.trim());
    }
    setIsEditing(false);
  };

  // 处理按键事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleEditComplete();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditValue(id);
    }
  };
  
  // 格式化值的显示（与主编辑器一致）
  const formatValue = (value: any): string => {
    if (value === undefined || value === null) {
      return '(empty)';
    }
    if (typeof value === 'string') {
      return value.length > 30 ? value.substring(0, 30) + '...' : value;
    }
    if (Array.isArray(value)) {
      if (value.length === 0) return '[]';
      if (value.length === 1) return `[${formatValue(value[0])}]`;
      return `[${value.length} items]`;
    }
    if (typeof value === 'object') {
      const keys = Object.keys(value);
      if (keys.length === 0) return '{}';
      return `{${keys.length} keys}`;
    }
    return String(value);
  };

  return (
    <div 
      className="p-2 rounded-lg transition-all duration-200 ring-1 ring-white/30 resize-node"
      style={{
        minWidth: data.width || 400,
        width: data.width || 400,
        height: 'auto',
        position: 'relative'
      }}
    >
      <div 
        className={`px-4 py-3 rounded-md transition-all duration-200 ${
          isForEachItemNode
            ? 'bg-green-800/50 ring-2 ring-green-500'
            : data.isResultNode 
            ? 'bg-indigo-800/50 ring-2 ring-indigo-400' 
            : 'bg-gray-800'
        } ${
          data.selected 
            ? 'ring-2 ring-indigo-500 shadow-lg' 
            : 'ring-1 ring-gray-700'
        } cursor-pointer hover:ring-2 hover:ring-indigo-400`}
        style={{
          width: '100%',
          height: '100%'
        }}
      >
        <div className="font-bold text-sm mb-2 flex items-center justify-between">
          {isEditing ? (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleEditComplete}
              onKeyDown={handleKeyDown}
              className="border border-blue-500 rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 bg-gray-700 text-white"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span 
              onDoubleClick={handleIdDoubleClick} 
              className="cursor-text text-gray-200 hover:text-indigo-300"
            >
              {id}
            </span>
          )}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{data.type}</span>
          </div>
        </div>
        
        {/* 特殊标识 */}
        {isForEachItemNode && (
          <div className="mb-2">
            <div className="text-xs text-green-300 bg-green-900/30 px-2 py-1 rounded">
              ⭐ 循环入口节点
            </div>
          </div>
        )}
        
        {data.isResultNode && (
          <div className="mb-2">
            <div className="text-xs text-indigo-300 bg-indigo-900/30 px-2 py-1 rounded">
              🎯 结果输出节点
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-4">
          {/* 输入端口 */}
          <div className="border-r border-gray-700 pr-3">
            <div className="text-xs font-semibold text-indigo-400 mb-2">Inputs</div>
            {data.inputPorts?.map((port: string) => {
              // 检查是否连接
              const isConnected = data.connections?.some((conn: any) => 
                conn.to_node === id && conn.to_port === port
              );
              return (
                <div key={`${id}-input-${port}`} className="relative mb-2 last:mb-0">
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={port}
                    isConnectable={true}
                    className={`w-2 h-2 ${isConnected ? '!bg-green-500' : '!bg-blue-500'}`}
                    style={{ top: '10px' }}
                  />
                  <div className="ml-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-300">{port}:</span>
                      <span 
                        className="text-xs text-gray-400 truncate max-w-[120px]" 
                        title={JSON.stringify(data.inputs?.[port], null, 2)}
                      >
                        {formatValue(data.inputs?.[port])}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 输出端口 */}
          <div className="pl-3">
            <div className="text-xs font-semibold text-indigo-400 mb-2">Outputs</div>
            {data.outputPorts?.map((port: string) => {
              // 检查是否连接
              const isConnected = data.connections?.some((conn: any) => 
                conn.from_node === id && conn.from_port === port
              );
              return (
                <div key={`${id}-output-${port}`} className="relative mb-2 last:mb-0">
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={port}
                    isConnectable={true}
                    className={`w-2 h-2 ${isConnected ? '!bg-green-500' : '!bg-blue-500'}`}
                    style={{ top: '10px' }}
                  />
                  <div className="mr-3">
                    <div className="flex items-center justify-end">
                      <span className="text-xs font-medium text-gray-300">{port}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// 简单的静态 nodeTypes
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
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ id: string; x: number; y: number; type: 'edge' } | null>(null);
  const { screenToFlowPosition } = useReactFlow();

  // 计算节点的执行顺序（与主编辑器一致）
  const calculateNodeOrder = (nodes: Array<{ type: string; id: string; input_values?: Record<string, any> }>, connections: Connection[]) => {
    const nodeOrder: string[] = [];
    const visited = new Set<string>();
    const inDegree: Record<string, number> = {};
    const graph: Record<string, string[]> = {};

    // 初始化入度和图
    nodes.forEach(node => {
      inDegree[node.id] = 0;
      graph[node.id] = [];
    });

    // 构建图和计算入度
    connections.forEach(conn => {
      if (graph[conn.from_node]) {
        graph[conn.from_node].push(conn.to_node);
        inDegree[conn.to_node] = (inDegree[conn.to_node] || 0) + 1;
      }
    });

    // 找到所有入度为0的节点（起始节点）
    const queue = nodes.map(n => n.id).filter(nodeId => inDegree[nodeId] === 0);

    // 拓扑排序
    while (queue.length > 0) {
      const currentNode = queue.shift()!;
      if (!visited.has(currentNode)) {
        visited.add(currentNode);
        nodeOrder.push(currentNode);

        // 处理所有相邻节点
        graph[currentNode].forEach(neighbor => {
          inDegree[neighbor]--;
          if (inDegree[neighbor] === 0) {
            queue.push(neighbor);
          }
        });
      }
    }

    // 添加任何剩余的节点（可能存在环）
    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        nodeOrder.push(node.id);
      }
    });

    return nodeOrder;
  };

  // 计算智能节点布局位置
  const calculateNodePositions = (nodes: Array<{ type: string; id: string; input_values?: Record<string, any> }>, connections: Connection[]) => {
    if (nodes.length === 0) return {};

    const nodeOrder = calculateNodeOrder(nodes, connections);
    const positions: Record<string, { x: number; y: number }> = {};

    // 布局参数（与主编辑器一致）
    const baseWidth = 400; // 节点的基础宽度
    const baseHeight = 200; // 节点的基础高度
    const xGap = baseWidth + 100; // 水平间距 = 节点宽度 + 100px间隙
    const yGap = baseHeight + 50; // 垂直间距 = 节点高度 + 50px间隙

    // 计算节点的层级（深度）
    const getNodeDepth = (nodeId: string): number => {
      const incomingConnections = connections.filter(conn => conn.to_node === nodeId);
      if (incomingConnections.length === 0) return 0;
      
      const parentDepths = incomingConnections.map(conn => 
        getNodeDepth(conn.from_node)
      );
      return Math.max(...parentDepths) + 1;
    };

    // 计算每个层级的节点数量
    const depthCounts = new Map<number, number>();
    nodeOrder.forEach(nodeId => {
      const depth = getNodeDepth(nodeId);
      depthCounts.set(depth, (depthCounts.get(depth) || 0) + 1);
    });

    // 为每个节点计算位置
    nodeOrder.forEach(nodeId => {
      const nodeDepth = getNodeDepth(nodeId);
      
      // 计算当前节点在其层级中的位置
      const nodesAtCurrentDepth = nodeOrder
        .filter(nid => getNodeDepth(nid) === nodeDepth)
        .indexOf(nodeId);

      // 计算节点位置，确保同层级的节点垂直分布
      const x = xGap * nodeDepth;
      const totalNodesAtDepth = depthCounts.get(nodeDepth) || 1;
      const y = (yGap * nodesAtCurrentDepth) - ((totalNodesAtDepth - 1) * yGap / 2);

      positions[nodeId] = { x, y };
    });

    return positions;
  };

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
          inputs: {},
        },
      }];
    }
    
    // 计算智能布局位置
    const positions = calculateNodePositions(initialSubWorkflow.nodes, initialSubWorkflow.connections);
    
    return initialSubWorkflow.nodes.map((node) => ({
      id: node.id,
      type: 'simple',
      position: positions[node.id] || { x: 100, y: 200 },
      data: {
        type: node.type,
        label: node.type,
        inputPorts: [] as string[],
        outputPorts: [] as string[],
        inputs: node.input_values || {},
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
                // 确保 inputs 存在，如果不存在则初始化为默认值
                inputs: node.data.inputs || Object.fromEntries(
                  Object.entries(nodeType.input_ports).map(([key, port]) => [
                    key,
                    port.default_value !== null ? port.default_value : undefined
                  ])
                ),
              },
            };
          }
          return node;
        })
      );
    });
  }, [setNodes]);

  // 处理节点双击
  const handleNodeDoubleClick = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
    }
  }, [nodes]);

  // 处理节点数据更新
  const handleNodeUpdate = useCallback((nodeId: string, newData: any) => {
    console.log('🔄 SubWorkflow handleNodeUpdate:', { nodeId, newData });
    setNodes(nodes => nodes.map(node => 
      node.id === nodeId ? { ...node, data: { ...node.data, ...newData } } : node
    ));
  }, [setNodes]);

  // 处理节点ID更改
  const handleNodeIdChange = useCallback((oldId: string, newId: string) => {
    // 更新节点ID
    setNodes(nodes => nodes.map(node => 
      node.id === oldId ? { ...node, id: newId } : node
    ));
    
    // 更新边的连接
    setEdges(edges => edges.map(edge => ({
      ...edge,
      source: edge.source === oldId ? newId : edge.source,
      target: edge.target === oldId ? newId : edge.target
    })));
    
    // 如果结果节点ID被更改，也要更新
    if (resultNodeId === oldId) {
      setResultNodeId(newId);
    }
  }, [setNodes, setEdges, resultNodeId]);

  // 更新结果节点标记和连接信息
  const nodesWithResultMark = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        isResultNode: node.id === resultNodeId,
        onNodeIdChange: handleNodeIdChange,
        connections: edges.filter(edge => 
          edge.source === node.id || edge.target === node.id
        ).map(edge => ({
          from_node: edge.source,
          from_port: edge.sourceHandle || '',
          to_node: edge.target,
          to_port: edge.targetHandle || '',
        })),
      },
    }));
  }, [nodes, resultNodeId, edges, handleNodeIdChange]);

  const onConnect = useCallback(
    (params: ReactFlowConnection) => {
      setEdges((eds) => addEdge({ ...params, style: { stroke: '#6366f1', strokeWidth: 2 } }, eds));
    },
    [setEdges]
  );

  // Handle edge click
  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedEdge(edge.id);
    setContextMenu({
      id: edge.id,
      x: event.clientX,
      y: event.clientY,
      type: 'edge'
    });
  }, []);

  // Handle edge mouse enter
  const onEdgeMouseEnter = useCallback((_: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge.id);
  }, []);

  // Handle edge mouse leave
  const onEdgeMouseLeave = useCallback(() => {
    if (!contextMenu) {
      setSelectedEdge(null);
    }
  }, [contextMenu]);

  // Handle edge deletion
  const onEdgeDelete = useCallback((edgeId: string) => {
    setEdges((eds) => eds.filter((e) => e.id !== edgeId));
    setContextMenu(null);
    setSelectedEdge(null);
  }, [setEdges]);

  // Handle background click to close context menu
  const onPaneClick = useCallback(() => {
    setContextMenu(null);
    setSelectedEdge(null);
  }, []);

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
          input_values: node.data.inputs || {},
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
      console.log('💾 SubWorkflow saving nodes with inputs:', nodes.map(n => ({ 
        id: n.id, 
        type: n.data.type, 
        inputs: n.data.inputs 
      })));
      
      const subWorkflow = {
        nodes: nodes.map((node) => ({
          type: node.data.type,
          id: node.id,
          input_values: node.data.inputs || {},
        })),
        connections: edges.map((edge) => ({
          from_node: edge.source,
          from_port: edge.sourceHandle || '',
          to_node: edge.target,
          to_port: edge.targetHandle || '',
        })),
      };
      
      console.log('💾 Final subWorkflow to save:', subWorkflow);
      onSave(subWorkflow, resultNodeId, resultPortName);
    }
  };


  // 添加节点的回调函数
  const handleAddNode = useCallback((nodeTypeName: string) => {
    console.log('🎯 SubWorkflow addNode called with:', nodeTypeName);
    const nodeType = nodeTypesList.find(t => t.name === nodeTypeName);
    if (!nodeType) {
      console.error('Node type not found:', nodeTypeName);
      return;
    }
    
    // 计算新节点的智能位置
    setNodes((currentNodes) => {
      const calculateNewNodePosition = () => {
        // 始终将新节点放在屏幕中心
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const flowPosition = screenToFlowPosition({ x: centerX, y: centerY });
        return { x: flowPosition.x - 200, y: flowPosition.y - 100 };
      };

      const position = calculateNewNodePosition();
      const newId = `node_${Date.now()}`;
      const newNode: Node = {
        id: newId,
        type: 'simple',
        position,
        data: {
          type: nodeType.name,
          label: nodeType.name,
          inputPorts: Object.keys(nodeType.input_ports) as string[],
          outputPorts: Object.keys(nodeType.output_ports) as string[],
          inputs: Object.fromEntries(
            Object.entries(nodeType.input_ports).map(([key, port]) => [
              key,
              port.default_value !== null ? port.default_value : undefined
            ])
          ),
        },
      };
      return [...currentNodes, newNode];
    });
  }, [nodeTypesList, screenToFlowPosition, setNodes]);

  // 暴露 API 给全局，让主界面的侧边栏可以调用
  useEffect(() => {
    console.log('🎨 SubWorkflowEditor mounting, registering API...');
    
    // 保存原有的 API（主工作流的）
    const originalAPI = window.workflowEditorAPI;
    
    // 创建子工作流的 API
    const subWorkflowAPI = {
      addNode: handleAddNode,
      loadWorkflow: () => {
        console.warn('loadWorkflow not available in SubWorkflowEditor');
      },
      // 保留原始 API 的其他方法（如果存在）
      ...(originalAPI ? {
        saveWorkflow: originalAPI.saveWorkflow,
        saveAsWorkflow: originalAPI.saveAsWorkflow,
        exportWorkflow: originalAPI.exportWorkflow,
        getCurrentWorkflow: originalAPI.getCurrentWorkflow,
      } : {}),
    };
    
    // 立即注册子工作流 API
    window.workflowEditorAPI = subWorkflowAPI;
    console.log('🎨 SubWorkflowEditor API registered with addNode override');
    
    // 清理：恢复原有的 API
    return () => {
      console.log('🎨 SubWorkflowEditor unmounting, restoring original API...');
      if (originalAPI) {
        window.workflowEditorAPI = originalAPI;
        console.log('🎨 SubWorkflowEditor API unregistered, restored original');
      } else {
        delete window.workflowEditorAPI;
        console.log('🎨 SubWorkflowEditor API unregistered, deleted global API');
      }
    };
  }, [handleAddNode]); // 只依赖 handleAddNode

  // 获取可选的结果节点（排除 ForEachItemNode）
  const selectableNodes = nodes.filter((node) => node.data.type !== 'ForEachItemNode');

  // 获取结果节点的输出端口
  const resultNodePorts = useMemo(() => {
    const node = nodes.find((n) => n.id === resultNodeId);
    return node?.data.outputPorts || [];
  }, [nodes, resultNodeId]);

  // nodeTypes 现在是静态的，不需要重新创建

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
          edges={edges.map(edge => ({
            ...edge,
            style: {
              stroke: edge.id === selectedEdge ? '#818cf8' : '#6366f1',
              strokeWidth: 2,
            },
            className: edge.id === selectedEdge ? 'selected-edge' : '',
            animated: edge.id === selectedEdge,
          }))}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDoubleClick={(_, node) => handleNodeDoubleClick(node.id)}
          onEdgeClick={onEdgeClick}
          onEdgeMouseEnter={onEdgeMouseEnter}
          onEdgeMouseLeave={onEdgeMouseLeave}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          minZoom={0.1}
          maxZoom={4}
          fitView
        >
          <Background color="#4b5563" gap={16} />
          <Controls className="!bg-gray-800 !border-gray-700 [&>button]:!bg-gray-900 [&>button]:!text-gray-400 [&>button]:!border-gray-700" />
        </ReactFlow>
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-gray-800 rounded-lg shadow-lg py-2 z-50 border border-gray-700"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
        >
          <button
            className="w-full px-4 py-2 text-left text-red-400 hover:bg-gray-700 hover:text-red-300"
            onClick={() => onEdgeDelete(contextMenu.id)}
          >
            Delete Connection
          </button>
        </div>
      )}

      {/* 节点属性对话框 */}
      {selectedNode && (
        <NodePropertiesDialog
          isOpen={true}
          onClose={() => setSelectedNode(null)}
          node={selectedNode}
          onUpdate={handleNodeUpdate}
        />
      )}
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
