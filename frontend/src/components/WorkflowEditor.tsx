import { useCallback, useState, useMemo, useEffect, useRef } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  ConnectionMode,
  Controls,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
  ReactFlowProvider,
  useReactFlow,
  useUpdateNodeInternals,
} from 'reactflow';
import type { 
  Edge, 
  Node, 
  Connection as ReactFlowConnection,
  NodeProps,
  OnNodesDelete,
} from 'reactflow';
import type { WorkflowData, NodeType } from '../services/api';
import { api } from '../services/api';
import { nodesCache } from '../services/nodesCache';
import NodePropertiesDialog from './NodePropertiesDialog';
import SaveAsDialog from './SaveAsDialog';
import SubWorkflowEditor from './SubWorkflowEditor';
import type { WorkflowTab } from './WorkflowTabs';

interface Connection {
  from_node: string;
  from_port: string;
  to_node: string;
  to_port: string;
}

interface WorkflowEditorProps {
  tabId: string;
  initialWorkflowData: WorkflowData | null;
  workflowName: string;
  onExecuteWorkflow: (workflowName: string, workflow: WorkflowData) => void;
  workflowTabsAPI: {
    updateCurrentTab: (updates: Partial<WorkflowTab>) => void;
    loadWorkflowToCurrentTab: (name: string, workflowData: WorkflowData) => void;
    importWorkflowToNewTab: (name: string, workflowData: WorkflowData) => void;
    getCurrentTab: () => WorkflowTab | undefined;
    createNewTab: () => void;
  };
}

// 自定义节点组件
interface CustomNodeProps extends NodeProps {
  setSelectedNode?: (node: Node | null) => void;
  setNodes?: (updater: (nodes: Node[]) => Node[]) => void;
  updateEdgesAfterNodeIdChange?: (oldId: string, newId: string) => void;
}

const CustomNode = ({ data, id, setSelectedNode, setNodes, updateEdgesAfterNodeIdChange }: CustomNodeProps) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(id);
  const [nodeTypeInfo, setNodeTypeInfo] = useState<NodeType | null>(null);
  const updateNodeInternals = useUpdateNodeInternals();
  
  // 检查是否是 ForEachNode
  const isForEachNode = data.type === 'ForEachNode';
  
  // 加载节点类型信息
  useEffect(() => {
    const loadNodeTypeInfo = async () => {
      try {
        const nodeTypes = await nodesCache.getNodeTypes();
        const nodeType = nodeTypes.nodes.find(t => t.name === data.type);
        setNodeTypeInfo(nodeType || null);
        // 节点类型信息加载完成后，更新节点内部结构
        updateNodeInternals(id);
      } catch (error) {
        console.error('Failed to get node types:', error);
        setNodeTypeInfo(null);
      }
    };

    loadNodeTypeInfo();
  }, [data.type, id, updateNodeInternals]);
  
  // 处理双击节点
  const handleNodeDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const node = { id, data, position: { x: 0, y: 0 }, type: 'default' };
    setSelectedNode?.(node);
  };

  // 处理双击节点ID
  const handleIdDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
    setEditValue(id);
  };

  // 处理编辑完成
  const handleEditComplete = () => {
    if (editValue.trim() && editValue !== id && setNodes) {
      const newId = editValue.trim();
      setNodes(nodes => nodes.map(node => {
        if (node.id === id) {
          return {
            ...node,
            id: newId,
            data: {
              ...node.data,
              label: `${newId} (${node.data.type})`
            }
          };
        }
        return node;
      }));
      // 更新相关连接的节点ID
      updateEdgesAfterNodeIdChange?.(id, newId);
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
  
  // 显示所有输入端口
  const ports = useMemo(() => {
    const inputPorts: string[] = [];
    const outputPorts: string[] = [];

    // 从节点类型定义中获取输入输出端口
    if (nodeTypeInfo) {
      // 从节点类型定义中获取输入端口
      Object.keys(nodeTypeInfo.input_ports).forEach(key => {
        if (!inputPorts.includes(key)) {
          inputPorts.push(key);
        }
      });
      
      // 从节点类型定义中获取输出端口
      Object.keys(nodeTypeInfo.output_ports).forEach(key => {
        if (!outputPorts.includes(key)) {
          outputPorts.push(key);
        }
      });
    }

    // 从现有的输入中添加端口
    if (data.inputs && typeof data.inputs === 'object') {
      Object.keys(data.inputs).forEach(key => {
        if (!inputPorts.includes(key)) {
          inputPorts.push(key);
        }
      });
    }

    // 从连接中推断端口
    if (data.connections) {
      data.connections.forEach((conn: Connection) => {
        if (conn.to_node === id && conn.to_port && !inputPorts.includes(conn.to_port)) {
          inputPorts.push(conn.to_port);
        }
        if (conn.from_node === id && conn.from_port && !outputPorts.includes(conn.from_port)) {
          outputPorts.push(conn.from_port);
        }
      });
    }

    return { inputPorts, outputPorts };
  }, [nodeTypeInfo, data.inputs, data.outputs, data.connections, id]);

  // 当端口发生变化时，更新节点内部结构
  useEffect(() => {
    updateNodeInternals(id);
  }, [ports.inputPorts, ports.outputPorts, id, updateNodeInternals]);

  // 格式化值的显示
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
          isForEachNode
            ? 'bg-purple-800/50 ring-2 ring-purple-500'
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
        onDoubleClick={handleNodeDoubleClick}
      >
      <div className="font-bold text-sm mb-2 flex items-center justify-between">
        {isEditing ? (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleEditComplete}
            onKeyDown={handleKeyDown}
            className="border border-blue-500 rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
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
        <div className="flex items-center gap-2 relative">
          <span className="text-xs text-gray-400">{data.type}</span>
          <button 
            className="cursor-pointer text-gray-400 hover:text-gray-200 px-1"
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
          >
            ⋮
          </button>
          {showMenu && (
            <div 
              className="absolute right-0 top-full mt-1 bg-gray-800 rounded-lg shadow-lg py-1 z-50 min-w-[100px] border border-gray-700"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                className="w-full px-3 py-1.5 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  const node = { id, data, position: { x: 0, y: 0 }, type: 'default' };
                  setSelectedNode?.(node);
                  setShowMenu(false);
                }}
              >
                Edit
              </button>
              <button
                className="w-full px-3 py-1.5 text-left text-sm text-red-400 hover:bg-gray-700 hover:text-red-300"
                onClick={(e) => {
                  e.stopPropagation();
                  setNodes?.(nodes => nodes.filter(n => n.id !== id));
                  setShowMenu(false);
                }}
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* ForEach 特殊显示 */}
      {isForEachNode && (
        <div className="mb-2">
          {data.subWorkflow ? (
            <div className="text-xs text-green-300 bg-green-900/30 px-2 py-1 rounded">
              ✓ 已配置子工作流 ({data.subWorkflow.nodes?.length || 0} 个节点)
            </div>
          ) : (
            <div className="text-xs text-yellow-300 bg-yellow-900/30 px-2 py-1 rounded">
              ⚠ 未配置子工作流
            </div>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              console.log('🔘 ForEach button clicked!', { 
                id, 
                hasCallback: !!data.onEditSubWorkflow,
                data: data 
              });
              if (data.onEditSubWorkflow) {
                data.onEditSubWorkflow(id);
              } else {
                console.error('❌ onEditSubWorkflow callback not found!');
              }
            }}
            className="w-full mt-2 px-3 py-1.5 bg-purple-600 text-white rounded text-xs hover:bg-purple-700"
          >
            {data.subWorkflow ? '✏️ 编辑子工作流' : '➕ 配置子工作流'}
          </button>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4">
        {/* 输入端口 */}
        <div className="border-r border-gray-700 pr-3">
          <div className="text-xs font-semibold text-indigo-400 mb-2">Inputs</div>
          {ports.inputPorts.map((port) => {
            // 只显示在 inputs 中的端口
            const isConnected = data.connections?.some((conn: Connection) => 
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
          {ports.outputPorts.map((port) => {
            // 只显示在 outputs 中的端口
            const isConnected = data.connections?.some((conn: Connection) => 
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

interface ContextMenu {
  id: string;
  x: number;
  y: number;
  type: 'edge' | 'node';
}

const WorkflowEditorContent = ({ 
  initialWorkflowData, 
  workflowName, 
  onExecuteWorkflow,
  workflowTabsAPI 
}: WorkflowEditorProps) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [showSaveAsDialog, setShowSaveAsDialog] = useState(false);
  const { screenToFlowPosition } = useReactFlow();
  
  // ForEach 子工作流编辑状态
  const [editingSubWorkflow, setEditingSubWorkflow] = useState<{
    nodeId: string;
    subWorkflow?: any;
    resultNodeId?: string;
    resultPortName?: string;
  } | null>(null);

  // Load initial workflow data
  useEffect(() => {
    if (initialWorkflowData) {
      const loadInitialData = async () => {
        try {
          const flowData = await transformWorkflowToFlow(initialWorkflowData);
          setNodes(flowData.nodes);
          setEdges(flowData.edges);
        } catch (error) {
          console.error('Failed to load initial workflow data:', error);
        }
      };
      loadInitialData();
    }
  }, [initialWorkflowData, setNodes, setEdges]);

  // Mark tab as dirty when workflow changes
  useEffect(() => {
    const currentTab = workflowTabsAPI.getCurrentTab();
    if (currentTab && (nodes.length > 0 || edges.length > 0)) {
      const currentWorkflow = transformFlowToWorkflow(nodes, edges);
      const hasChanges = JSON.stringify(currentWorkflow) !== JSON.stringify(initialWorkflowData);
      
      if (hasChanges !== currentTab.isDirty) {
        workflowTabsAPI.updateCurrentTab({ isDirty: hasChanges });
      }
    }
  }, [nodes, edges, initialWorkflowData, workflowTabsAPI]);


  // 计算节点的执行顺序
  const calculateNodeOrder = (nodes: Record<string, any>, connections: Connection[]) => {
    const nodeOrder: string[] = [];
    const visited = new Set<string>();
    const inDegree: Record<string, number> = {};
    const graph: Record<string, string[]> = {};

    // 初始化入度和图
    Object.keys(nodes).forEach(nodeId => {
      inDegree[nodeId] = 0;
      graph[nodeId] = [];
    });

    // 构建图和计算入度
    connections.forEach(conn => {
      if (graph[conn.from_node]) {
        graph[conn.from_node].push(conn.to_node);
        inDegree[conn.to_node] = (inDegree[conn.to_node] || 0) + 1;
      }
    });

    // 找到所有入度为0的节点（起始节点）
    const queue = Object.keys(nodes).filter(nodeId => inDegree[nodeId] === 0);

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
    Object.keys(nodes).forEach(nodeId => {
      if (!visited.has(nodeId)) {
        nodeOrder.push(nodeId);
      }
    });

    return nodeOrder;
  };

  // 将workflow数据转换为ReactFlow格式
  const transformWorkflowToFlow = async (data: WorkflowData) => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    // 获取所有节点类型定义
    const nodeTypesResponse = await nodesCache.getNodeTypes();
    const nodeTypeDefinitions = nodeTypesResponse.nodes.reduce((acc: Record<string, NodeType>, type: NodeType) => {
      acc[type.name] = type;
      return acc;
    }, {});

    // 计算节点顺序
    const nodeOrder = calculateNodeOrder(data.nodes, data.connections);

    // 创建节点
    nodeOrder.forEach(id => {
      const node = data.nodes[id];
      const nodeType = nodeTypeDefinitions[node.type];
      const inputPorts = nodeType ? Object.keys(nodeType.input_ports) : [];
      const outputPorts = nodeType ? Object.keys(nodeType.output_ports) : [];
      
      // 根据端口定义分离输入和输出
      const inputs: Record<string, any> = {};
      const outputs: Record<string, any> = {};
      
      // 处理已有的输入
      if (node.inputs) {
        Object.entries(node.inputs).forEach(([key, value]) => {
          if (inputPorts.includes(key)) {
            inputs[key] = value;
          }
        });
      }
      
      // 从连接中推断输出端口
      data.connections.forEach(conn => {
        if (conn.from_node === id && outputPorts.includes(conn.from_port)) {
          outputs[conn.from_port] = null;
        }
      });

      // 根据节点顺序和层级计算位置
      const baseWidth = 400; // 节点的基础宽度
      const baseHeight = 200; // 节点的基础高度
      const xGap = baseWidth + 100; // 水平间距 = 节点宽度 + 100px间隙
      const yGap = baseHeight + 50; // 垂直间距 = 节点高度 + 50px间隙
      
      // 计算节点的层级（深度）
      const getNodeDepth = (nodeId: string): number => {
        const incomingConnections = data.connections.filter(conn => conn.to_node === nodeId);
        if (incomingConnections.length === 0) return 0;
        
        const parentDepths = incomingConnections.map(conn => 
          getNodeDepth(conn.from_node)
        );
        return Math.max(...parentDepths) + 1;
      };

      // 计算每个层级的节点数量
      const nodeDepth = getNodeDepth(id);
      const depthCounts = new Map<number, number>();
      nodeOrder.forEach(nid => {
        const depth = getNodeDepth(nid);
        depthCounts.set(depth, (depthCounts.get(depth) || 0) + 1);
      });

      // 计算当前节点在其层级中的位置
      const nodesAtCurrentDepth = nodeOrder
        .filter(nid => getNodeDepth(nid) === nodeDepth)
        .indexOf(id);

      // 计算节点位置，确保同层级的节点垂直分布
      const x = xGap * nodeDepth;
      const totalNodesAtDepth = depthCounts.get(nodeDepth) || 1;
      const y = (yGap * nodesAtCurrentDepth) - ((totalNodesAtDepth - 1) * yGap / 2);

      flowNodes.push({
        id,
        type: 'default',
        position: { x, y },
        data: { 
          label: `${id} (${node.type})`,
          type: node.type,
          inputs,
          outputs,
          connections: data.connections.filter(conn => conn.from_node === id || conn.to_node === id),
        },
      });
    });

    // 创建连接
    data.connections.forEach((conn, index) => {
      flowEdges.push({
        id: `edge-${index}`,
        source: conn.from_node,
        sourceHandle: conn.from_port,
        target: conn.to_node,
        targetHandle: conn.to_port,
      });
    });

    return { nodes: flowNodes, edges: flowEdges };
  };

  // 将ReactFlow格式转换回workflow数据
  const transformFlowToWorkflow = (nodes: Node[], edges: Edge[]): WorkflowData => {
    const workflowNodes: Record<string, any> = {};
    const workflowConnections: any[] = [];

    // 转换节点
    nodes.forEach((node) => {
      const { id, data } = node;
      const { label, type, inputs, outputs, connections, ...nodeData } = data;
      workflowNodes[id] = {
        type,
        inputs,
        ...nodeData,
      };
    });

    // 转换连接
    edges.forEach((edge) => {
      workflowConnections.push({
        from_node: edge.source,
        from_port: edge.sourceHandle,
        to_node: edge.target,
        to_port: edge.targetHandle,
      });
    });

    return {
      nodes: workflowNodes,
      connections: workflowConnections,
    };
  };


  // 导入workflow文件到新tab
  const importWorkflow = useCallback(async () => {
    try {
      // 创建一个隐藏的文件输入元素
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
            workflowTabsAPI.importWorkflowToNewTab(fileName, data);
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
  }, [workflowTabsAPI]);

  // 保存workflow到服务器
  const saveWorkflow = useCallback(async (name?: string) => {
    try {
      const workflowData = transformFlowToWorkflow(nodes, edges);
      const currentTab = workflowTabsAPI.getCurrentTab();
      const saveName = name || (currentTab?.isNew ? undefined : currentTab?.name);
      
      if (!saveName) {
        setShowSaveAsDialog(true);
        return;
      }
      
      await api.saveWorkflow(saveName, workflowData);
      workflowTabsAPI.updateCurrentTab({
        name: saveName,
        workflowData,
        isDirty: false,
        isNew: false,
      });
      alert('Workflow saved successfully!');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow. Please try again.');
    }
  }, [nodes, edges, workflowTabsAPI]);

  // 导出workflow到本地文件
  const exportWorkflow = useCallback(() => {
    try {
      const workflowData = transformFlowToWorkflow(nodes, edges);
      const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `${workflowName || 'workflow'}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export workflow:', error);
    }
  }, [nodes, edges, workflowName]);

  // 加载服务器端的workflow
  const loadWorkflow = useCallback(async (name: string) => {
    try {
      const data = await api.getWorkflow(name);
      workflowTabsAPI.loadWorkflowToCurrentTab(name, data);
    } catch (error) {
      console.error('Failed to load workflow:', error);
      alert('Failed to load workflow. Please try again.');
    }
  }, [workflowTabsAPI]);

  // 处理连接变化
  const onConnect = useCallback(
    (params: ReactFlowConnection) => {
      // 添加边
      setEdges((eds) => addEdge(params, eds));
      
      // 更新节点数据中的connections数组
      const newConnection: Connection = {
        from_node: params.source!,
        from_port: params.sourceHandle!,
        to_node: params.target!,
        to_port: params.targetHandle!,
      };
      
      setNodes(nodes => nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          connections: [
            ...(node.data.connections || []),
            newConnection
          ]
        }
      })));
    },
    [setEdges, setNodes]
  );

  // 处理节点ID变更后更新相关连接
  const updateEdgesAfterNodeIdChange = useCallback(
    (oldId: string, newId: string) => {
      // 更新边的连接信息
      setEdges(edges => edges.map(edge => ({
        ...edge,
        source: edge.source === oldId ? newId : edge.source,
        target: edge.target === oldId ? newId : edge.target
      })));
      
      // 更新所有节点数据中的connections数组
      setNodes(nodes => nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          connections: node.data.connections?.map((conn: Connection) => ({
            ...conn,
            from_node: conn.from_node === oldId ? newId : conn.from_node,
            to_node: conn.to_node === oldId ? newId : conn.to_node
          })) || []
        }
      })));
    },
    [setEdges, setNodes]
  );

  // Handle node deletion
  const onNodesDelete: OnNodesDelete = useCallback(
    (nodesToDelete) => {
      const nodeIds = new Set(nodesToDelete.map(node => node.id));
      
      // Remove all edges connected to deleted nodes
      setEdges(edges.filter(edge => 
        !nodeIds.has(edge.source) && !nodeIds.has(edge.target)
      ));
      
      // Remove connections from remaining nodes' data
      setNodes(nodes => nodes.map(node => {
        if (nodeIds.has(node.id)) {
          return node; // 被删除的节点不需要处理
        }
        return {
          ...node,
          data: {
            ...node.data,
            connections: (node.data.connections || []).filter((conn: Connection) => 
              !nodeIds.has(conn.from_node) && !nodeIds.has(conn.to_node)
            )
          }
        };
      }));
    },
    [edges, setEdges, setNodes]
  );

  // Handle adding new nodes
  const onNodeTypeSelect = useCallback((nodeType: NodeType) => {
    // 计算屏幕中心位置对应的画布坐标
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    
    // 将屏幕坐标转换为画布坐标
    const flowPosition = screenToFlowPosition({ x: centerX, y: centerY });
    
    const newNode: Node = {
      id: `${Date.now()}`,
      type: 'default',
      position: { 
        x: flowPosition.x - 200, // 减去节点宽度的一半，让节点居中
        y: flowPosition.y - 100  // 减去节点高度的一半，让节点居中
      },
      data: {
        type: nodeType.name,
        width: 400,
        selected: false,
        inputs: Object.fromEntries(
          Object.entries(nodeType.input_ports).map(([key, port]) => [
            key,
            port.default_value !== null ? port.default_value : undefined
          ])
        ),
        outputs: Object.fromEntries(
          Object.entries(nodeType.output_ports).map(([key, port]) => [
            key,
            port.default_value !== null ? port.default_value : undefined
          ])
        ),
        connections: [],
        // onEditSubWorkflow 将通过 useEffect 注入
      },
    };
    setNodes(nodes => [...nodes, newNode]);
  }, [setNodes, screenToFlowPosition]);

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
    // 找到要删除的边
    const edgeToDelete = edges.find(e => e.id === edgeId);
    
    // 从边列表中删除
    setEdges((eds) => eds.filter((e) => e.id !== edgeId));
    
    // 从节点数据的connections数组中删除对应的连接
    if (edgeToDelete) {
      setNodes(nodes => nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          connections: (node.data.connections || []).filter((conn: Connection) => 
            !(conn.from_node === edgeToDelete.source && 
              conn.from_port === edgeToDelete.sourceHandle &&
              conn.to_node === edgeToDelete.target && 
              conn.to_port === edgeToDelete.targetHandle)
          )
        }
      })));
    }
    
    setContextMenu(null);
    setSelectedEdge(null);
  }, [setEdges, setNodes, edges]);

  // Handle background click to close context menu
  const onPaneClick = useCallback(() => {
    setContextMenu(null);
    setSelectedEdge(null);
  }, []);

  // Handle node selection
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    event.stopPropagation();
    
    // Update selection
    setNodes(nodes => nodes.map(n => ({
      ...n,
      data: {
        ...n.data,
        selected: n.id === node.id
      }
    })));
    
    // Close edge selection
    setSelectedEdge(null);
  }, [setNodes]);

  // Handle node data update
  const onNodeUpdate = useCallback((nodeId: string, data: any) => {
    setNodes(nodes => nodes.map(node => 
      node.id === nodeId ? { ...node, data } : node
    ));
  }, [setNodes]);

  // 处理编辑子工作流
  const handleEditSubWorkflow = useCallback((nodeId: string) => {
    console.log('🎯 handleEditSubWorkflow called with nodeId:', nodeId);
    const node = nodes.find(n => n.id === nodeId);
    console.log('  Found node:', node);
    
    if (!node) {
      console.error('❌ Node not found!');
      return;
    }

    const subWorkflowData = {
      nodeId,
      subWorkflow: node.data.subWorkflow || {
        nodes: [{ type: 'ForEachItemNode', id: 'foreach_item' }],
        connections: []
      },
      resultNodeId: node.data.resultNodeId,
      resultPortName: node.data.resultPortName,
    };
    
    console.log('  Setting editingSubWorkflow:', subWorkflowData);
    setEditingSubWorkflow(subWorkflowData);
  }, [nodes]);

  // 保存子工作流
  const handleSaveSubWorkflow = useCallback((
    subWorkflow: any,
    resultNodeId: string,
    resultPortName: string
  ) => {
    if (!editingSubWorkflow) return;

    // 更新节点数据
    setNodes(nodes => nodes.map(node => 
      node.id === editingSubWorkflow.nodeId
        ? {
            ...node,
            data: {
              ...node.data,
              subWorkflow,
              resultNodeId,
              resultPortName,
              // 更新 inputs，以便保存到后端
              inputs: {
                ...node.data.inputs,
                sub_workflow: subWorkflow,
                result_node_id: resultNodeId,
                result_port_name: resultPortName,
              }
            }
          }
        : node
    ));

    setEditingSubWorkflow(null);
  }, [editingSubWorkflow, setNodes]);

  // 注入 onEditSubWorkflow 回调到所有节点
  const handleEditSubWorkflowRef = useRef(handleEditSubWorkflow);
  handleEditSubWorkflowRef.current = handleEditSubWorkflow;
  
  useEffect(() => {
    console.log('🔄 Injecting onEditSubWorkflow to nodes... (nodes count:', nodes.length, ')');
    
    // 检查是否有 ForEachNode 需要注入回调
    const forEachNodes = nodes.filter(n => n.data.type === 'ForEachNode');
    console.log('  Found ForEachNode count:', forEachNodes.length);
    
    if (forEachNodes.length === 0) {
      console.log('  ⏭️ No ForEachNode found, skipping injection');
      return;
    }
    
    setNodes((currentNodes) => {
      let updated = false;
      const updatedNodes = currentNodes.map((node) => {
        // 只处理 ForEachNode
        if (node.data.type !== 'ForEachNode') {
          return node;
        }
        
        // 检查是否需要更新
        const hasCallback = !!node.data.onEditSubWorkflow;
        const hasSubWorkflowInInputs = !!node.data.inputs?.sub_workflow;
        const hasSubWorkflowInData = !!node.data.subWorkflow;
        
        console.log(`  📦 ForEachNode "${node.id}":`, {
          hasCallback,
          hasSubWorkflowInInputs,
          hasSubWorkflowInData,
          willUpdate: !hasCallback || (hasSubWorkflowInInputs && !hasSubWorkflowInData)
        });
        
        // 如果已经有回调且数据已同步，跳过
        if (hasCallback && (!hasSubWorkflowInInputs || hasSubWorkflowInData)) {
          return node;
        }
        
        updated = true;
        return {
          ...node,
          data: {
            ...node.data,
            onEditSubWorkflow: (nodeId: string) => {
              console.log('📞 onEditSubWorkflow called for:', nodeId);
              handleEditSubWorkflowRef.current(nodeId);
            },
            // 如果节点有 sub_workflow 输入，也设置到 data 中
            subWorkflow: node.data.inputs?.sub_workflow || node.data.subWorkflow,
            resultNodeId: node.data.inputs?.result_node_id || node.data.resultNodeId,
            resultPortName: node.data.inputs?.result_port_name || node.data.resultPortName,
          },
        };
      });
      
      if (updated) {
        console.log('✅ Injection complete - nodes updated');
        return updatedNodes;
      } else {
        console.log('✅ All ForEachNodes already have callbacks');
        return currentNodes;
      }
    });
  }, [nodes.length, setNodes]); // 依赖节点数量，避免循环

  const nodeTypes = useMemo(() => ({
    default: (props: NodeProps) => (
      <CustomNode
        {...props}
        setSelectedNode={setSelectedNode}
        setNodes={setNodes}
        updateEdgesAfterNodeIdChange={updateEdgesAfterNodeIdChange}
      />
    ),
  }), []); // 空依赖 - 这些 props 应该是稳定的

  // 缓存 workflow 对象以避免重复执行
  const workflow = useMemo(() => transformFlowToWorkflow(nodes, edges), [nodes, edges]);

  // Add keyboard shortcuts for menu actions
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'o':
            e.preventDefault();
            importWorkflow();
            break;
          case 's':
            e.preventDefault();
            if (e.shiftKey) {
              setShowSaveAsDialog(true);
            } else {
              saveWorkflow();
            }
            break;
          case 'e':
            e.preventDefault();
            exportWorkflow();
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [importWorkflow, saveWorkflow, exportWorkflow]);

  // 自定义连线样式
  const edgeStyles = {
    stroke: '#6366f1', // Indigo-500
    strokeWidth: 2,
    animated: true,
  };



  // 暴露给全局的API
  const editorAPI = {
    addNode: (nodeType: string) => {
      nodesCache.getNodeTypes().then(nodeTypes => {
        const selectedType = nodeTypes.nodes.find((t: NodeType) => t.name === nodeType);
        if (selectedType) {
          onNodeTypeSelect(selectedType);
        }
      });
    },
    loadWorkflow,
    saveWorkflow: () => saveWorkflow(),
    saveAsWorkflow: () => setShowSaveAsDialog(true),
    exportWorkflow,
    getCurrentWorkflow: () => workflow,
  };

  // 将API暴露给全局
  useEffect(() => {
    window.workflowEditorAPI = editorAPI;
    return () => {
      delete window.workflowEditorAPI;
    };
  }, [editorAPI]);

  // 如果正在编辑子工作流，显示子工作流编辑器
  if (editingSubWorkflow) {
    console.log('🎨 Rendering SubWorkflowEditor with:', editingSubWorkflow);
    return (
      <SubWorkflowEditor
        initialSubWorkflow={editingSubWorkflow.subWorkflow}
        initialResultNodeId={editingSubWorkflow.resultNodeId}
        initialResultPortName={editingSubWorkflow.resultPortName}
        onSave={handleSaveSubWorkflow}
        onCancel={() => setEditingSubWorkflow(null)}
      />
    );
  }

  return (
    <div className="h-full w-full flex flex-col bg-gray-900 text-gray-100">
      {/* Main Content */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges.map(edge => ({
            ...edge,
            ...edgeStyles,
            className: edge.id === selectedEdge ? 'selected-edge' : '',
            animated: edge.id === selectedEdge,
            style: {
              ...edgeStyles,
              stroke: edge.id === selectedEdge ? '#818cf8' : '#6366f1', // Lighter color when selected
            }
          }))}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodesDelete={onNodesDelete}
          onNodeClick={onNodeClick}
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
          <Controls 
            className="!bg-gray-800 !border-gray-700 [&>button]:!bg-gray-900 [&>button]:!text-gray-400 [&>button]:!border-gray-700 
              [&>button:hover]:!bg-gray-700 [&>button:hover]:!text-gray-200"
          />
        </ReactFlow>
      </div>

      {/* Dialogs and Overlays */}
      {selectedNode && (
        <NodePropertiesDialog
          isOpen={true}
          onClose={() => setSelectedNode(null)}
          node={selectedNode}
          onUpdate={onNodeUpdate}
        />
      )}

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-gray-800 rounded-lg shadow-lg py-2 z-50 border border-gray-700"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
        >
          {contextMenu.type === 'edge' ? (
            <button
              className="w-full px-4 py-2 text-left text-red-400 hover:bg-gray-700 hover:text-red-300"
              onClick={() => onEdgeDelete(contextMenu.id)}
            >
              Delete Connection
            </button>
          ) : (
            <>
              <button
                className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white"
                onClick={() => {
                  const node = nodes.find(n => n.id === contextMenu.id);
                  if (node) setSelectedNode(node);
                  setContextMenu(null);
                }}
              >
                Edit Node
              </button>
              <button
                className="w-full px-4 py-2 text-left text-red-400 hover:bg-gray-700 hover:text-red-300"
                onClick={() => {
                  setNodes(nodes => nodes.filter(n => n.id !== contextMenu.id));
                  setContextMenu(null);
                }}
              >
                Delete Node
              </button>
            </>
          )}
        </div>
      )}

      {/* Save As Dialog */}
      <SaveAsDialog
        isOpen={showSaveAsDialog}
        onClose={() => setShowSaveAsDialog(false)}
        onSave={(name) => saveWorkflow(name)}
        currentName={workflowName}
      />
    </div>
  );
};

function WorkflowEditor(props: WorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <WorkflowEditorContent {...props} />
    </ReactFlowProvider>
  );
}

export default WorkflowEditor;