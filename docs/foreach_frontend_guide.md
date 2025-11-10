# ForEach 前端集成完整指南

## 快速概览

本指南提供了在前端实现 ForEach 可视化编辑器的完整方案，包括：

1. **后端 API** - 已实现在 `app/api/foreach_editor.py`
2. **前端示例代码** - 参考 `docs/frontend_implementation_example.tsx`
3. **集成方案** - 详见 `docs/foreach_frontend_integration.md`

## 核心交互流程

```
1. 用户在主画布添加 ForEachNode
   ↓
2. 双击 ForEachNode 或点击"编辑子工作流"
   ↓
3. 进入子工作流编辑模式
   │
   ├─ 自动添加 ForEachItemNode（起点）
   ├─ 用户拖拽添加其他节点
   ├─ 创建节点间的连接
   ├─ 选择结果节点和输出端口
   └─ 点击"保存并返回"
      ↓
4. 自动生成 sub_workflow 配置
   ↓
5. 返回主画布，ForEachNode 显示已配置状态
```

## 后端 API 接口

### 1. 获取节点端口信息

```typescript
GET /api/workflow/foreach/nodes/{node_type}/ports

Response:
{
  "node_type": "TextStripNode",
  "input_ports": [
    {
      "name": "text",
      "type": "string",
      "required": true,
      "tooltip": "要处理的文本"
    }
  ],
  "output_ports": [
    {
      "name": "text",
      "type": "string",
      "tooltip": "处理后的文本"
    }
  ],
  "category": "text_process",
  "description": "节点描述"
}
```

**用途**: 在画布上显示节点的输入输出端口，以便用户连接

### 2. 获取可用节点列表

```typescript
GET /api/workflow/foreach/nodes/list

Response:
{
  "text_process": ["TextStripNode", "TextReplaceNode", "TextSplitNode"],
  "list_process": ["ListConcatNode", "ListIndexNode"],
  "basic_types": ["IntInputNode", "TextInputNode"],
  "control": ["ForEachItemNode"]
}
```

**用途**: 在节点选择器中显示可用的节点类型

### 3. 验证子工作流

```typescript
POST /api/workflow/foreach/validate

Request:
{
  "sub_workflow": {
    "nodes": [...],
    "connections": [...]
  },
  "result_node_id": "text_strip_1",
  "result_port_name": "text"
}

Response:
{
  "valid": true,
  "errors": [],
  "warnings": [
    "发现 1 个未连接的节点: node_2"
  ]
}
```

**用途**: 在保存前验证子工作流配置的正确性

### 4. 获取模板

```typescript
GET /api/workflow/foreach/templates

Response:
[
  {
    "name": "简单文本处理",
    "description": "清理文本：去除空格和换行",
    "sub_workflow": {...},
    "result_node_id": "text_strip",
    "result_port_name": "text"
  }
]
```

**用途**: 为用户提供快速开始的模板

## 前端实现步骤

### Step 1: 安装依赖

```bash
npm install reactflow
# 或
yarn add reactflow
```

### Step 2: 创建画布管理器

```typescript
// src/stores/canvasStore.ts
import create from 'zustand';

interface Canvas {
  id: string;
  type: 'main' | 'foreach_subworkflow';
  parentNodeId?: string;
  nodes: Node[];
  edges: Edge[];
}

interface CanvasStore {
  canvasStack: Canvas[];
  currentIndex: number;
  
  // 进入子工作流
  enterSubWorkflow: (nodeId: string) => void;
  
  // 退出子工作流
  exitSubWorkflow: () => void;
  
  // 保存子工作流
  saveSubWorkflow: (subWorkflow: SubWorkflowDefinition) => void;
}

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  canvasStack: [],
  currentIndex: 0,
  
  enterSubWorkflow: (nodeId) => {
    // 实现逻辑...
  },
  
  exitSubWorkflow: () => {
    // 实现逻辑...
  },
  
  saveSubWorkflow: (subWorkflow) => {
    // 实现逻辑...
  },
}));
```

### Step 3: 创建 ForEachNode 组件

```typescript
// src/components/ForEachNodeCard.tsx
import React from 'react';

export const ForEachNodeCard = ({ data, selected }) => {
  const hasSubWorkflow = data.subWorkflow?.nodes?.length > 0;
  
  return (
    <div className={`foreach-node ${selected ? 'selected' : ''}`}>
      <div className="node-header">
        🔄 ForEach
      </div>
      
      <div className="node-body">
        {/* 输入端口 */}
        <Handle type="target" position="left" id="items" />
        
        {/* 状态显示 */}
        <div className="status">
          {hasSubWorkflow ? (
            <span className="success">
              ✓ 已配置 ({data.subWorkflow.nodes.length} 节点)
            </span>
          ) : (
            <span className="warning">⚠ 未配置</span>
          )}
        </div>
        
        {/* 编辑按钮 */}
        <button
          onClick={() => data.onEdit?.()}
          className="edit-btn"
        >
          {hasSubWorkflow ? '编辑子工作流' : '配置子工作流'}
        </button>
        
        {/* 输出端口 */}
        <Handle type="source" position="right" id="results" />
        <Handle type="source" position="right" id="success_count" />
        <Handle type="source" position="right" id="error_count" />
      </div>
    </div>
  );
};
```

### Step 4: 创建子工作流编辑器

```typescript
// src/components/SubWorkflowEditor.tsx
import React, { useState, useCallback } from 'react';
import ReactFlow, { Controls, Background } from 'reactflow';

export const SubWorkflowEditor = ({
  foreachNodeId,
  initialSubWorkflow,
  onSave,
  onCancel
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [resultNodeId, setResultNodeId] = useState('');
  const [resultPortName, setResultPortName] = useState('');
  
  // 初始化
  useEffect(() => {
    if (initialSubWorkflow) {
      loadSubWorkflow(initialSubWorkflow);
    } else {
      // 自动添加 ForEachItemNode
      initializeWithItemNode();
    }
  }, []);
  
  // 保存
  const handleSave = async () => {
    const subWorkflow = serializeToSubWorkflow(nodes, edges);
    const isValid = await validateSubWorkflow(
      subWorkflow,
      resultNodeId,
      resultPortName
    );
    
    if (isValid) {
      onSave(subWorkflow, resultNodeId, resultPortName);
    }
  };
  
  return (
    <div className="subworkflow-editor">
      {/* 工具栏 */}
      <Toolbar
        resultNodeId={resultNodeId}
        resultPortName={resultPortName}
        onResultNodeChange={setResultNodeId}
        onResultPortChange={setResultPortName}
        onSave={handleSave}
        onCancel={onCancel}
      />
      
      {/* 画布 */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};
```

### Step 5: 集成到主画布

```typescript
// src/components/MainCanvas.tsx
import React, { useState } from 'react';
import ReactFlow from 'reactflow';
import { ForEachNodeCard } from './ForEachNodeCard';
import { SubWorkflowEditor } from './SubWorkflowEditor';

const nodeTypes = {
  ForEachNode: ForEachNodeCard,
  // ... 其他节点类型
};

export const MainCanvas = () => {
  const [editingForeachNode, setEditingForeachNode] = useState(null);
  
  // 处理双击 ForEachNode
  const handleNodeDoubleClick = (event, node) => {
    if (node.type === 'ForEachNode') {
      setEditingForeachNode(node);
    }
  };
  
  // 保存子工作流
  const handleSubWorkflowSave = (subWorkflow, resultNodeId, resultPortName) => {
    // 更新 ForEachNode 的配置
    updateNode(editingForeachNode.id, {
      ...editingForeachNode.data,
      subWorkflow,
      resultNodeId,
      resultPortName
    });
    
    // 关闭编辑器
    setEditingForeachNode(null);
  };
  
  return (
    <>
      {editingForeachNode ? (
        // 显示子工作流编辑器
        <SubWorkflowEditor
          foreachNodeId={editingForeachNode.id}
          initialSubWorkflow={editingForeachNode.data.subWorkflow}
          onSave={handleSubWorkflowSave}
          onCancel={() => setEditingForeachNode(null)}
        />
      ) : (
        // 显示主画布
        <ReactFlow
          nodeTypes={nodeTypes}
          onNodeDoubleClick={handleNodeDoubleClick}
        >
          <Controls />
          <Background />
        </ReactFlow>
      )}
    </>
  );
};
```

## 数据转换

### 从 API 格式转换到 ReactFlow 格式

```typescript
function toReactFlowFormat(
  subWorkflow: SubWorkflowDefinition
): { nodes: Node[]; edges: Edge[] } {
  const nodes = subWorkflow.nodes.map(node => ({
    id: node.id,
    type: node.type === 'ForEachItemNode' ? 'foreachItem' : 'custom',
    position: node.position || { x: 0, y: 0 },
    data: {
      label: node.type,
      nodeType: node.type,
      config: node.input_values
    }
  }));
  
  const edges = subWorkflow.connections.map(conn => ({
    id: `${conn.from_node}_${conn.from_port}_${conn.to_node}_${conn.to_port}`,
    source: conn.from_node,
    sourceHandle: conn.from_port,
    target: conn.to_node,
    targetHandle: conn.to_port
  }));
  
  return { nodes, edges };
}
```

### 从 ReactFlow 格式转换到 API 格式

```typescript
function toSubWorkflowFormat(
  nodes: Node[],
  edges: Edge[]
): SubWorkflowDefinition {
  return {
    nodes: nodes.map(node => ({
      type: node.data.nodeType,
      id: node.id,
      input_values: node.data.config || {},
      position: node.position
    })),
    connections: edges.map(edge => ({
      from_node: edge.source,
      from_port: edge.sourceHandle || '',
      to_node: edge.target,
      to_port: edge.targetHandle || ''
    }))
  };
}
```

## UI/UX 最佳实践

### 1. 面包屑导航

在子工作流编辑模式下显示导航路径：

```typescript
<div className="breadcrumb">
  <a onClick={() => goToMainCanvas()}>主工作流</a>
  <span> / </span>
  <span>ForEach 子工作流</span>
</div>
```

### 2. 结果节点高亮

当用户选择结果节点时，在画布上高亮显示：

```typescript
<Node
  className={classNames({
    'result-node': node.id === resultNodeId,
    'selectable': node.type !== 'ForEachItemNode'
  })}
/>
```

### 3. 实时验证

在用户编辑时提供实时反馈：

```typescript
useEffect(() => {
  if (resultNodeId && resultPortName) {
    validateSubWorkflow(subWorkflow, resultNodeId, resultPortName)
      .then(result => setValidation(result));
  }
}, [nodes, edges, resultNodeId, resultPortName]);
```

### 4. 自动布局

提供自动布局功能，帮助用户整理节点：

```typescript
const autoLayout = useCallback(() => {
  const layoutedNodes = calculateLayout(nodes, edges);
  setNodes(layoutedNodes);
}, [nodes, edges]);
```

### 5. 模板快速开始

提供模板选择器，让用户快速开始：

```typescript
<button onClick={() => loadTemplate('simple_text_processing')}>
  使用模板：简单文本处理
</button>
```

## 完整示例

查看以下文件获取完整实现：

1. **后端 API**: `app/api/foreach_editor.py`
2. **前端组件**: `docs/frontend_implementation_example.tsx`
3. **设计方案**: `docs/foreach_frontend_integration.md`

## 测试建议

### 1. 单元测试

```typescript
describe('SubWorkflowEditor', () => {
  it('should initialize with ForEachItemNode', () => {
    // 测试初始化
  });
  
  it('should validate subworkflow correctly', () => {
    // 测试验证
  });
  
  it('should serialize to correct format', () => {
    // 测试序列化
  });
});
```

### 2. 集成测试

```typescript
describe('ForEach Integration', () => {
  it('should save and load subworkflow', async () => {
    // 测试保存和加载
  });
  
  it('should update parent node after save', async () => {
    // 测试父节点更新
  });
});
```

## 常见问题

### Q: 如何处理嵌套的 ForEach？

A: 目前不支持在子工作流中使用 ForEachNode。后端 API 已经过滤掉了 ForEachNode。

### Q: 如何保存子工作流的布局？

A: 在序列化时保存 `position` 字段，加载时恢复：

```typescript
{
  type: "TextStripNode",
  id: "node_1",
  position: { x: 200, y: 300 }
}
```

### Q: 如何处理大型子工作流？

A: 提供缩放、平移、小地图等功能，ReactFlow 已内置这些功能。

### Q: 如何支持撤销/重做？

A: 使用状态管理库（如 Zustand）的时间旅行功能，或自己实现历史栈。

## 下一步

1. 根据后端 API 实现前端组件
2. 测试各种场景
3. 优化用户体验
4. 添加更多模板
5. 实现高级功能（自动布局、智能推荐等）

## 总结

通过可视化的子工作流编辑器，用户可以：

- ✅ 直观地创建和编辑子工作流
- ✅ 无需手写 JSON 配置
- ✅ 实时验证和反馈
- ✅ 快速使用模板开始
- ✅ 轻松管理复杂的 ForEach 逻辑

这大大降低了使用 ForEachNode 的门槛，提升了整体的用户体验！

