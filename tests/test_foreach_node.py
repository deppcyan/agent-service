"""
Tests for ForEach nodes
"""

import pytest
import asyncio
from app.workflow.base import WorkflowGraph
from app.workflow.executor import WorkflowExecutor
from app.workflow.nodes.foreach_simple import SimpleForEachNode
from app.workflow.nodes.foreach_node import ForEachNode, ForEachItemNode
from app.workflow.nodes.text_process import TextStripNode, TextToListNode
from app.workflow.nodes.basic_types import TextInputNode
from app.workflow.registry import node_registry


@pytest.fixture
def setup_registry():
    """Ensure all nodes are registered"""
    node_registry.load_builtin_nodes()
    yield node_registry


class TestSimpleForEachNode:
    """Test SimpleForEachNode functionality"""
    
    @pytest.mark.asyncio
    async def test_simple_sequential_processing(self, setup_registry):
        """Test basic sequential processing"""
        graph = WorkflowGraph()
        
        # Create input list
        input_node = TextToListNode()
        input_node.input_values = {
            "text": '["  hello  ", "  world  "]',
            "format": "json"
        }
        graph.add_node(input_node)
        
        # ForEach to strip each item
        foreach_node = SimpleForEachNode()
        foreach_node.input_values = {
            "node_type": "TextStripNode",
            "item_port_name": "text",
            "result_port_name": "text",
            "parallel": False
        }
        graph.add_node(foreach_node)
        
        graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
        
        # Execute
        executor = WorkflowExecutor(graph)
        results = await executor.execute()
        
        # Verify
        foreach_results = results[foreach_node.node_id]
        assert foreach_results["success_count"] == 2
        assert foreach_results["error_count"] == 0
        assert foreach_results["results"] == ["hello", "world"]
    
    @pytest.mark.asyncio
    async def test_parallel_processing(self, setup_registry):
        """Test parallel processing"""
        graph = WorkflowGraph()
        
        # Create input
        input_node = TextToListNode()
        input_node.input_values = {
            "text": "a,b,c,d,e",
            "format": "delimited",
            "delimiter": ",",
            "trim_items": False
        }
        graph.add_node(input_node)
        
        # ForEach parallel
        foreach_node = SimpleForEachNode()
        foreach_node.input_values = {
            "node_type": "TextStripNode",
            "item_port_name": "text",
            "result_port_name": "text",
            "parallel": True,
            "max_workers": 3
        }
        graph.add_node(foreach_node)
        
        graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
        
        # Execute
        executor = WorkflowExecutor(graph)
        results = await executor.execute()
        
        # Verify
        foreach_results = results[foreach_node.node_id]
        assert foreach_results["success_count"] == 5
        assert len(foreach_results["results"]) == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, setup_registry):
        """Test error handling with continue_on_error"""
        # This test would need a node that can fail
        # For now, we'll test the structure
        foreach_node = SimpleForEachNode()
        foreach_node.input_values = {
            "items": ["valid"],
            "node_type": "TextStripNode",
            "item_port_name": "text",
            "result_port_name": "text",
            "continue_on_error": True
        }
        
        result = await foreach_node.process()
        assert "errors" in result
        assert "success_count" in result
        assert "error_count" in result


class TestForEachNode:
    """Test advanced ForEachNode functionality"""
    
    @pytest.mark.asyncio
    async def test_subworkflow_execution(self, setup_registry):
        """Test sub-workflow execution"""
        # Define sub-workflow
        sub_workflow = {
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
        
        input_node = TextToListNode()
        input_node.input_values = {
            "text": '["  test1  ", "  test2  "]',
            "format": "json"
        }
        graph.add_node(input_node)
        
        foreach_node = ForEachNode()
        foreach_node.input_values = {
            "sub_workflow": sub_workflow,
            "result_node_id": "strip_node",
            "result_port_name": "text",
            "parallel": False
        }
        graph.add_node(foreach_node)
        
        graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
        
        # Execute
        executor = WorkflowExecutor(graph)
        results = await executor.execute()
        
        # Verify
        foreach_results = results[foreach_node.node_id]
        assert foreach_results["success_count"] == 2
        assert foreach_results["results"] == ["test1", "test2"]


class TestForEachItemNode:
    """Test ForEachItemNode helper"""
    
    @pytest.mark.asyncio
    async def test_item_passthrough(self):
        """Test that ForEachItemNode passes through values correctly"""
        node = ForEachItemNode()
        node.input_values = {
            "foreach_item": "test_value",
            "foreach_index": 5
        }
        
        result = await node.process()
        
        assert result["item"] == "test_value"
        assert result["index"] == 5


class TestIntegration:
    """Integration tests combining multiple features"""
    
    @pytest.mark.asyncio
    async def test_realworld_workflow(self, setup_registry):
        """Test a realistic workflow scenario"""
        graph = WorkflowGraph()
        
        # Input: list of texts that need cleaning
        input_node = TextToListNode()
        input_node.input_values = {
            "text": "  hello  ,  world  ,  test  ",
            "format": "delimited",
            "delimiter": ",",
            "trim_items": False
        }
        graph.add_node(input_node)
        
        # Process with ForEach
        foreach_node = SimpleForEachNode()
        foreach_node.input_values = {
            "node_type": "TextStripNode",
            "item_port_name": "text",
            "result_port_name": "text",
            "parallel": True,
            "continue_on_error": True
        }
        graph.add_node(foreach_node)
        
        graph.connect(input_node.node_id, "list", foreach_node.node_id, "items")
        
        # Execute
        executor = WorkflowExecutor(graph)
        results = await executor.execute()
        
        # Verify complete pipeline
        foreach_results = results[foreach_node.node_id]
        assert foreach_results["success_count"] == 3
        assert all(isinstance(r, str) for r in foreach_results["results"])
        assert all(r.strip() == r for r in foreach_results["results"])
        assert foreach_results["results"] == ["hello", "world", "test"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

