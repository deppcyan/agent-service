# ForEach Node 使用指南

## 概述

ForEach 节点系列为工作流提供了**动态执行**能力，允许对列表中的每个项目执行相同的处理逻辑。这突破了静态工作流的限制，实现了真正的批量处理和迭代执行。

## 三种 ForEach 节点类型

### 1. SimpleForEachNode（推荐）

**最简单、最实用的选择**

- 对列表中的每个项目执行指定类型的节点
- API 简洁，易于使用
- 支持并行和串行执行
- 适合 80% 的使用场景

```python
# 示例：对文本列表进行批量处理
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": ["text1", "text2", "text3"],
    "node_type": "TextStripNode",        # 要执行的节点类型
    "item_port_name": "text",            # 输入端口名称
    "result_port_name": "text",          # 输出端口名称
    "parallel": True,                     # 并行执行
    "continue_on_error": True            # 出错继续
}
```

#### 输入端口

| 端口名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `items` | array | 是 | 要处理的项目列表 |
| `node_type` | string | 是 | 节点类名（如 "TextStripNode"） |
| `item_port_name` | string | 否 | 将项目传入的端口名（默认："text"） |
| `result_port_name` | string | 否 | 收集结果的端口名（默认："result"） |
| `node_config` | object | 否 | 节点的额外配置参数 |
| `parallel` | boolean | 否 | 是否并行执行（默认：false） |
| `continue_on_error` | boolean | 否 | 出错是否继续（默认：true） |
| `max_workers` | number | 否 | 最大并发数（仅并行模式） |

#### 输出端口

| 端口名 | 类型 | 说明 |
|--------|------|------|
| `results` | array | 所有成功的结果列表 |
| `success_count` | number | 成功处理的数量 |
| `error_count` | number | 失败的数量 |
| `errors` | array | 错误详情列表 |

### 2. BatchProcessNode

**大数据集批量处理**

- 将项目分批处理
- 更好的资源管理
- 支持批间和批内并行控制
- 适合处理大量数据或有速率限制的场景

```python
# 示例：分批处理大量数据
batch_node = BatchProcessNode()
batch_node.input_values = {
    "items": large_list,                  # 大量数据
    "node_type": "TextStripNode",
    "batch_size": 10,                     # 每批 10 个
    "parallel_batches": False,            # 批次串行
    "parallel_within_batch": True         # 批内并行
}
```

#### 输入端口

| 端口名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `items` | array | 是 | 要处理的项目列表 |
| `node_type` | string | 是 | 节点类名 |
| `batch_size` | number | 否 | 批次大小（默认：10） |
| `item_port_name` | string | 否 | 输入端口名 |
| `result_port_name` | string | 否 | 输出端口名 |
| `node_config` | object | 否 | 节点配置 |
| `parallel_batches` | boolean | 否 | 批次间并行（默认：false） |
| `parallel_within_batch` | boolean | 否 | 批次内并行（默认：true） |

#### 输出端口

| 端口名 | 类型 | 说明 |
|--------|------|------|
| `results` | array | 所有结果 |
| `batch_count` | number | 批次总数 |
| `success_count` | number | 成功数量 |
| `error_count` | number | 失败数量 |
| `errors` | array | 错误列表 |

### 3. ForEachNode（高级）

**完整子工作流执行**

- 为每个项目执行完整的子工作流
- 最大灵活性
- 可以构建复杂的多步处理流程
- 适合需要多个节点协作处理每个项目的场景

```python
# 示例：执行子工作流
sub_workflow = {
    "nodes": [
        {"type": "ForEachItemNode", "id": "input"},
        {"type": "TextStripNode", "id": "strip"},
        {"type": "TextReplaceNode", "id": "replace"}
    ],
    "connections": [
        {"from_node": "input", "from_port": "item", 
         "to_node": "strip", "to_port": "text"},
        {"from_node": "strip", "from_port": "text",
         "to_node": "replace", "to_port": "text"}
    ]
}

foreach_node = ForEachNode()
foreach_node.input_values = {
    "items": ["item1", "item2"],
    "sub_workflow": sub_workflow,
    "result_node_id": "replace",          # 收集哪个节点的结果
    "result_port_name": "replaced_text"   # 收集哪个端口
}
```

## 使用场景

### 场景 1: 批量文本处理

**需求**: 清理用户输入的文本列表

```python
# 使用 SimpleForEachNode
graph = WorkflowGraph()

# 输入节点
input_node = TextToListNode()
input_node.input_values = {
    "text": '["  text1  ", "  text2  "]',
    "format": "json"
}
graph.add_node(input_node)

# ForEach 清理
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "node_type": "TextStripNode",
    "item_port_name": "text",
    "result_port_name": "text",
    "parallel": True
}
graph.add_node(foreach_node)

# 连接
graph.connect(input_node.node_id, "list", 
              foreach_node.node_id, "items")

# 执行
executor = WorkflowExecutor(graph)
results = await executor.execute()
```

### 场景 2: 批量 API 调用

**需求**: 对多个问题调用 LLM API

```python
# 使用 SimpleForEachNode 调用模型
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": ["问题1", "问题2", "问题3"],
    "node_type": "ModelRequestNode",
    "item_port_name": "prompt",
    "result_port_name": "response",
    "parallel": True,
    "max_workers": 3,  # 限制并发，避免超过 API 速率限制
    "node_config": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}
```

### 场景 3: 数据转换管道

**需求**: 多步骤转换每个数据项

```python
# 使用 ForEachNode 执行复杂子工作流
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
    "items": raw_data_list,
    "sub_workflow": sub_workflow,
    "result_node_id": "parse",
    "result_port_name": "dict"
}
```

### 场景 4: 大数据集分批处理

**需求**: 处理 10000 条记录，每批 100 条

```python
# 使用 BatchProcessNode
batch_node = BatchProcessNode()
batch_node.input_values = {
    "items": large_dataset,  # 10000 条
    "node_type": "DataProcessNode",
    "batch_size": 100,
    "parallel_batches": False,      # 批次串行，避免内存溢出
    "parallel_within_batch": True,  # 批内并行，提高速度
    "item_port_name": "data",
    "result_port_name": "processed"
}
```

## 性能优化建议

### 1. 并行 vs 串行

**并行执行**（parallel=True）:
- ✅ 优势：速度快，充分利用资源
- ❌ 劣势：内存占用高，可能超出速率限制
- 🎯 适用：I/O 密集型任务（API 调用、文件读取）

**串行执行**（parallel=False）:
- ✅ 优势：内存占用低，可控的资源使用
- ❌ 劣势：速度慢
- 🎯 适用：CPU 密集型任务，内存有限，需要保证顺序

### 2. 批次大小选择

```python
# 小批次（10-50）：
# - 内存占用低
# - 适合大对象处理
# - 进度反馈快

batch_size = 20

# 大批次（100-1000）：
# - 吞吐量高
# - 适合小对象处理
# - 减少批次切换开销

batch_size = 500
```

### 3. 并发控制

```python
# 限制并发数，避免超过 API 速率限制
foreach_node.input_values = {
    "parallel": True,
    "max_workers": 5,  # 最多同时处理 5 个
    # ...
}
```

### 4. 错误处理策略

```python
# 策略 1: 继续执行（默认）
# 适合：数据清洗、最大化处理量
"continue_on_error": True

# 策略 2: 遇错即停
# 适合：严格的数据处理、关键任务
"continue_on_error": False
```

## 高级用法

### 1. 嵌套 ForEach

```python
# 外层 ForEach 处理类别
outer_foreach = SimpleForEachNode()
outer_foreach.input_values = {
    "items": ["category1", "category2"],
    "node_type": "CategoryProcessNode",
    # ...
}

# 内层 ForEach 处理每个类别的项目
# 在 CategoryProcessNode 内部使用另一个 ForEach
```

### 2. 动态配置

```python
# 根据项目类型动态选择处理节点
foreach_node.input_values = {
    "items": mixed_items,
    "node_type": "DynamicProcessNode",  # 可根据输入选择处理方式
    "node_config": {
        "strategy": "auto",
        "fallback": "default_handler"
    }
}
```

### 3. 结果聚合

```python
# ForEach 处理后，使用聚合节点汇总
graph.connect(foreach_node.node_id, "results",
              aggregate_node.node_id, "items")
```

## 常见问题

### Q1: 如何访问当前项目的索引？

**A**: 使用 `ForEachItemNode`（仅在子工作流中）

```python
# 在子工作流中
{"type": "ForEachItemNode", "id": "input"}
# 输出端口：item（项目值）, index（索引）
```

### Q2: 如何在处理过程中保存中间结果？

**A**: 使用子工作流并指定要收集的节点

```python
foreach_node.input_values = {
    "sub_workflow": workflow_def,
    "result_node_id": "final_node",  # 指定收集哪个节点的结果
}
```

### Q3: 如何限制 API 调用速率？

**A**: 使用 `max_workers` 或批处理

```python
# 方法 1: 限制并发数
"parallel": True,
"max_workers": 3

# 方法 2: 使用批处理 + 批次串行
"parallel_batches": False,
"parallel_within_batch": True,
"batch_size": 10
```

### Q4: 如何处理不同类型的错误？

**A**: 检查 errors 输出端口

```python
results = await executor.execute()
errors = results[foreach_node.node_id]["errors"]

for error in errors:
    print(f"Item {error['index']}: {error['error']}")
    # 根据错误类型进行处理
```

### Q5: 能否在 ForEach 中使用其他 ForEach？

**A**: 可以，但要注意性能

```python
# 可以嵌套使用，但要注意：
# - 外层串行 + 内层并行（推荐）
# - 避免两层都并行（资源消耗大）
outer_foreach.input_values["parallel"] = False
inner_foreach.input_values["parallel"] = True
```

## 最佳实践

### ✅ 推荐做法

1. **优先使用 SimpleForEachNode**：覆盖大多数场景
2. **合理设置并发**：根据任务类型选择并行/串行
3. **添加错误处理**：检查 error_count 和 errors
4. **监控资源使用**：大数据集使用批处理
5. **记录日志**：ForEach 会自动记录执行信息

### ❌ 避免做法

1. **无限制并行**：容易耗尽资源
2. **过大的批次**：可能导致内存溢出
3. **忽略错误**：不检查 error_count
4. **过度嵌套**：降低可读性和性能
5. **同步阻塞**：确保所有节点都是异步的

## 示例代码

完整示例请参考 `examples/foreach_node_examples.py`

```bash
# 运行示例
python examples/foreach_node_examples.py
```

## 总结

ForEach 节点系列为工作流带来了强大的动态执行能力：

- **SimpleForEachNode**: 简单直接，适合大多数场景
- **BatchProcessNode**: 批量处理，适合大数据集
- **ForEachNode**: 完整子工作流，适合复杂场景

选择合适的节点类型，配置好并行策略和错误处理，就能高效处理各种批量任务！

