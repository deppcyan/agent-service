# ForEach Node 前端可视化编辑方案

## 概述

为了让用户更方便地使用 ForEachNode，我们需要在前端实现可视化的子工作流编辑器。用户可以通过双击 ForEachNode 进入子工作流画布，直观地拖拽节点和连接，编辑完成后自动生成 `sub_workflow` 配置。

## 用户交互流程

```
主画布
  │
  ├─ 添加 ForEachNode
  │
  ├─ 双击 ForEachNode（或点击"编辑子工作流"按钮）
  │     │
  │     ├─ 进入子工作流编辑模式
  │     │   │
  │     │   ├─ 新画布打开（面包屑导航显示：主工作流 > ForEach 子工作流）
  │     │   │
  │     │   ├─ 自动添加 ForEachItemNode（作为起点）
  │     │   │
  │     │   ├─ 用户拖拽节点、创建连接
  │     │   │
  │     │   ├─ 指定输出节点（高亮可选）
  │     │   │
  │     │   └─ 点击"完成"或"返回"
  │     │         │
  │     └─────────┘
  │
  └─ 自动生成 sub_workflow 配置，返回主画布
```

## 核心设计

### 1. 多层画布管理

#### 画布状态结构

```typescript
interface WorkflowCanvas {
  id: string;
  type: 'main' | 'foreach_subworkflow';
  parentNodeId?: string;  // 如果是子工作流，记录父节点ID
  nodes: Node[];
  connections: Connection[];
  metadata: {
    title: string;
    description?: string;
  };
}

interface CanvasStack {
  canvases: WorkflowCanvas[];  // 画布栈
  currentIndex: number;         // 当前画布索引
}
```

#### 画布切换

```typescript
class CanvasManager {
  private canvasStack: WorkflowCanvas[] = [];
  private currentIndex: number = 0;

  // 进入子工作流编辑
  enterSubWorkflow(foreachNode: ForEachNode) {
    const subCanvas: WorkflowCanvas = {
      id: `subworkflow_${foreachNode.id}`,
      type: 'foreach_subworkflow',
      parentNodeId: foreachNode.id,
      nodes: this.loadSubWorkflowNodes(foreachNode),
      connections: this.loadSubWorkflowConnections(foreachNode),
      metadata: {
        title: `${foreachNode.name} 子工作流`
      }
    };
    
    this.canvasStack.push(subCanvas);
    this.currentIndex = this.canvasStack.length - 1;
    this.renderCanvas(subCanvas);
  }

  // 退出子工作流编辑
  exitSubWorkflow() {
    if (this.currentIndex > 0) {
      const subCanvas = this.canvasStack.pop();
      this.currentIndex--;
      
      // 保存子工作流到父节点
      this.saveSubWorkflowToParent(subCanvas);
      
      // 返回父画布
      this.renderCanvas(this.getCurrentCanvas());
    }
  }

  // 保存子工作流到 ForEachNode
  private saveSubWorkflowToParent(subCanvas: WorkflowCanvas) {
    const parentCanvas = this.canvasStack[this.currentIndex];
    const foreachNode = parentCanvas.nodes.find(
      n => n.id === subCanvas.parentNodeId
    ) as ForEachNode;
    
    if (foreachNode) {
      foreachNode.config.sub_workflow = {
        nodes: subCanvas.nodes.map(n => ({
          type: n.type,
          id: n.id,
          input_values: n.inputValues || {}
        })),
        connections: subCanvas.connections.map(c => ({
          from_node: c.fromNodeId,
          from_port: c.fromPort,
          to_node: c.toNodeId,
          to_port: c.toPort
        }))
      };
    }
  }
}
```

### 2. UI 组件设计

#### 面包屑导航

```typescript
interface BreadcrumbItem {
  label: string;
  canvasId: string;
  onClick: () => void;
}

const BreadcrumbNavigation: React.FC<{
  items: BreadcrumbItem[];
}> = ({ items }) => {
  return (
    <div className="breadcrumb-nav">
      {items.map((item, index) => (
        <span key={item.canvasId}>
          <a onClick={item.onClick}>{item.label}</a>
          {index < items.length - 1 && <span> / </span>}
        </span>
      ))}
    </div>
  );
};
```

#### ForEachNode 卡片

```typescript
const ForEachNodeCard: React.FC<{
  node: ForEachNode;
  onEdit: () => void;
}> = ({ node, onEdit }) => {
  const hasSubWorkflow = node.config.sub_workflow?.nodes?.length > 0;
  
  return (
    <div className="foreach-node-card">
      <div className="node-header">
        <span className="node-icon">🔄</span>
        <span className="node-title">ForEach</span>
      </div>
      
      <div className="node-body">
        {/* 输入端口 */}
        <div className="port-group">
          <div className="port input">items</div>
        </div>
        
        {/* 子工作流状态 */}
        <div className="subworkflow-status">
          {hasSubWorkflow ? (
            <span className="status-indicator success">
              ✓ 已配置 ({node.config.sub_workflow.nodes.length} 个节点)
            </span>
          ) : (
            <span className="status-indicator warning">
              ⚠ 未配置子工作流
            </span>
          )}
        </div>
        
        {/* 编辑按钮 */}
        <button 
          className="edit-subworkflow-btn"
          onClick={onEdit}
        >
          {hasSubWorkflow ? '编辑子工作流' : '配置子工作流'}
        </button>
        
        {/* 输出端口 */}
        <div className="port-group">
          <div className="port output">results</div>
          <div className="port output">success_count</div>
          <div className="port output">error_count</div>
        </div>
      </div>
    </div>
  );
};
```

#### 子工作流编辑器工具栏

```typescript
const SubWorkflowToolbar: React.FC<{
  onSave: () => void;
  onCancel: () => void;
  selectedResultNode?: string;
  availableNodes: Node[];
  onSelectResultNode: (nodeId: string) => void;
}> = ({ onSave, onCancel, selectedResultNode, availableNodes, onSelectResultNode }) => {
  return (
    <div className="subworkflow-toolbar">
      <div className="toolbar-left">
        <span className="toolbar-label">子工作流编辑器</span>
      </div>
      
      <div className="toolbar-center">
        <label>结果节点:</label>
        <select 
          value={selectedResultNode}
          onChange={(e) => onSelectResultNode(e.target.value)}
        >
          <option value="">请选择...</option>
          {availableNodes.map(node => (
            <option key={node.id} value={node.id}>
              {node.name} ({node.type})
            </option>
          ))}
        </select>
      </div>
      
      <div className="toolbar-right">
        <button onClick={onCancel} className="btn-secondary">
          取消
        </button>
        <button onClick={onSave} className="btn-primary">
          保存并返回
        </button>
      </div>
    </div>
  );
};
```

### 3. 子工作流初始化

当用户首次进入子工作流编辑器时，自动创建 ForEachItemNode：

```typescript
function initializeSubWorkflow(foreachNodeId: string): WorkflowCanvas {
  // 创建 ForEachItemNode 作为起点
  const itemNode: Node = {
    id: `foreach_item_${Date.now()}`,
    type: 'ForEachItemNode',
    name: 'ForEach Item',
    position: { x: 100, y: 200 },
    config: {},
    ports: {
      input: [],
      output: [
        { name: 'item', type: 'any', label: '当前项目' },
        { name: 'index', type: 'number', label: '索引' }
      ]
    }
  };

  return {
    id: `subworkflow_${foreachNodeId}`,
    type: 'foreach_subworkflow',
    parentNodeId: foreachNodeId,
    nodes: [itemNode],
    connections: [],
    metadata: {
      title: 'ForEach 子工作流',
      description: '在这里编辑每个项目的处理逻辑'
    }
  };
}
```

### 4. 结果节点选择

#### 高亮可选节点

```typescript
const SubWorkflowCanvas: React.FC<{
  canvas: WorkflowCanvas;
  resultNodeId?: string;
}> = ({ canvas, resultNodeId }) => {
  // 计算哪些节点可以作为结果节点（有输出端口的节点）
  const selectableNodes = canvas.nodes.filter(
    node => node.ports.output.length > 0 && node.type !== 'ForEachItemNode'
  );

  return (
    <div className="canvas">
      {canvas.nodes.map(node => (
        <NodeComponent
          key={node.id}
          node={node}
          isResultNode={node.id === resultNodeId}
          isSelectable={selectableNodes.includes(node)}
          className={classNames({
            'result-node': node.id === resultNodeId,
            'selectable': selectableNodes.includes(node)
          })}
        />
      ))}
    </div>
  );
};
```

#### 结果端口选择

```typescript
interface ResultConfig {
  nodeId: string;
  portName: string;
}

const ResultPortSelector: React.FC<{
  nodes: Node[];
  selected?: ResultConfig;
  onChange: (config: ResultConfig) => void;
}> = ({ nodes, selected, onChange }) => {
  const [selectedNode, setSelectedNode] = useState(selected?.nodeId);
  const [selectedPort, setSelectedPort] = useState(selected?.portName);
  
  const availablePorts = selectedNode
    ? nodes.find(n => n.id === selectedNode)?.ports.output || []
    : [];

  return (
    <div className="result-port-selector">
      <div className="selector-group">
        <label>结果节点:</label>
        <select 
          value={selectedNode}
          onChange={(e) => {
            setSelectedNode(e.target.value);
            setSelectedPort('');
          }}
        >
          <option value="">请选择节点...</option>
          {nodes.filter(n => n.type !== 'ForEachItemNode').map(node => (
            <option key={node.id} value={node.id}>
              {node.name}
            </option>
          ))}
        </select>
      </div>
      
      {selectedNode && (
        <div className="selector-group">
          <label>输出端口:</label>
          <select
            value={selectedPort}
            onChange={(e) => {
              setSelectedPort(e.target.value);
              onChange({
                nodeId: selectedNode,
                portName: e.target.value
              });
            }}
          >
            <option value="">请选择端口...</option>
            {availablePorts.map(port => (
              <option key={port.name} value={port.name}>
                {port.label || port.name} ({port.type})
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};
```

### 5. 数据序列化与反序列化

#### 从 sub_workflow 加载到画布

```typescript
function deserializeSubWorkflow(
  subWorkflow: SubWorkflowDefinition
): WorkflowCanvas {
  // 转换节点
  const nodes: Node[] = subWorkflow.nodes.map(nodeDef => ({
    id: nodeDef.id,
    type: nodeDef.type,
    name: getNodeDisplayName(nodeDef.type),
    position: nodeDef.position || getAutoPosition(),
    config: nodeDef.input_values || {},
    ports: getNodePorts(nodeDef.type)
  }));

  // 转换连接
  const connections: Connection[] = subWorkflow.connections.map(connDef => ({
    id: `${connDef.from_node}_${connDef.from_port}_${connDef.to_node}_${connDef.to_port}`,
    fromNodeId: connDef.from_node,
    fromPort: connDef.from_port,
    toNodeId: connDef.to_node,
    toPort: connDef.to_port
  }));

  return {
    id: `subworkflow_${Date.now()}`,
    type: 'foreach_subworkflow',
    nodes,
    connections,
    metadata: {
      title: 'ForEach 子工作流'
    }
  };
}
```

#### 从画布序列化到 sub_workflow

```typescript
function serializeSubWorkflow(canvas: WorkflowCanvas): SubWorkflowDefinition {
  return {
    nodes: canvas.nodes.map(node => ({
      type: node.type,
      id: node.id,
      input_values: node.config,
      position: node.position  // 可选，用于保存布局
    })),
    connections: canvas.connections.map(conn => ({
      from_node: conn.fromNodeId,
      from_port: conn.fromPort,
      to_node: conn.toNodeId,
      to_port: conn.toPort
    }))
  };
}
```

## 完整交互示例

### 场景：批量文本处理

```typescript
// 1. 用户在主画布添加 ForEachNode
const foreachNode = createNode('ForEachNode', {
  name: 'Batch Text Process'
});

// 2. 双击进入子工作流编辑
canvasManager.enterSubWorkflow(foreachNode);

// 3. 自动创建的 ForEachItemNode 作为起点
// 用户拖拽添加节点：
//   - TextStripNode (去除空格)
//   - TextReplaceNode (替换文本)

// 4. 用户创建连接：
//   ForEachItemNode.item -> TextStripNode.text
//   TextStripNode.text -> TextReplaceNode.text

// 5. 选择结果节点：
resultConfig = {
  nodeId: 'text_replace_node_id',
  portName: 'replaced_text'
};

// 6. 点击"保存并返回"
// 自动生成 sub_workflow：
{
  nodes: [
    { type: 'ForEachItemNode', id: 'item_1' },
    { type: 'TextStripNode', id: 'strip_1' },
    { type: 'TextReplaceNode', id: 'replace_1', input_values: { ... } }
  ],
  connections: [
    { from_node: 'item_1', from_port: 'item', to_node: 'strip_1', to_port: 'text' },
    { from_node: 'strip_1', from_port: 'text', to_node: 'replace_1', to_port: 'text' }
  ]
}

// 7. ForEachNode 自动更新配置：
foreachNode.config = {
  sub_workflow: { ... },
  result_node_id: 'replace_1',
  result_port_name: 'replaced_text'
};
```

## 视觉设计

### 主画布中的 ForEachNode

```
┌─────────────────────────────┐
│     🔄 ForEach Node         │
├─────────────────────────────┤
│ ◄ items (array)             │
├─────────────────────────────┤
│                             │
│  ┌─────────────────────┐   │
│  │ ✓ 已配置子工作流     │   │
│  │   (3 个节点)        │   │
│  └─────────────────────┘   │
│                             │
│  [ 编辑子工作流 📝 ]        │
│                             │
├─────────────────────────────┤
│             results (array) ►│
│       success_count (number)►│
│         error_count (number)►│
└─────────────────────────────┘
```

### 子工作流编辑模式

```
┌──────────────────────────────────────────────────────────┐
│ 主工作流 / ForEach 子工作流                   [取消] [保存]│
├──────────────────────────────────────────────────────────┤
│ 结果节点: [TextReplaceNode ▼] 端口: [replaced_text ▼]   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐                                    │
│  │ ForEachItemNode │─────item─────┐                     │
│  │  (自动添加)     │              │                     │
│  └─────────────────┘              ▼                     │
│                          ┌──────────────────┐           │
│                          │  TextStripNode   │           │
│                          └──────────────────┘           │
│                                   │                     │
│                                   │ text                │
│                                   ▼                     │
│                          ┌──────────────────┐  ◄──结果节点
│                          │ TextReplaceNode  │           │
│                          └──────────────────┘           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 技术实现要点

### 1. 状态管理

```typescript
// Redux Store
interface WorkflowState {
  canvasStack: WorkflowCanvas[];
  currentCanvasIndex: number;
  selectedNodes: string[];
  resultConfig?: {
    nodeId: string;
    portName: string;
  };
}

// Actions
const actions = {
  enterSubWorkflow: (nodeId: string) => ({...}),
  exitSubWorkflow: () => ({...}),
  updateSubWorkflow: (canvas: WorkflowCanvas) => ({...}),
  setResultNode: (nodeId: string, portName: string) => ({...})
};
```

### 2. 验证逻辑

```typescript
function validateSubWorkflow(canvas: WorkflowCanvas): ValidationResult {
  const errors: string[] = [];
  
  // 1. 必须有 ForEachItemNode
  const hasItemNode = canvas.nodes.some(n => n.type === 'ForEachItemNode');
  if (!hasItemNode) {
    errors.push('子工作流必须包含 ForEachItemNode');
  }
  
  // 2. 必须选择结果节点
  if (!canvas.metadata.resultNodeId) {
    errors.push('请选择结果节点');
  }
  
  // 3. 结果节点必须存在
  const resultNode = canvas.nodes.find(n => n.id === canvas.metadata.resultNodeId);
  if (!resultNode) {
    errors.push('选择的结果节点不存在');
  }
  
  // 4. 检查是否有孤立节点
  const connectedNodes = new Set<string>();
  canvas.connections.forEach(c => {
    connectedNodes.add(c.fromNodeId);
    connectedNodes.add(c.toNodeId);
  });
  
  const isolatedNodes = canvas.nodes.filter(
    n => !connectedNodes.has(n.id) && n.type !== 'ForEachItemNode'
  );
  
  if (isolatedNodes.length > 0) {
    errors.push(`发现 ${isolatedNodes.length} 个未连接的节点`);
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}
```

### 3. 自动布局

```typescript
function autoLayoutNodes(nodes: Node[]): Node[] {
  // 简单的从左到右布局算法
  const layers = calculateLayers(nodes);
  const layerWidth = 250;
  const nodeHeight = 120;
  const verticalSpacing = 50;
  
  return nodes.map(node => {
    const layer = layers[node.id];
    const nodesInLayer = Object.keys(layers).filter(id => layers[id] === layer);
    const indexInLayer = nodesInLayer.indexOf(node.id);
    
    return {
      ...node,
      position: {
        x: 100 + layer * layerWidth,
        y: 100 + indexInLayer * (nodeHeight + verticalSpacing)
      }
    };
  });
}
```

## API 支持

### 后端需要提供的接口

```python
# 获取节点的输入输出端口信息
GET /api/workflow/nodes/{node_type}/ports
Response:
{
  "input_ports": [
    {"name": "text", "type": "string", "required": true}
  ],
  "output_ports": [
    {"name": "text", "type": "string"}
  ]
}

# 验证子工作流配置
POST /api/workflow/foreach/validate
Request:
{
  "sub_workflow": {...},
  "result_node_id": "node_1",
  "result_port_name": "text"
}
Response:
{
  "valid": true,
  "errors": []
}
```

## 渐进式实现计划

### Phase 1: 基础功能（MVP）
- ✅ 双击 ForEachNode 进入子工作流编辑
- ✅ 面包屑导航
- ✅ 自动创建 ForEachItemNode
- ✅ 基本的节点拖拽和连接
- ✅ 选择结果节点
- ✅ 保存并返回

### Phase 2: 增强体验
- 节点搜索和过滤
- 自动布局
- 子工作流验证
- 错误提示
- 布局保存

### Phase 3: 高级功能
- 子工作流预览
- 结果端口智能推荐
- 子工作流模板
- 复制粘贴子工作流
- 历史版本管理

## 样式示例 (CSS)

```css
/* ForEachNode 卡片 */
.foreach-node-card {
  border: 2px solid #6366f1;
  border-radius: 8px;
  background: white;
  min-width: 200px;
}

.subworkflow-status {
  padding: 8px;
  margin: 8px 0;
  border-radius: 4px;
  background: #f3f4f6;
}

.status-indicator.success {
  color: #10b981;
}

.status-indicator.warning {
  color: #f59e0b;
}

.edit-subworkflow-btn {
  width: 100%;
  padding: 8px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-subworkflow-btn:hover {
  background: #4f46e5;
}

/* 子工作流编辑器 */
.subworkflow-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.result-node {
  border: 2px solid #10b981;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}

.selectable {
  cursor: pointer;
}

.selectable:hover {
  border-color: #6366f1;
}

/* 面包屑 */
.breadcrumb-nav {
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.breadcrumb-nav a {
  color: #6366f1;
  cursor: pointer;
  text-decoration: none;
}

.breadcrumb-nav a:hover {
  text-decoration: underline;
}
```

## 总结

这个方案提供了完整的可视化编辑体验：

1. **直观的交互** - 双击进入，画布编辑，一键返回
2. **自动管理** - 自动生成配置，无需手写 JSON
3. **即时反馈** - 实时验证，错误提示
4. **灵活扩展** - 支持任意复杂的子工作流

用户只需要像编辑普通工作流一样编辑子工作流，系统会自动处理所有的配置生成和保存工作。

