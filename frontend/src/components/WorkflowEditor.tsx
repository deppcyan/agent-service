import { useCallback, useState, useMemo } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  ConnectionMode,
  Controls,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
  Panel,
  ReactFlowProvider,
} from 'reactflow';
import type { 
  Edge, 
  Node, 
  Connection as ReactFlowConnection,
  NodeProps,
  OnNodesDelete,
} from 'reactflow';
import type { WorkflowData, NodeType } from '../services/api';
import NodeTypeSelector from './NodeTypeSelector';
import ExecuteWorkflowButton from './ExecuteWorkflowDialog';
import NodePropertiesDialog from './NodePropertiesDialog';

interface Connection {
  from_node: string;
  from_port: string;
  to_node: string;
  to_port: string;
}

interface WorkflowEditorProps {}

// 自定义节点组件
interface CustomNodeProps extends NodeProps {
  setSelectedNode?: (node: Node | null) => void;
  setNodes?: (updater: (nodes: Node[]) => Node[]) => void;
}

const CustomNode = ({ data, id, setSelectedNode, setNodes }: CustomNodeProps) => {
  const [showMenu, setShowMenu] = useState(false);
  
  // 显示所有输入端口
  const ports = useMemo(() => {
    const inputPorts: string[] = [];
    const outputPorts: string[] = [];

    // 从节点的 inputs 中获取所有可能的输入端口
    if (data.inputs && typeof data.inputs === 'object') {
      Object.keys(data.inputs).forEach(key => {
        inputPorts.push(key);
      });
    }

    // 从节点的 outputs 中获取所有可能的输出端口
    if (data.outputs && typeof data.outputs === 'object') {
      Object.keys(data.outputs).forEach(key => {
        outputPorts.push(key);
      });
    }

    // 如果没有明确的 outputs，则从连接中推断输出端口
    if (data.connections) {
      data.connections.forEach((conn: Connection) => {
        if (conn.from_port && !outputPorts.includes(conn.from_port)) {
          outputPorts.push(conn.from_port);
        }
      });
    }

    return { inputPorts, outputPorts };
  }, [data.inputs, data.outputs, data.connections]);

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
      className="p-2 rounded-lg transition-all duration-200 ring-1 ring-black/70 resize-node"
      style={{
        minWidth: data.width || 400,
        width: data.width || 400,
        height: 'auto',
        position: 'relative'
      }}
    >
      <div 
        className={`px-4 py-3 rounded-md bg-white transition-all duration-200 ${
          data.selected 
            ? 'ring-2 ring-blue-500 shadow-lg' 
            : 'ring-1 ring-gray-200/50'
        }`}
        style={{
          width: '100%',
          height: '100%'
        }}
      >
      <div className="font-bold text-sm mb-2 flex items-center justify-between">
        <span>{id}</span>
        <div className="flex items-center gap-2 relative">
          <span className="text-xs text-gray-500">{data.type}</span>
          <button 
            className="cursor-pointer text-gray-400 hover:text-gray-600 px-1"
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
          >
            ⋮
          </button>
          {showMenu && (
            <div 
              className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg py-1 z-50 min-w-[100px]"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                className="w-full px-3 py-1.5 text-left text-sm hover:bg-gray-100"
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
                className="w-full px-3 py-1.5 text-left text-sm text-red-600 hover:bg-gray-100"
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
      
      <div className="grid grid-cols-2 gap-4">
        {/* 输入端口 */}
        <div className="border-r border-gray-200 pr-3">
          <div className="text-xs font-semibold text-gray-600 mb-2">Inputs</div>
          {ports.inputPorts.map((port) => (
            <div key={`${id}-input-${port}`} className="relative mb-2 last:mb-0">
              <Handle
                type="target"
                position={Position.Left}
                id={port}
                className="w-2 h-2 !bg-blue-500"
                style={{ top: '10px' }}
              />
              <div className="ml-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-700">{port}:</span>
                  <span 
                    className="text-xs text-gray-500 truncate max-w-[120px]" 
                    title={JSON.stringify(data.inputs[port], null, 2)}
                  >
                    {formatValue(data.inputs[port])}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 输出端口 */}
        <div className="pl-3">
          <div className="text-xs font-semibold text-gray-600 mb-2">Outputs</div>
          {ports.outputPorts.map((port) => (
            <div key={`${id}-output-${port}`} className="relative mb-2 last:mb-0">
              <Handle
                type="source"
                position={Position.Right}
                id={port}
                className="w-2 h-2 !bg-green-500"
                style={{ top: '10px' }}
              />
              <div className="mr-3">
                <div className="flex items-center justify-end">
                  <span className="text-xs font-medium text-gray-700">{port}</span>
                </div>
              </div>
            </div>
          ))}
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

const WorkflowEditorContent = ({}: WorkflowEditorProps) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);

  // 将workflow数据转换为ReactFlow格式
  const transformWorkflowToFlow = (data: WorkflowData) => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    // 创建节点
    Object.entries(data.nodes).forEach(([id, node], index) => {
      flowNodes.push({
        id,
        type: 'default',
        position: { x: 250 * (index % 3), y: 200 * Math.floor(index / 3) },
        data: { 
          label: `${id} (${node.type})`,
          type: node.type,
          inputs: node.inputs,
          outputs: {},  // 初始化为空对象
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

  // 打开本地workflow文件
  const openWorkflow = useCallback(async () => {
    try {
      // 创建一个隐藏的文件输入元素
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.json';
      
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = JSON.parse(e.target?.result as string);
            const flowData = transformWorkflowToFlow(data);
            setNodes(flowData.nodes);
            setEdges(flowData.edges);
          } catch (error) {
            console.error('Failed to parse workflow file:', error);
            alert('Failed to parse workflow file. Please make sure it is a valid JSON file.');
          }
        };
        reader.readAsText(file);
      };

      input.click();
    } catch (error) {
      console.error('Failed to open workflow:', error);
    }
  }, [setNodes, setEdges]);

  // 保存workflow数据到本地文件
  const saveWorkflow = useCallback(() => {
    try {
      const workflowData = transformFlowToWorkflow(nodes, edges);
      const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = 'workflow.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  }, [nodes, edges]);

  // 处理连接变化
  const onConnect = useCallback(
    (params: ReactFlowConnection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );


  // Handle node deletion
  const onNodesDelete: OnNodesDelete = useCallback(
    (nodesToDelete) => {
      // Remove all edges connected to deleted nodes
      const nodeIds = new Set(nodesToDelete.map(node => node.id));
      setEdges(edges.filter(edge => 
        !nodeIds.has(edge.source) && !nodeIds.has(edge.target)
      ));
    },
    [edges, setEdges]
  );

  // Handle adding new nodes
  const onNodeTypeSelect = useCallback((nodeType: NodeType) => {
    const newNode: Node = {
      id: `${nodeType.name}_${Date.now()}`,
      type: 'default',
      position: { x: 100, y: 100 },
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
      },
    };
    setNodes(nodes => [...nodes, newNode]);
  }, [setNodes]);

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

  const nodeTypes = useMemo(() => ({
    default: (props: NodeProps) => (
      <CustomNode
        {...props}
        setSelectedNode={setSelectedNode}
        setNodes={setNodes}
      />
    ),
  }), [setSelectedNode, setNodes]);

  return (
    <div className="h-screen w-full">
      <Panel position="top-right" className="flex gap-2">
        <NodeTypeSelector onSelect={onNodeTypeSelect} />
        <button
          onClick={openWorkflow}
          className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
        >
          Open
        </button>
        <button
          onClick={saveWorkflow}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Export
        </button>
        <ExecuteWorkflowButton
          workflow={transformFlowToWorkflow(nodes, edges)}
        />
      </Panel>
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
          className="fixed bg-white rounded-lg shadow-lg py-2 z-50"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
        >
          {contextMenu.type === 'edge' ? (
            <button
              className="w-full px-4 py-2 text-left text-red-600 hover:bg-gray-100"
              onClick={() => onEdgeDelete(contextMenu.id)}
            >
              Delete Connection
            </button>
          ) : (
            <>
              <button
                className="w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => {
                  const node = nodes.find(n => n.id === contextMenu.id);
                  if (node) setSelectedNode(node);
                  setContextMenu(null);
                }}
              >
                Edit Node
              </button>
              <button
                className="w-full px-4 py-2 text-left text-red-600 hover:bg-gray-100"
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

      <ReactFlow
        nodes={nodes}
        edges={edges.map(edge => ({
          ...edge,
          className: edge.id === selectedEdge ? 'selected-edge' : '',
          animated: edge.id === selectedEdge,
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
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

const WorkflowEditor = (props: WorkflowEditorProps) => {
  return (
    <ReactFlowProvider>
      <WorkflowEditorContent {...props} />
    </ReactFlowProvider>
  );
};

export default WorkflowEditor;