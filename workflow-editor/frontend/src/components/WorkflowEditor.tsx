import { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  ConnectionMode,
  Controls,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
} from 'reactflow';
import type { 
  Edge, 
  Node, 
  Connection as ReactFlowConnection,
  NodeProps,
} from 'reactflow';
import { api, type WorkflowData } from '../services/api';

interface Connection {
  from_node: string;
  from_port: string;
  to_node: string;
  to_port: string;
}

interface WorkflowEditorProps {
  filename: string;
}

// 自定义节点组件
const CustomNode = ({ data, id }: NodeProps) => {
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

  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-gray-200">
      <div className="font-bold text-sm">{id}</div>
      <div className="text-xs text-gray-500">{data.type}</div>
      
      {/* 输入端口 */}
      {ports.inputPorts.map((port, index) => (
        <div key={`${id}-input-${port}`} className="relative" style={{ height: '20px' }}>
          <Handle
            type="target"
            position={Position.Left}
            id={port}
            className="w-2 h-2 !bg-blue-500"
            style={{ top: '50%' }}
          />
          <span className="text-xs absolute left-4 top-1/2 transform -translate-y-1/2">
            {port}
          </span>
        </div>
      ))}

      {/* 输出端口 */}
      {ports.outputPorts.map((port, index) => (
        <div key={`${id}-output-${port}`} className="relative" style={{ height: '20px' }}>
          <Handle
            type="source"
            position={Position.Right}
            id={port}
            className="w-2 h-2 !bg-green-500"
            style={{ top: '50%' }}
          />
          <span className="text-xs absolute right-4 top-1/2 transform -translate-y-1/2">
            {port}
          </span>
        </div>
      ))}
    </div>
  );
};

const nodeTypes = {
  default: CustomNode,
};

const WorkflowEditor = ({ filename }: WorkflowEditorProps) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

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

  // 加载workflow数据
  const loadWorkflow = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getWorkflow(filename);
      const flowData = transformWorkflowToFlow(data);
      setNodes(flowData.nodes);
      setEdges(flowData.edges);
    } catch (error) {
      console.error('Failed to load workflow:', error);
    } finally {
      setLoading(false);
    }
  }, [filename, setNodes, setEdges]);

  // 保存workflow数据
  const saveWorkflow = useCallback(async () => {
    try {
      const workflowData = transformFlowToWorkflow(nodes, edges);
      await api.updateWorkflow(filename, workflowData);
    } catch (error) {
      console.error('Failed to save workflow:', error);
    }
  }, [filename, nodes, edges]);

  // 处理连接变化
  const onConnect = useCallback(
    (params: ReactFlowConnection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  useEffect(() => {
    loadWorkflow();
  }, [loadWorkflow]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="h-screen w-full">
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={saveWorkflow}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Save
        </button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
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

export default WorkflowEditor;