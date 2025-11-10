/**
 * ForEach 子工作流编辑器 - 前端实现示例
 * 
 * 这个文件展示了如何在前端实现可视化的 ForEach 子工作流编辑器
 * 使用 React + TypeScript + React Flow (或类似的流程图库)
 */

import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';

// ============================================================================
// 类型定义
// ============================================================================

interface SubWorkflowNode {
  type: string;
  id: string;
  input_values?: Record<string, any>;
  position?: { x: number; y: number };
}

interface SubWorkflowConnection {
  from_node: string;
  from_port: string;
  to_node: string;
  to_port: string;
}

interface SubWorkflowDefinition {
  nodes: SubWorkflowNode[];
  connections: SubWorkflowConnection[];
}

interface PortInfo {
  name: string;
  type: string;
  required: boolean;
  tooltip?: string;
}

interface NodeTypeInfo {
  node_type: string;
  input_ports: PortInfo[];
  output_ports: PortInfo[];
  category: string;
  description?: string;
}

interface ValidationError {
  type: string;
  message: string;
  node_id?: string;
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: string[];
}

// ============================================================================
// API 客户端
// ============================================================================

class ForEachEditorAPI {
  private baseUrl = '/api/workflow/foreach';

  async getNodePorts(nodeType: string): Promise<NodeTypeInfo> {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeType}/ports`);
    if (!response.ok) throw new Error('Failed to fetch node ports');
    return response.json();
  }

  async listAvailableNodes(): Promise<Record<string, string[]>> {
    const response = await fetch(`${this.baseUrl}/nodes/list`);
    if (!response.ok) throw new Error('Failed to fetch node list');
    return response.json();
  }

  async validateSubWorkflow(
    subWorkflow: SubWorkflowDefinition,
    resultNodeId: string,
    resultPortName: string
  ): Promise<ValidationResult> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sub_workflow: subWorkflow,
        result_node_id: resultNodeId,
        result_port_name: resultPortName,
      }),
    });
    if (!response.ok) throw new Error('Failed to validate subworkflow');
    return response.json();
  }

  async getTemplates() {
    const response = await fetch(`${this.baseUrl}/templates`);
    if (!response.ok) throw new Error('Failed to fetch templates');
    return response.json();
  }
}

const api = new ForEachEditorAPI();

// ============================================================================
// 子工作流编辑器组件
// ============================================================================

interface SubWorkflowEditorProps {
  foreachNodeId: string;
  initialSubWorkflow?: SubWorkflowDefinition;
  initialResultNodeId?: string;
  initialResultPortName?: string;
  onSave: (
    subWorkflow: SubWorkflowDefinition,
    resultNodeId: string,
    resultPortName: string
  ) => void;
  onCancel: () => void;
}

export const SubWorkflowEditor: React.FC<SubWorkflowEditorProps> = ({
  foreachNodeId,
  initialSubWorkflow,
  initialResultNodeId,
  initialResultPortName,
  onSave,
  onCancel,
}) => {
  // React Flow 状态
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 编辑器状态
  const [resultNodeId, setResultNodeId] = useState(initialResultNodeId || '');
  const [resultPortName, setResultPortName] = useState(initialResultPortName || '');
  const [availableNodes, setAvailableNodes] = useState<Record<string, string[]>>({});
  const [nodeTypeInfo, setNodeTypeInfo] = useState<Record<string, NodeTypeInfo>>({});
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [showNodePicker, setShowNodePicker] = useState(false);

  // 初始化：加载可用节点和子工作流
  useEffect(() => {
    loadAvailableNodes();
    if (initialSubWorkflow) {
      loadSubWorkflow(initialSubWorkflow);
    } else {
      initializeEmptySubWorkflow();
    }
  }, []);

  // 加载可用节点列表
  const loadAvailableNodes = async () => {
    try {
      const nodes = await api.listAvailableNodes();
      setAvailableNodes(nodes);
    } catch (error) {
      console.error('Failed to load available nodes:', error);
    }
  };

  // 初始化空的子工作流（自动添加 ForEachItemNode）
  const initializeEmptySubWorkflow = () => {
    const itemNode: Node = {
      id: 'foreach_item_node',
      type: 'foreachItem',
      position: { x: 100, y: 200 },
      data: {
        label: 'ForEach Item',
        nodeType: 'ForEachItemNode',
        outputs: [
          { id: 'item', label: '当前项目', type: 'any' },
          { id: 'index', label: '索引', type: 'number' },
        ],
      },
    };

    setNodes([itemNode]);
  };

  // 从 SubWorkflowDefinition 加载到画布
  const loadSubWorkflow = async (subWorkflow: SubWorkflowDefinition) => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    // 转换节点
    for (const node of subWorkflow.nodes) {
      // 获取节点的端口信息
      if (!nodeTypeInfo[node.type]) {
        try {
          const info = await api.getNodePorts(node.type);
          setNodeTypeInfo((prev) => ({ ...prev, [node.type]: info }));
        } catch (error) {
          console.error(`Failed to load info for ${node.type}:`, error);
        }
      }

      flowNodes.push({
        id: node.id,
        type: node.type === 'ForEachItemNode' ? 'foreachItem' : 'custom',
        position: node.position || { x: 0, y: 0 },
        data: {
          label: node.type,
          nodeType: node.type,
          config: node.input_values,
        },
      });
    }

    // 转换连接
    for (const conn of subWorkflow.connections) {
      flowEdges.push({
        id: `${conn.from_node}_${conn.from_port}_${conn.to_node}_${conn.to_port}`,
        source: conn.from_node,
        sourceHandle: conn.from_port,
        target: conn.to_node,
        targetHandle: conn.to_port,
      });
    }

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  // 从画布序列化到 SubWorkflowDefinition
  const serializeSubWorkflow = (): SubWorkflowDefinition => {
    const subWorkflowNodes: SubWorkflowNode[] = nodes.map((node) => ({
      type: node.data.nodeType,
      id: node.id,
      input_values: node.data.config || {},
      position: node.position,
    }));

    const subWorkflowConnections: SubWorkflowConnection[] = edges.map((edge) => ({
      from_node: edge.source,
      from_port: edge.sourceHandle || '',
      to_node: edge.target,
      to_port: edge.targetHandle || '',
    }));

    return {
      nodes: subWorkflowNodes,
      connections: subWorkflowConnections,
    };
  };

  // 添加节点
  const addNode = useCallback(
    (nodeType: string) => {
      const newId = `node_${Date.now()}`;
      const newNode: Node = {
        id: newId,
        type: 'custom',
        position: { x: Math.random() * 400 + 200, y: Math.random() * 400 + 200 },
        data: {
          label: nodeType,
          nodeType: nodeType,
          config: {},
        },
      };

      setNodes((nds) => [...nds, newNode]);
      setShowNodePicker(false);

      // 加载节点端口信息
      if (!nodeTypeInfo[nodeType]) {
        api.getNodePorts(nodeType).then((info) => {
          setNodeTypeInfo((prev) => ({ ...prev, [nodeType]: info }));
        });
      }
    },
    [nodeTypeInfo]
  );

  // 处理连接
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge(connection, eds));
    },
    []
  );

  // 验证子工作流
  const validateWorkflow = async () => {
    if (!resultNodeId || !resultPortName) {
      setValidation({
        valid: false,
        errors: [{ type: 'missing_config', message: '请选择结果节点和端口' }],
        warnings: [],
      });
      return false;
    }

    try {
      const subWorkflow = serializeSubWorkflow();
      const result = await api.validateSubWorkflow(
        subWorkflow,
        resultNodeId,
        resultPortName
      );
      setValidation(result);
      return result.valid;
    } catch (error) {
      console.error('Validation failed:', error);
      return false;
    }
  };

  // 保存并返回
  const handleSave = async () => {
    const isValid = await validateWorkflow();
    if (isValid) {
      const subWorkflow = serializeSubWorkflow();
      onSave(subWorkflow, resultNodeId, resultPortName);
    }
  };

  // 获取可选的结果节点
  const selectableResultNodes = nodes.filter(
    (node) => node.data.nodeType !== 'ForEachItemNode'
  );

  // 获取结果节点的可用端口
  const resultNodePorts =
    resultNodeId && nodeTypeInfo[nodes.find((n) => n.id === resultNodeId)?.data.nodeType]
      ? nodeTypeInfo[nodes.find((n) => n.id === resultNodeId)!.data.nodeType].output_ports
      : [];

  return (
    <div className="subworkflow-editor">
      {/* 工具栏 */}
      <div className="editor-toolbar">
        <div className="toolbar-left">
          <h3>子工作流编辑器</h3>
          <button onClick={() => setShowNodePicker(true)} className="btn-add-node">
            + 添加节点
          </button>
        </div>

        <div className="toolbar-center">
          <label>结果节点:</label>
          <select
            value={resultNodeId}
            onChange={(e) => {
              setResultNodeId(e.target.value);
              setResultPortName('');
            }}
          >
            <option value="">请选择...</option>
            {selectableResultNodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.data.label}
              </option>
            ))}
          </select>

          {resultNodeId && (
            <>
              <label>输出端口:</label>
              <select
                value={resultPortName}
                onChange={(e) => setResultPortName(e.target.value)}
              >
                <option value="">请选择...</option>
                {resultNodePorts.map((port) => (
                  <option key={port.name} value={port.name}>
                    {port.name} ({port.type})
                  </option>
                ))}
              </select>
            </>
          )}
        </div>

        <div className="toolbar-right">
          <button onClick={validateWorkflow} className="btn-validate">
            验证
          </button>
          <button onClick={onCancel} className="btn-cancel">
            取消
          </button>
          <button onClick={handleSave} className="btn-save">
            保存并返回
          </button>
        </div>
      </div>

      {/* 验证结果 */}
      {validation && (
        <div className={`validation-result ${validation.valid ? 'valid' : 'invalid'}`}>
          {validation.valid ? (
            <span className="success">✓ 子工作流配置有效</span>
          ) : (
            <div className="errors">
              {validation.errors.map((error, index) => (
                <div key={index} className="error-item">
                  ✗ {error.message}
                </div>
              ))}
            </div>
          )}
          {validation.warnings.length > 0 && (
            <div className="warnings">
              {validation.warnings.map((warning, index) => (
                <div key={index} className="warning-item">
                  ⚠ {warning}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* React Flow 画布 */}
      <div className="flow-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>

      {/* 节点选择器 */}
      {showNodePicker && (
        <NodePicker
          availableNodes={availableNodes}
          onSelect={addNode}
          onClose={() => setShowNodePicker(false)}
        />
      )}
    </div>
  );
};

// ============================================================================
// 节点选择器组件
// ============================================================================

interface NodePickerProps {
  availableNodes: Record<string, string[]>;
  onSelect: (nodeType: string) => void;
  onClose: () => void;
}

const NodePicker: React.FC<NodePickerProps> = ({ availableNodes, onSelect, onClose }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // 过滤节点
  const filteredNodes = Object.entries(availableNodes).reduce(
    (acc, [category, nodeTypes]) => {
      if (selectedCategory !== 'all' && category !== selectedCategory) {
        return acc;
      }

      const filtered = nodeTypes.filter((type) =>
        type.toLowerCase().includes(search.toLowerCase())
      );

      if (filtered.length > 0) {
        acc[category] = filtered;
      }

      return acc;
    },
    {} as Record<string, string[]>
  );

  return (
    <div className="node-picker-overlay" onClick={onClose}>
      <div className="node-picker-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>选择节点</h3>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* 搜索和过滤 */}
          <div className="search-bar">
            <input
              type="text"
              placeholder="搜索节点..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="category-filter">
            <button
              className={selectedCategory === 'all' ? 'active' : ''}
              onClick={() => setSelectedCategory('all')}
            >
              全部
            </button>
            {Object.keys(availableNodes).map((category) => (
              <button
                key={category}
                className={selectedCategory === category ? 'active' : ''}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          {/* 节点列表 */}
          <div className="node-list">
            {Object.entries(filteredNodes).map(([category, nodeTypes]) => (
              <div key={category} className="node-category">
                <h4>{category}</h4>
                <div className="node-items">
                  {nodeTypes.map((nodeType) => (
                    <button
                      key={nodeType}
                      className="node-item"
                      onClick={() => onSelect(nodeType)}
                    >
                      {nodeType}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// ForEachNode 卡片组件（在主画布中显示）
// ============================================================================

interface ForEachNodeCardProps {
  nodeId: string;
  subWorkflow?: SubWorkflowDefinition;
  onEditSubWorkflow: () => void;
}

export const ForEachNodeCard: React.FC<ForEachNodeCardProps> = ({
  nodeId,
  subWorkflow,
  onEditSubWorkflow,
}) => {
  const hasSubWorkflow = subWorkflow && subWorkflow.nodes.length > 0;

  return (
    <div className="foreach-node-card">
      <div className="node-header">
        <span className="node-icon">🔄</span>
        <span className="node-title">ForEach</span>
      </div>

      <div className="node-body">
        {/* 输入端口 */}
        <div className="port-section">
          <div className="port input">
            <span className="port-dot"></span>
            <span className="port-label">items</span>
          </div>
        </div>

        {/* 子工作流状态 */}
        <div className="subworkflow-status">
          {hasSubWorkflow ? (
            <>
              <span className="status-indicator success">✓</span>
              <span className="status-text">
                已配置 ({subWorkflow.nodes.length} 个节点)
              </span>
            </>
          ) : (
            <>
              <span className="status-indicator warning">⚠</span>
              <span className="status-text">未配置子工作流</span>
            </>
          )}
        </div>

        {/* 编辑按钮 */}
        <button className="edit-btn" onClick={onEditSubWorkflow}>
          {hasSubWorkflow ? '编辑子工作流 ✏️' : '配置子工作流 ➕'}
        </button>

        {/* 输出端口 */}
        <div className="port-section">
          <div className="port output">
            <span className="port-label">results</span>
            <span className="port-dot"></span>
          </div>
          <div className="port output">
            <span className="port-label">success_count</span>
            <span className="port-dot"></span>
          </div>
          <div className="port output">
            <span className="port-label">error_count</span>
            <span className="port-dot"></span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 样式（CSS-in-JS 或单独的 CSS 文件）
// ============================================================================

const styles = `
.subworkflow-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.toolbar-left h3 {
  margin: 0 16px 0 0;
  display: inline-block;
}

.btn-add-node {
  padding: 8px 16px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-center select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.btn-validate {
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  padding: 8px 16px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-save {
  padding: 8px 16px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.validation-result {
  padding: 12px 16px;
  margin: 0;
}

.validation-result.valid {
  background: #d1fae5;
  color: #065f46;
}

.validation-result.invalid {
  background: #fee2e2;
  color: #991b1b;
}

.flow-canvas {
  flex: 1;
  background: white;
}

.foreach-node-card {
  border: 2px solid #6366f1;
  border-radius: 8px;
  background: white;
  min-width: 200px;
  padding: 12px;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.subworkflow-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  margin: 8px 0;
}

.status-indicator.success {
  color: #10b981;
}

.status-indicator.warning {
  color: #f59e0b;
}

.edit-btn {
  width: 100%;
  padding: 8px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin: 8px 0;
}

.edit-btn:hover {
  background: #4f46e5;
}

.port {
  display: flex;
  align-items: center;
  padding: 4px 0;
}

.port.input {
  justify-content: flex-start;
}

.port.output {
  justify-content: flex-end;
}

.port-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #6366f1;
  margin: 0 8px;
}
`;

export default SubWorkflowEditor;

