# ForEach Node 设计文档

## 背景

当前 `/app/workflow` 的执行是静态的，创建执行图之后就按照静态顺序执行。为了实现动态执行能力，我们设计并实现了 ForEach 节点系列，使得工作流能够对列表中的每个项目进行迭代处理。

## 设计目标

1. **动态执行**: 能够在运行时动态创建和执行节点实例
2. **结果收集**: 每次循环都能将结果存储起来
3. **完整返回**: 执行完成后返回整个结果列表
4. **错误处理**: 支持灵活的错误处理策略
5. **性能优化**: 支持并行执行和批量处理
6. **易用性**: 提供简单和高级两种使用方式

## 架构设计

### 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                     ForEach Node 架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  输入: items = [item1, item2, item3, ...]                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  For each item in items:                           │    │
│  │    1. 创建节点实例 / 子工作流                        │    │
│  │    2. 将 item 注入到节点输入                         │    │
│  │    3. 执行节点/工作流                                │    │
│  │    4. 收集结果                                       │    │
│  │    5. 处理错误（可选继续/停止）                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  输出: results = [result1, result2, result3, ...]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 三层设计

我们实现了三种不同复杂度的 ForEach 节点，以满足不同的使用场景：

#### 1. SimpleForEachNode（简单层）

**设计理念**: 80% 的使用场景只需要对列表中的每个项目执行同一类型的节点

```python
# 使用方式
SimpleForEachNode({
    "items": [...],
    "node_type": "NodeClassName",  # 字符串，节点类名
    "item_port_name": "input",      # 将项目传入哪个端口
    "result_port_name": "output"    # 从哪个端口收集结果
})
```

**实现原理**:
1. 从 NodeRegistry 动态创建节点实例
2. 为每个项目创建独立的节点实例
3. 执行并收集结果
4. 支持并行和串行执行

**优势**:
- API 简洁，易于使用
- 无需定义复杂的子工作流
- 性能开销小

**适用场景**:
- 批量文本处理
- 批量 API 调用
- 简单的数据转换

#### 2. BatchProcessNode（批处理层）

**设计理念**: 大数据集需要分批处理以管理资源

```python
# 使用方式
BatchProcessNode({
    "items": [...],
    "batch_size": 10,                    # 每批处理多少个
    "parallel_batches": False,           # 批次间并行
    "parallel_within_batch": True        # 批次内并行
})
```

**实现原理**:
1. 将 items 切分为固定大小的批次
2. 可配置批次间和批次内的并行策略
3. 逐批处理并收集结果

**优势**:
- 更好的内存管理
- 适合处理大数据集
- 灵活的并行策略
- 进度可追踪

**适用场景**:
- 大量数据处理（>1000 项）
- API 速率限制场景
- 内存受限环境

#### 3. ForEachNode（高级层）

**设计理念**: 某些场景需要为每个项目执行完整的多步骤工作流

```python
# 使用方式
ForEachNode({
    "items": [...],
    "sub_workflow": {
        "nodes": [...],        # 子工作流的节点定义
        "connections": [...]   # 子工作流的连接定义
    },
    "result_node_id": "node_id",      # 收集哪个节点的结果
    "result_port_name": "output"      # 收集哪个端口
})
```

**实现原理**:
1. 为每个项目构建完整的 WorkflowGraph
2. 使用 ForEachItemNode 作为子工作流的输入点
3. 通过 WorkflowExecutor 执行子工作流
4. 从指定节点收集结果

**优势**:
- 最大灵活性
- 支持复杂的多步骤处理
- 可以使用任意节点组合

**适用场景**:
- 复杂的数据处理管道
- 需要多个节点协作的场景
- 条件分支处理

## 技术实现

### 1. 动态节点创建

```python
# 通过 NodeRegistry 动态创建节点
from app.workflow.registry import node_registry

node = node_registry.create_node(node_type, node_id)
node.input_values[port_name] = item
result = await node.process()
```

### 2. 并行执行

```python
# 使用 asyncio.gather 实现并行
import asyncio

tasks = [self._execute_single_item(item, i) for i, item in enumerate(items)]
results = await asyncio.gather(*tasks)

# 使用 Semaphore 限制并发
semaphore = asyncio.Semaphore(max_workers)
async with semaphore:
    result = await process_item(item)
```

### 3. 结果收集

每个迭代返回统一的结果结构：

```python
{
    "success": bool,      # 是否成功
    "result": Any,        # 结果值
    "error": str,         # 错误信息（如果失败）
    "index": int,         # 项目索引
    "item": Any          # 原始项目
}
```

最终输出：

```python
{
    "results": [r1, r2, r3, ...],     # 所有成功的结果
    "success_count": int,              # 成功数量
    "error_count": int,                # 失败数量
    "errors": [                        # 错误详情
        {"index": 0, "item": ..., "error": "..."},
        ...
    ]
}
```

### 4. 子工作流执行

ForEachNode 的核心实现：

```python
async def _execute_iteration(self, item, index, sub_workflow_def, ...):
    # 1. 构建子工作流图
    graph = self._build_sub_workflow(sub_workflow_def)
    
    # 2. 注入当前项目
    for node in graph.nodes.values():
        if "foreach_item" in node.input_ports:
            node.input_values["foreach_item"] = item
        if "foreach_index" in node.input_ports:
            node.input_values["foreach_index"] = index
    
    # 3. 执行子工作流
    executor = WorkflowExecutor(graph, task_id=self.task_id)
    await executor.execute()
    
    # 4. 收集结果
    node_results = executor.get_node_result(result_node_id)
    result_value = node_results[result_port_name]
    
    return result_value
```

### 5. 错误处理

两种错误处理策略：

```python
if not result.success and not continue_on_error:
    break  # 遇到错误立即停止

# 或者
if not result.success:
    errors.append(error_info)
    continue  # 记录错误但继续处理
```

## 性能考虑

### 并行执行的权衡

| 模式 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| 串行 | 内存低、可控 | 速度慢 | CPU 密集型 |
| 并行 | 速度快、高吞吐 | 内存高、资源竞争 | I/O 密集型 |
| 限制并发 | 平衡速度和资源 | 需要调优 | API 调用 |

### 批处理策略

```python
# 小批次（10-50）
+ 内存占用低
+ 进度反馈快
- 批次切换开销

# 大批次（100-1000）
+ 吞吐量高
+ 减少开销
- 内存占用高
- 进度反馈慢
```

### 内存管理

```python
# 避免在内存中累积所有结果
# 方案：流式处理 + 批量写入
async def process_large_dataset():
    batch_node = BatchProcessNode()
    batch_node.input_values = {
        "batch_size": 100,
        "parallel_batches": False,  # 避免内存峰值
        "parallel_within_batch": True
    }
```

## 扩展性

### 1. 自定义节点支持

ForEach 节点可以执行任何注册在 NodeRegistry 中的节点：

```python
# 注册自定义节点
node_registry.register_node(MyCustomNode, "custom")

# 在 ForEach 中使用
foreach_node.input_values = {
    "node_type": "MyCustomNode",
    ...
}
```

### 2. 嵌套 ForEach

支持 ForEach 嵌套使用：

```python
# 外层 ForEach 处理类别
outer_foreach = SimpleForEachNode()

# 内层 ForEach 处理每个类别的项目
inner_foreach = SimpleForEachNode()
# 在 CategoryProcessNode 内部使用
```

### 3. 条件执行

结合条件节点实现条件迭代：

```python
sub_workflow = {
    "nodes": [
        {"type": "ForEachItemNode", "id": "input"},
        {"type": "ConditionNode", "id": "check"},
        {"type": "ProcessNode", "id": "process"}
    ]
}
```

## 使用示例

### 示例 1: 简单批量处理

```python
# 清理文本列表
graph = WorkflowGraph()

input_node = TextToListNode()
input_node.input_values = {"text": '["  a  ", "  b  "]', "format": "json"}
graph.add_node(input_node)

foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "node_type": "TextStripNode",
    "item_port_name": "text",
    "result_port_name": "text"
}
graph.add_node(foreach_node)

graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")

executor = WorkflowExecutor(graph)
results = await executor.execute()
# results: ["a", "b"]
```

### 示例 2: 批量 API 调用

```python
# 对多个问题调用 LLM
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": ["问题1", "问题2", "问题3"],
    "node_type": "ModelRequestNode",
    "item_port_name": "prompt",
    "result_port_name": "response",
    "parallel": True,
    "max_workers": 3,  # 限制并发
    "node_config": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}
```

### 示例 3: 复杂数据管道

```python
# 多步骤处理每个项目
sub_workflow = {
    "nodes": [
        {"type": "ForEachItemNode", "id": "input"},
        {"type": "TextStripNode", "id": "clean"},
        {"type": "TextReplaceNode", "id": "normalize"},
        {"type": "TextToDictNode", "id": "parse"}
    ],
    "connections": [
        {"from_node": "input", "from_port": "item",
         "to_node": "clean", "to_port": "text"},
        {"from_node": "clean", "from_port": "text",
         "to_node": "normalize", "to_port": "text"},
        {"from_node": "normalize", "from_port": "replaced_text",
         "to_node": "parse", "to_port": "text"}
    ]
}

foreach_node = ForEachNode()
foreach_node.input_values = {
    "items": raw_data,
    "sub_workflow": sub_workflow,
    "result_node_id": "parse",
    "result_port_name": "dict"
}
```

## 测试

测试覆盖：

1. **单元测试**: 测试每个 ForEach 节点的基本功能
2. **集成测试**: 测试与其他节点的组合使用
3. **性能测试**: 测试并行执行和批处理性能
4. **错误测试**: 测试错误处理和恢复

运行测试：

```bash
pytest tests/test_foreach_node.py -v
```

## 文档

- **使用指南**: `docs/foreach_node_guide.md`
- **示例代码**: `examples/foreach_node_examples.py`
- **设计文档**: `docs/foreach_node_design.md` (本文档)

## 总结

ForEach 节点系列成功实现了工作流的动态执行能力：

✅ **实现目标**:
- 动态创建和执行节点实例
- 完整的结果收集机制
- 灵活的错误处理
- 并行和批处理支持
- 三层 API 设计满足不同需求

✅ **技术特点**:
- 基于现有的 WorkflowNode 和 WorkflowGraph 架构
- 利用 asyncio 实现高效并行
- 通过 NodeRegistry 实现动态节点创建
- 完善的日志记录和错误追踪

✅ **易用性**:
- SimpleForEachNode 覆盖大多数场景
- 清晰的 API 设计
- 丰富的示例和文档
- 完整的类型提示和注释

这个设计既保持了与现有系统的兼容性，又提供了强大的动态执行能力，为工作流系统带来了质的提升！

