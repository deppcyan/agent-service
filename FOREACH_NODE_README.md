# ForEach Node - 动态工作流执行

## 📋 概述

ForEach Node 为 `/app/workflow` 提供了**动态执行**能力，突破了静态工作流的限制。现在你可以：

- ✅ 对列表中的每个项目执行相同的处理逻辑
- ✅ 每次循环自动存储结果
- ✅ 执行完成后返回完整的结果列表
- ✅ 支持并行和串行执行
- ✅ 灵活的错误处理策略
- ✅ 批量处理大数据集

## 🚀 快速开始

### 最简单的例子

```python
from app.workflow.nodes.foreach_simple import SimpleForEachNode

# 对文本列表进行批量清理
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": ["  hello  ", "  world  "],  # 输入列表
    "node_type": "TextStripNode",         # 执行的节点类型
    "item_port_name": "text",             # 输入端口
    "result_port_name": "text",           # 输出端口
}

result = await foreach_node.process()
# result["results"] = ["hello", "world"]
```

### 运行演示

```bash
# 快速入门演示（3 个简单示例）
python examples/simple_foreach_demo.py

# 完整示例（6 个详细示例）
python examples/foreach_node_examples.py
```

## 📦 文件结构

```
agent-service/
├── app/workflow/nodes/
│   ├── foreach_node.py           # ForEachNode (高级，完整子工作流)
│   ├── foreach_simple.py         # SimpleForEachNode & BatchProcessNode
│   └── ...
├── examples/
│   ├── simple_foreach_demo.py    # 快速入门演示 (推荐先看这个!)
│   └── foreach_node_examples.py  # 完整示例
├── docs/
│   ├── foreach_node_guide.md     # 详细使用指南
│   └── foreach_node_design.md    # 设计文档
├── tests/
│   └── test_foreach_node.py      # 单元测试
└── FOREACH_NODE_README.md        # 本文档
```

## 🎯 两种 ForEach 节点

### 1. SimpleForEachNode ⭐ (推荐)

**最常用，覆盖 90% 的场景**

```python
SimpleForEachNode({
    "items": [1, 2, 3],           # 要处理的列表
    "node_type": "TextStripNode", # 节点类名
    "parallel": True,              # 并行执行
    "max_workers": 5              # 最大并发数
})
```

**适用场景**:
- 批量文本处理
- 批量 API 调用
- 简单数据转换
- 大多数日常任务

### 2. ForEachNode (高级)

**执行完整的子工作流**

```python
ForEachNode({
    "items": [...],
    "sub_workflow": {              # 完整的工作流定义
        "nodes": [...],
        "connections": [...]
    },
    "result_node_id": "node_id"    # 收集哪个节点的结果
})
```

**适用场景**:
- 多步骤处理每个项目
- 复杂的数据管道
- 需要多个节点协作

## 💡 使用示例

### 示例 1: 批量文本清理

```python
# 清理用户输入的文本列表
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
    "parallel": True  # 并行执行更快
}
graph.add_node(foreach_node)

# 连接并执行
graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
executor = WorkflowExecutor(graph)
results = await executor.execute()

# 结果: ["text1", "text2"]
```

### 示例 2: 批量 API 调用（带速率限制）

```python
# 对多个问题调用 LLM，限制并发避免超速
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": ["问题1", "问题2", "问题3"],
    "node_type": "ModelRequestNode",
    "item_port_name": "prompt",
    "result_port_name": "response",
    "parallel": True,
    "max_workers": 3,  # 🔥 限制最多 3 个并发
    "node_config": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}
```

### 示例 3: 大数据集处理（使用并发限制）

```python
# 处理大量数据，限制并发数避免资源耗尽
foreach_node = SimpleForEachNode()
foreach_node.input_values = {
    "items": large_dataset,  # 大量数据
    "node_type": "DataProcessNode",
    "parallel": True,
    "max_workers": 10,          # 限制最多 10 个并发
    "continue_on_error": True
}
```

## 🔧 核心功能

### 1. 结果收集

每次循环的结果都会被收集：

```python
result = {
    "results": [r1, r2, r3, ...],  # 所有成功的结果
    "success_count": 3,              # 成功数量
    "error_count": 1,                # 失败数量
    "errors": [                      # 错误详情
        {"index": 2, "item": "...", "error": "..."}
    ]
}
```

### 2. 错误处理

两种策略：

```python
# 策略 1: 继续执行（默认）
"continue_on_error": True   # 出错继续，最大化处理量

# 策略 2: 遇错即停
"continue_on_error": False  # 遇到第一个错误就停止
```

### 3. 并行控制

```python
# 串行执行
"parallel": False

# 并行执行
"parallel": True

# 限制并发数
"parallel": True,
"max_workers": 5  # 最多 5 个同时执行
```


## 📊 性能对比

| 模式 | 速度 | 内存 | 适用场景 |
|------|------|------|----------|
| 串行 | 慢 | 低 | CPU 密集型，需要保证顺序 |
| 并行（无限制） | 快 | 高 | I/O 密集型（API 调用） |
| 并行（限制并发） | 中 | 中 | API 速率限制，大数据集 |

## 🎓 学习路径

1. **入门** (5 分钟)
   - 运行 `python examples/simple_foreach_demo.py`
   - 看三个简单示例

2. **进阶** (15 分钟)
   - 阅读 `docs/foreach_node_guide.md`
   - 运行 `python examples/foreach_node_examples.py`

3. **深入** (30 分钟)
   - 阅读 `docs/foreach_node_design.md`
   - 查看 `app/workflow/nodes/foreach_*.py` 源码

4. **实践** (1 小时)
   - 在你的项目中使用 ForEach
   - 根据需求选择合适的节点类型

## 🧪 测试

运行测试确保一切正常：

```bash
# 运行所有 ForEach 相关测试
pytest tests/test_foreach_node.py -v

# 运行特定测试
pytest tests/test_foreach_node.py::TestSimpleForEachNode -v
```

## 📚 API 参考

### SimpleForEachNode 输入端口

| 端口 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `items` | array | ✓ | 要处理的项目列表 |
| `node_type` | string | ✓ | 节点类名 |
| `item_port_name` | string | | 输入端口（默认: "text"） |
| `result_port_name` | string | | 输出端口（默认: "result"） |
| `parallel` | boolean | | 并行执行（默认: false） |
| `max_workers` | number | | 最大并发数 |
| `continue_on_error` | boolean | | 出错继续（默认: true） |
| `node_config` | object | | 额外配置 |

### SimpleForEachNode 输出端口

| 端口 | 类型 | 说明 |
|------|------|------|
| `results` | array | 所有结果 |
| `success_count` | number | 成功数量 |
| `error_count` | number | 失败数量 |
| `errors` | array | 错误列表 |

完整 API 文档请参考 `docs/foreach_node_guide.md`

## ❓ 常见问题

**Q: 如何选择用哪个 ForEach 节点？**

A: 
- 简单场景 → `SimpleForEachNode`
- 大数据集 → `BatchProcessNode`
- 复杂多步骤 → `ForEachNode`

**Q: 并行执行会不会太消耗资源？**

A: 使用 `max_workers` 限制并发数，或使用 `BatchProcessNode` 分批处理。

**Q: 如何处理错误？**

A: 检查输出的 `error_count` 和 `errors` 列表，设置 `continue_on_error` 控制策略。

**Q: 能否嵌套使用 ForEach？**

A: 可以，但要注意性能。建议外层串行 + 内层并行。

**Q: 如何限制 API 调用速率？**

A: 使用 `max_workers` 或 `batch_size` + `parallel_batches=False`。

更多问题请参考 `docs/foreach_node_guide.md`

## 🎉 总结

ForEach Node 为工作流带来了强大的动态执行能力：

- ✅ **易用性**: 简单 API，快速上手
- ✅ **灵活性**: 两种节点满足不同需求
- ✅ **性能**: 支持并行执行和并发控制
- ✅ **可靠性**: 完善的错误处理
- ✅ **可扩展**: 支持任何自定义节点

现在，你的工作流不再是静态的了！🚀

## 📞 获取帮助

- 查看示例: `examples/`
- 阅读文档: `docs/foreach_node_guide.md`
- 运行测试: `pytest tests/test_foreach_node.py`
- 查看源码: `app/workflow/nodes/foreach_*.py`

Happy coding! 🎨

