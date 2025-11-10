# ForEach 前端集成 - 简化方案

## 概述

本文档说明如何在现有前端中添加 ForEach 子工作流的可视化编辑功能。

## 已完成的工作

### 后端 API（已简化并集成）

在 `app/routers/workflow.py` 中添加了一个简洁的验证 API：

```
POST /v1/workflow/foreach/validate
```

**用途**: 验证子工作流配置是否正确

**请求**:
```json
{
  "nodes": [
    { "type": "ForEachItemNode", "id": "item_1" },
    { "type": "TextStripNode", "id": "strip_1", "input_values": {} }
  ],
  "connections": [
    {
      "from_node": "item_1",
      "from_port": "item",
      "to_node": "strip_1",
      "to_port": "text"
    }
  ],
  "result_node_id": "strip_1",
  "result_port_name": "text"
}
```

**响应**:
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

## 前端集成步骤

### Step 1: 添加 ForEach 节点类型识别

在 `CustomNode` 组件中，识别 ForEachNode 并添加特殊处理：

```tsx
// WorkflowEditor.tsx - CustomNode 组件
const CustomNode = ({ data, id, ... }: CustomNodeProps) => {
  const isForEachNode = data.type === 'ForEachNode';
  
  // ... 现有代码 ...
  
  return (
    <div className={`custom-node ${isForEachNode ? 'foreach-node' : ''}`}>
      {/* 现有的节点内容 */}
      
      {/* ForEach 专用按钮 */}
      {isForEachNode && (
        <button
          onClick={() => handleEditSubWorkflow(id)}
          className="edit-subworkflow-btn"
        >
          {data.subWorkflow ? '编辑子工作流 ✏️' : '配置子工作流 ➕'}
        </button>
      )}
      
      {/* ForEach 状态显示 */}
      {isForEachNode && data.subWorkflow && (
        <div className="subworkflow-status">
          ✓ {data.subWorkflow.nodes.length} 个节点
        </div>
      )}
    </div>
  );
};
```

### Step 2: 添加子工作流编辑模式

在 `WorkflowEditor` 组件中添加状态管理：

```tsx
// WorkflowEditor.tsx
const WorkflowEditor = ({ ... }: WorkflowEditorProps) => {
  // 现有状态...
  
  // 新增：子工作流编辑状态
  const [editingSubWorkflow, setEditingSubWorkflow] = useState<{
    nodeId: string;
    subWorkflow: any;
  } | null>(null);
  
  // 进入子工作流编辑
  const handleEditSubWorkflow = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    setEditingSubWorkflow({
      nodeId,
      subWorkflow: node.data.subWorkflow || {
        nodes: [
          { type: 'ForEachItemNode', id: 'foreach_item' }
        ],
        connections: []
      }
    });
  }, [nodes]);
  
  // 保存子工作流
  const handleSaveSubWorkflow = useCallback(async (
    subWorkflow: any,
    resultNodeId: string,
    resultPortName: string
  ) => {
    if (!editingSubWorkflow) return;
    
    // 验证子工作流
    try {
      const response = await api.validateSubWorkflow({
        nodes: subWorkflow.nodes,
        connections: subWorkflow.connections,
        result_node_id: resultNodeId,
        result_port_name: resultPortName
      });
      
      if (!response.valid) {
        alert(`验证失败: ${response.errors.join(', ')}`);
        return;
      }
      
      // 更新节点数据
      setNodes(nodes => nodes.map(node => 
        node.id === editingSubWorkflow.nodeId
          ? {
              ...node,
              data: {
                ...node.data,
                subWorkflow,
                resultNodeId,
                resultPortName
              }
            }
          : node
      ));
      
      // 关闭编辑器
      setEditingSubWorkflow(null);
      
    } catch (error) {
      alert(`验证失败: ${error}`);
    }
  }, [editingSubWorkflow, setNodes]);
  
  // 渲染
  return (
    <div>
      {editingSubWorkflow ? (
        // 子工作流编辑器
        <SubWorkflowEditor
          initialSubWorkflow={editingSubWorkflow.subWorkflow}
          onSave={handleSaveSubWorkflow}
          onCancel={() => setEditingSubWorkflow(null)}
        />
      ) : (
        // 主画布
        <ReactFlow nodes={nodes} edges={edges} ...>
          {/* 现有内容 */}
        </ReactFlow>
      )}
    </div>
  );
};
```

### Step 3: 创建子工作流编辑器组件

创建新文件 `frontend/src/components/SubWorkflowEditor.tsx`:

```tsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  useEdgesState,
  useNodesState,
} from 'reactflow';

interface SubWorkflowEditorProps {
  initialSubWorkflow: {
    nodes: any[];
    connections: any[];
  };
  onSave: (
    subWorkflow: any,
    resultNodeId: string,
    resultPortName: string
  ) => void;
  onCancel: () => void;
}

export const SubWorkflowEditor: React.FC<SubWorkflowEditorProps> = ({
  initialSubWorkflow,
  onSave,
  onCancel
}) => {
  // 转换为 ReactFlow 格式
  const initialNodes = initialSubWorkflow.nodes.map(node => ({
    id: node.id,
    type: 'default',
    position: { x: Math.random() * 400, y: Math.random() * 400 },
    data: { label: node.type, type: node.type }
  }));
  
  const initialEdges = initialSubWorkflow.connections.map((conn, i) => ({
    id: `e${i}`,
    source: conn.from_node,
    sourceHandle: conn.from_port,
    target: conn.to_node,
    targetHandle: conn.to_port
  }));
  
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [resultNodeId, setResultNodeId] = useState('');
  const [resultPortName, setResultPortName] = useState('');
  
  const onConnect = useCallback((params: any) => {
    setEdges(eds => addEdge(params, eds));
  }, [setEdges]);
  
  const handleSave = () => {
    // 转换回 API 格式
    const subWorkflow = {
      nodes: nodes.map(node => ({
        type: node.data.type,
        id: node.id,
        input_values: {}
      })),
      connections: edges.map(edge => ({
        from_node: edge.source,
        from_port: edge.sourceHandle || 'output',
        to_node: edge.target,
        to_port: edge.targetHandle || 'input'
      }))
    };
    
    onSave(subWorkflow, resultNodeId, resultPortName);
  };
  
  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 工具栏 */}
      <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #ddd' }}>
        <span style={{ marginRight: '20px', fontWeight: 'bold' }}>子工作流编辑器</span>
        
        <label style={{ marginRight: '10px' }}>结果节点:</label>
        <select 
          value={resultNodeId} 
          onChange={e => setResultNodeId(e.target.value)}
          style={{ marginRight: '10px' }}
        >
          <option value="">选择...</option>
          {nodes.filter(n => n.data.type !== 'ForEachItemNode').map(node => (
            <option key={node.id} value={node.id}>{node.id}</option>
          ))}
        </select>
        
        <label style={{ marginRight: '10px' }}>输出端口:</label>
        <input 
          value={resultPortName} 
          onChange={e => setResultPortName(e.target.value)}
          placeholder="例如: text"
          style={{ marginRight: '20px' }}
        />
        
        <button onClick={onCancel} style={{ marginRight: '10px' }}>取消</button>
        <button onClick={handleSave} disabled={!resultNodeId || !resultPortName}>
          保存并返回
        </button>
      </div>
      
      {/* 画布 */}
      <div style={{ flex: 1 }}>
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
    </div>
  );
};
```

### Step 4: 在 API 服务中添加验证方法

在 `frontend/src/services/api.ts` 中添加：

```typescript
// api.ts
export const api = {
  // 现有方法...
  
  // 验证子工作流
  validateSubWorkflow: async (request: {
    nodes: any[];
    connections: any[];
    result_node_id: string;
    result_port_name: string;
  }) => {
    const response = await fetch(`${BASE_URL}/v1/workflow/foreach/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error('Validation failed');
    }
    
    return response.json();
  }
};
```

### Step 5: 添加样式

在 `App.css` 或相应的样式文件中添加：

```css
/* ForEach 节点样式 */
.foreach-node {
  border: 2px solid #6366f1 !important;
}

.edit-subworkflow-btn {
  width: 100%;
  padding: 6px 12px;
  margin-top: 8px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.edit-subworkflow-btn:hover {
  background: #4f46e5;
}

.subworkflow-status {
  margin-top: 4px;
  padding: 4px 8px;
  background: #d1fae5;
  color: #065f46;
  border-radius: 4px;
  font-size: 11px;
  text-align: center;
}
```

## 使用流程

1. **添加 ForEachNode**: 用户从节点选择器中拖拽 ForEachNode 到画布
2. **配置子工作流**: 点击 ForEachNode 上的"配置子工作流"按钮
3. **编辑子工作流**: 
   - 自动添加 ForEachItemNode 作为起点
   - 用户添加其他节点和连接
   - 选择结果节点和输出端口
4. **保存**: 点击"保存并返回"，自动验证并更新 ForEachNode 配置
5. **执行**: ForEachNode 会使用配置的子工作流处理每个项目

## 数据格式

### ForEachNode 节点数据

```json
{
  "id": "foreach_1",
  "type": "ForEachNode",
  "data": {
    "type": "ForEachNode",
    "label": "ForEach",
    "subWorkflow": {
      "nodes": [...],
      "connections": [...]
    },
    "resultNodeId": "strip_1",
    "resultPortName": "text",
    "config": {
      "parallel": false,
      "continue_on_error": true
    }
  }
}
```

### 保存到后端的格式

```json
{
  "nodes": [
    {
      "id": "foreach_1",
      "type": "ForEachNode",
      "position": { "x": 100, "y": 100 },
      "input_values": {
        "sub_workflow": {
          "nodes": [...],
          "connections": [...]
        },
        "result_node_id": "strip_1",
        "result_port_name": "text"
      }
    }
  ]
}
```

## 最小化实现（MVP）

如果想快速实现，可以简化为：

1. **不用独立的子工作流编辑器**，而是用 JSON 编辑器让用户直接编辑配置
2. **使用现有的 NodePropertiesDialog**，添加一个特殊的"子工作流配置"字段
3. **提供模板**，让用户从预定义的模板开始

示例：

```tsx
// 在 NodePropertiesDialog 中
{selectedNode.data.type === 'ForEachNode' && (
  <div>
    <label>子工作流配置 (JSON):</label>
    <textarea
      value={JSON.stringify(selectedNode.data.subWorkflow, null, 2)}
      onChange={(e) => {
        try {
          const subWorkflow = JSON.parse(e.target.value);
          updateNodeData({ subWorkflow });
        } catch (error) {
          // 显示错误
        }
      }}
      rows={20}
      style={{ width: '100%', fontFamily: 'monospace' }}
    />
    
    <button onClick={loadTemplate}>
      使用模板：简单文本处理
    </button>
  </div>
)}
```

## 总结

这个方案：

- ✅ **简化了 API** - 只添加了一个验证接口
- ✅ **最小化修改** - 主要在现有的 WorkflowEditor 中添加功能
- ✅ **渐进式** - 可以先实现 JSON 编辑，再逐步升级到可视化编辑器
- ✅ **复用现有组件** - 子工作流编辑器可以复用现有的 ReactFlow 组件

建议先实现 MVP（JSON 编辑），验证功能可用后，再逐步实现可视化的子工作流编辑器。

