# ForEach Node 快速参考

## 一分钟快速开始

```python
from app.workflow.nodes.foreach_simple import SimpleForEachNode

# 创建 ForEach 节点
foreach = SimpleForEachNode()
foreach.input_values = {
    "items": ["  hello  ", "  world  "],  # 输入列表
    "node_type": "TextStripNode",         # 节点类名
    "item_port_name": "text",             # 输入端口
    "result_port_name": "text"            # 输出端口
}

# 执行
result = await foreach.process()
# result["results"] = ["hello", "world"]
```

## SimpleForEachNode API

### 输入端口

| 端口 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `items` | array | ✓ | - | 要处理的列表 |
| `node_type` | string | ✓ | - | 节点类名 |
| `item_port_name` | string | | "text" | 输入端口名 |
| `result_port_name` | string | | "result" | 输出端口名 |
| `node_config` | object | | {} | 额外配置 |
| `parallel` | boolean | | false | 并行执行 |
| `continue_on_error` | boolean | | true | 出错继续 |
| `max_workers` | number | | - | 最大并发数 |

### 输出端口

| 端口 | 类型 | 说明 |
|------|------|------|
| `results` | array | 所有结果 |
| `success_count` | number | 成功数量 |
| `error_count` | number | 失败数量 |
| `errors` | array | 错误列表 |

## 常用模式

### 模式 1: 串行执行

```python
{
    "items": [1, 2, 3],
    "node_type": "ProcessNode",
    "parallel": False  # 串行，按顺序执行
}
```

### 模式 2: 并行执行

```python
{
    "items": [1, 2, 3],
    "node_type": "ProcessNode",
    "parallel": True  # 并行，快速执行
}
```

### 模式 3: 限制并发

```python
{
    "items": list(range(100)),
    "node_type": "APINode",
    "parallel": True,
    "max_workers": 5  # 最多 5 个并发
}
```

### 模式 4: 带配置

```python
{
    "items": ["text1", "text2"],
    "node_type": "TextReplaceNode",
    "node_config": {      # 额外配置
        "old_text": "o",
        "new_text": "0"
    }
}
```

### 模式 5: 遇错即停

```python
{
    "items": [1, 2, 3],
    "node_type": "CriticalNode",
    "continue_on_error": False  # 遇到错误立即停止
}
```

## ForEachNode API（高级）

### 输入端口

| 端口 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `items` | array | ✓ | 要处理的列表 |
| `sub_workflow` | object | ✓ | 子工作流定义 |
| `result_node_id` | string | ✓ | 结果节点 ID |
| `result_port_name` | string | | 结果端口名 |
| `parallel` | boolean | | 并行执行 |
| `continue_on_error` | boolean | | 出错继续 |
| `max_iterations` | number | | 最大迭代数 |

### 子工作流定义

```python
sub_workflow = {
    "nodes": [
        {
            "type": "ForEachItemNode",  # 接收当前项
            "id": "input"
        },
        {
            "type": "ProcessNode",
            "id": "process"
        }
    ],
    "connections": [
        {
            "from_node": "input",
            "from_port": "item",
            "to_node": "process",
            "to_port": "input"
        }
    ]
}
```

## 性能指南

| 数据量 | 推荐配置 |
|--------|----------|
| < 10 | 串行 |
| 10-100 | 并行（无限制） |
| 100-1000 | 并行 + max_workers=10 |
| > 1000 | 并行 + max_workers=20-50 |

## 错误处理

### 检查结果

```python
result = await foreach.process()

if result["error_count"] > 0:
    print(f"有 {result['error_count']} 个失败")
    for error in result["errors"]:
        print(f"  索引 {error['index']}: {error['error']}")
```

### 两种策略

| 策略 | 配置 | 适用场景 |
|------|------|----------|
| 继续执行 | `continue_on_error=True` | 数据清洗，最大化处理量 |
| 遇错即停 | `continue_on_error=False` | 关键任务，严格处理 |

## 实际示例

### 批量文本处理

```python
from app.workflow.base import WorkflowGraph
from app.workflow.executor import WorkflowExecutor
from app.workflow.nodes.foreach_simple import SimpleForEachNode
from app.workflow.nodes.text_process import TextToListNode

graph = WorkflowGraph()

# 输入
input_node = TextToListNode()
input_node.input_values = {
    "text": '["  a  ", "  b  ", "  c  "]',
    "format": "json"
}
graph.add_node(input_node)

# ForEach
foreach = SimpleForEachNode()
foreach.input_values = {
    "node_type": "TextStripNode",
    "item_port_name": "text",
    "result_port_name": "text"
}
graph.add_node(foreach)

# 连接
graph.connect(input_node.node_id, "list", foreach.node_id, "items")

# 执行
executor = WorkflowExecutor(graph)
results = await executor.execute()
# 结果: ["a", "b", "c"]
```

### 批量 API 调用

```python
foreach = SimpleForEachNode()
foreach.input_values = {
    "items": ["问题1", "问题2", "问题3"],
    "node_type": "ModelRequestNode",
    "item_port_name": "prompt",
    "result_port_name": "response",
    "parallel": True,
    "max_workers": 3,
    "node_config": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}

result = await foreach.process()
# result["results"] = [response1, response2, response3]
```

## 常见问题速查

| 问题 | 解决方案 |
|------|----------|
| 如何限制 API 速率？ | 使用 `max_workers` |
| 如何处理大数据集？ | 使用 `max_workers` 限制并发 |
| 如何获取当前索引？ | 使用 ForEachItemNode（高级） |
| 如何跳过某些项？ | 在 node_config 中设置条件 |
| 如何保证顺序？ | 使用 `parallel=False` |

## 文件位置

```
examples/simple_foreach_demo.py      # 快速演示
examples/foreach_node_examples.py    # 完整示例
docs/foreach_node_guide.md           # 详细指南
FOREACH_NODE_README.md               # 完整文档
```

## 运行示例

```bash
# 快速入门（3 个示例）
python examples/simple_foreach_demo.py

# 完整示例（5 个示例）
python examples/foreach_node_examples.py

# 运行测试
pytest tests/test_foreach_node.py -v
```

---

**提示**: 90% 的场景使用 `SimpleForEachNode` 即可，只有需要多步骤处理时才使用 `ForEachNode`。

