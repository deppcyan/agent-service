"""
ForEach Node Examples and Usage Guide

This file demonstrates different ways to use the ForEach nodes for dynamic workflow execution.

There are two types of ForEach nodes:

1. SimpleForEachNode (推荐)
   - 执行单个节点类型处理每个项目
   - API 简单，覆盖大多数场景
   
2. ForEachNode (高级)
   - 执行完整的子工作流处理每个项目
   - 最大灵活性，但配置更复杂
"""

import asyncio
from app.workflow.base import WorkflowGraph
from app.workflow.executor import WorkflowExecutor
from app.workflow.nodes.foreach_simple import SimpleForEachNode
from app.workflow.nodes.foreach_node import ForEachNode, ForEachItemNode
from app.workflow.nodes.text_process import TextStripNode, TextRepeatNode
from app.workflow.nodes.basic_types import TextInputNode, MathOperationNode


# ============================================================================
# Example 1: Simple text processing with SimpleForEachNode
# ============================================================================

async def example_simple_text_processing():
    """
    Process a list of texts by stripping whitespace from each.
    This is the simplest use case.
    """
    print("\n" + "="*70)
    print("Example 1: Simple Text Processing")
    print("="*70)
    
    graph = WorkflowGraph()
    
    # Create input node with list of texts
    input_node = TextRepeatNode()
    input_node.input_values = {
        "text": "  hello world  ",
        "repeat_count": 3
    }
    graph.add_node(input_node)
    
    # Create ForEach node that will strip each text
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",  # Node class name to execute
        "item_port_name": "text",       # Input port to send each item
        "result_port_name": "text",     # Output port to collect results
        "parallel": False,               # Sequential processing
        "continue_on_error": True
    }
    graph.add_node(foreach_node)
    
    # Connect nodes
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    # Execute workflow
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    # Display results
    foreach_results = results[foreach_node.node_id]
    print(f"Processed {foreach_results['success_count']} items")
    print(f"Results: {foreach_results['results']}")
    
    return foreach_results


# ============================================================================
# Example 2: Parallel processing with configuration
# ============================================================================

async def example_parallel_processing():
    """
    Process multiple items in parallel with additional node configuration.
    """
    print("\n" + "="*70)
    print("Example 2: Parallel Processing with Configuration")
    print("="*70)
    
    graph = WorkflowGraph()
    
    # Create input with list of numbers
    from app.workflow.nodes.basic_types import IntInputNode
    input_node = IntInputNode()
    input_node.input_values = {"value": 5}
    graph.add_node(input_node)
    
    # Create list from number
    repeat_node = TextRepeatNode()
    repeat_node.input_values = {"text": "item"}
    graph.add_node(repeat_node)
    graph.connect(input_node.node_id, "value", repeat_node.node_id, "repeat_count")
    
    # ForEach node with parallel execution
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",
        "item_port_name": "text",
        "result_port_name": "text",
        "parallel": True,               # Enable parallel processing
        "max_workers": 3,                # Limit concurrent workers
        "continue_on_error": True
    }
    graph.add_node(foreach_node)
    graph.connect(repeat_node.node_id, "list", foreach_node.node_id, "items")
    
    # Execute
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"Parallel processing completed:")
    print(f"  Success: {foreach_results['success_count']}")
    print(f"  Errors: {foreach_results['error_count']}")
    print(f"  Results: {foreach_results['results']}")
    
    return foreach_results


# ============================================================================
# Example 3: Advanced - Full sub-workflow execution
# ============================================================================

async def example_advanced_subworkflow():
    """
    Execute a complete sub-workflow for each item using ForEachNode.
    This is more complex but allows for multi-step processing per item.
    """
    print("\n" + "="*70)
    print("Example 3: Advanced Sub-Workflow Execution")
    print("="*70)
    
    # Define the sub-workflow that will be executed for each item
    sub_workflow_def = {
        "nodes": [
            {
                "type": "ForEachItemNode",
                "id": "item_input",
                "input_values": {}
            },
            {
                "type": "TextStripNode",
                "id": "strip_node",
                "input_values": {}
            }
        ],
        "connections": [
            {
                "from_node": "item_input",
                "from_port": "item",
                "to_node": "strip_node",
                "to_port": "text"
            }
        ]
    }
    
    # Create main workflow
    graph = WorkflowGraph()
    
    # Input node with list
    from app.workflow.nodes.text_process import TextToListNode
    input_node = TextToListNode()
    input_node.input_values = {
        "text": "  hello  ,  world  ,  test  ",
        "format": "delimited",
        "delimiter": ",",
        "trim_items": False  # Don't trim here - let sub-workflow do it
    }
    graph.add_node(input_node)
    
    # ForEach node with sub-workflow
    foreach_node = ForEachNode()
    foreach_node.input_values = {
        "sub_workflow": sub_workflow_def,
        "result_node_id": "strip_node",      # Which node's output to collect
        "result_port_name": "text",           # Which port from that node
        "parallel": False,
        "continue_on_error": True
    }
    graph.add_node(foreach_node)
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    # Execute
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"Sub-workflow execution completed:")
    print(f"  Total: {foreach_results['total_count']}")
    print(f"  Success: {foreach_results['success_count']}")
    print(f"  Results: {foreach_results['results']}")
    
    return foreach_results


# ============================================================================
# Example 4: Error handling and recovery
# ============================================================================

async def example_error_handling():
    """
    Demonstrate error handling capabilities of ForEach nodes.
    """
    print("\n" + "="*70)
    print("Example 4: Error Handling")
    print("="*70)
    
    graph = WorkflowGraph()
    
    # Create input with mixed valid/invalid data
    from app.workflow.nodes.text_process import TextToListNode
    input_node = TextToListNode()
    input_node.input_values = {
        "text": '["valid1", "valid2", "valid3"]',
        "format": "json"
    }
    graph.add_node(input_node)
    
    # ForEach with error handling
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",
        "item_port_name": "text",
        "result_port_name": "text",
        "parallel": False,
        "continue_on_error": True  # Continue even if some items fail
    }
    graph.add_node(foreach_node)
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    # Execute
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"Error handling results:")
    print(f"  Success: {foreach_results['success_count']}")
    print(f"  Errors: {foreach_results['error_count']}")
    if foreach_results['errors']:
        print(f"  Error details: {foreach_results['errors']}")
    print(f"  Successful results: {foreach_results['results']}")
    
    return foreach_results


# ============================================================================
# Example 5: Real-world use case - Batch text transformation
# ============================================================================

async def example_realworld_batch_transform():
    """
    Real-world example: Transform a list of user inputs by cleaning and processing them.
    """
    print("\n" + "="*70)
    print("Example 5: Real-World Batch Text Transformation")
    print("="*70)
    
    graph = WorkflowGraph()
    
    # Simulate user inputs with various formatting issues
    user_inputs = [
        "  Hello World  ",
        "\n\nWelcome to our service\n\n",
        "  Data Processing  ",
        "\tTabbed content\t",
        "   Multiple   Spaces   "
    ]
    
    # Convert to workflow input
    from app.workflow.nodes.text_process import TextToListNode
    input_node = TextToListNode()
    input_node.input_values = {
        "text": '["  Hello World  ", "\\n\\nWelcome\\n\\n", "  Data  "]',
        "format": "json"
    }
    graph.add_node(input_node)
    
    # Clean texts using ForEach
    foreach_node = SimpleForEachNode()
    foreach_node.input_values = {
        "node_type": "TextStripNode",
        "item_port_name": "text",
        "result_port_name": "text",
        "parallel": True,
        "max_workers": 5,
        "continue_on_error": True
    }
    graph.add_node(foreach_node)
    graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
    
    # Execute
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    foreach_results = results[foreach_node.node_id]
    print(f"Batch transformation completed:")
    print(f"  Processed: {foreach_results['success_count']} items")
    print(f"  Cleaned results:")
    for i, result in enumerate(foreach_results['results'], 1):
        print(f"    {i}. '{result}'")
    
    return foreach_results


# ============================================================================
# Main execution
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    print("\n" + "="*80)
    print(" ForEach Node Examples - Dynamic Workflow Execution")
    print("="*80)
    
    # Run each example
    await example_simple_text_processing()
    await example_parallel_processing()
    await example_advanced_subworkflow()
    await example_error_handling()
    await example_realworld_batch_transform()
    
    print("\n" + "="*80)
    print(" All examples completed!")
    print("="*80)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())

