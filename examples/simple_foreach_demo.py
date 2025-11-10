#!/usr/bin/env python3
"""
Simple ForEach Demo - Quick Start Guide

This is a minimal example to get you started with ForEach nodes.
Run this file to see ForEach in action!
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workflow.base import WorkflowGraph
from app.workflow.executor import WorkflowExecutor
from app.workflow.nodes.foreach_simple import SimpleForEachNode
from app.workflow.nodes.text_process import TextToListNode, TextStripNode
from app.workflow.registry import node_registry


async def demo_basic_foreach():
    """
    最简单的 ForEach 示例
    
    场景：有一个文本列表，每个文本都有多余的空格，需要清理
    """
    print("\n" + "="*70)
    print("Demo 1: 基础 ForEach - 批量清理文本")
    print("="*70)
    
    # 步骤 1: 加载节点
    print("\n[1/4] 加载节点...")
    node_registry.load_builtin_nodes()
    print("✓ 节点加载完成")
    
    # 步骤 2: 创建工作流图
    print("\n[2/4] 创建工作流...")
    graph = WorkflowGraph()
    
    # 输入节点：创建一个文本列表
    input_node = TextToListNode()
    input_node.input_values = {
        "text": '["  hello  ", "  world  ", "  python  "]',
        "format": "json"
    }
    graph.add_node(input_node)
    print("✓ 添加输入节点")
    
    # ForEach 节点：对每个文本执行 strip 操作
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",     # 使用 TextStripNode 处理每个项目
        "item_port_name": "text",         # 将项目传入 text 端口
        "result_port_name": "text",       # 从 text 端口收集结果
        "parallel": False,                 # 串行执行
        "continue_on_error": True         # 出错继续
    }
    graph.add_node(foreach_node)
    print("✓ 添加 ForEach 节点")
    
    # 连接节点
    graph.connect(
        input_node.node_id, "list",      # 从输入节点的 list 端口
        foreach_node.node_id, "items"    # 连接到 ForEach 的 items 端口
    )
    print("✓ 连接节点完成")
    
    # 步骤 3: 执行工作流
    print("\n[3/4] 执行工作流...")
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    print("✓ 执行完成")
    
    # 步骤 4: 查看结果
    print("\n[4/4] 结果:")
    foreach_results = results[foreach_node.node_id]
    
    print(f"\n输入列表: ['  hello  ', '  world  ', '  python  ']")
    print(f"输出列表: {foreach_results['results']}")
    print(f"\n统计信息:")
    print(f"  - 成功处理: {foreach_results['success_count']} 个")
    print(f"  - 失败: {foreach_results['error_count']} 个")
    
    return foreach_results


async def demo_parallel_foreach():
    """
    并行执行示例
    
    场景：同时处理多个项目，提高速度
    """
    print("\n" + "="*70)
    print("Demo 2: 并行 ForEach - 快速批量处理")
    print("="*70)
    
    node_registry.load_builtin_nodes()
    
    graph = WorkflowGraph()
    
    # 创建更大的列表
    items = [f"  item_{i:02d}  " for i in range(10)]
    input_node = TextToListNode()
    input_node.input_values = {
        "text": str(items),
        "format": "json"
    }
    graph.add_node(input_node)
    
    # 并行执行 ForEach
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",
        "item_port_name": "text",
        "result_port_name": "text",
        "parallel": True,              # 🔥 启用并行执行
        "max_workers": 5,              # 🔥 最多 5 个并发
        "continue_on_error": True
    }
    graph.add_node(foreach_node)
    
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    print("\n执行中（并行处理 10 个项目）...")
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"\n✓ 并行处理完成!")
    print(f"  - 处理了 {foreach_results['success_count']} 个项目")
    print(f"  - 结果预览: {foreach_results['results'][:3]} ...")
    
    return foreach_results


async def demo_with_config():
    """
    带配置的 ForEach 示例
    
    场景：执行节点时需要额外配置
    """
    print("\n" + "="*70)
    print("Demo 3: 配置 ForEach - 自定义节点参数")
    print("="*70)
    
    node_registry.load_builtin_nodes()
    
    graph = WorkflowGraph()
    
    # 输入
    input_node = TextToListNode()
    input_node.input_values = {
        "text": "hello,world,test",
        "format": "delimited",
        "delimiter": ","
    }
    graph.add_node(input_node)
    
    # ForEach 带额外配置
    from app.workflow.nodes.text_process import TextReplaceNode
    
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextReplaceNode",
        "item_port_name": "text",
        "result_port_name": "replaced_text",
        "parallel": False,
        "node_config": {                # 🔥 额外配置
            "old_text": "o",
            "new_text": "0",
            "count": -1,
            "direction": "all"
        }
    }
    graph.add_node(foreach_node)
    
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    print("\n执行中（将 'o' 替换为 '0'）...")
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"\n✓ 处理完成!")
    print(f"  - 输入: ['hello', 'world', 'test']")
    print(f"  - 输出: {foreach_results['results']}")
    print(f"  - 解释: 所有的 'o' 都被替换成了 '0'")
    
    return foreach_results


async def main():
    """运行所有演示"""
    print("\n" + "="*70)
    print("  ForEach Node - 快速入门演示")
    print("="*70)
    print("\n这个脚本将展示三个 ForEach 的使用示例")
    
    try:
        # 运行演示
        await demo_basic_foreach()
        await demo_parallel_foreach()
        await demo_with_config()
        
        print("\n" + "="*70)
        print("  ✓ 所有演示完成!")
        print("="*70)
        print("\n下一步:")
        print("  1. 查看完整示例: examples/foreach_node_examples.py")
        print("  2. 阅读使用指南: docs/foreach_node_guide.md")
        print("  3. 阅读设计文档: docs/foreach_node_design.md")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

