from typing import Dict, Any, Optional
from .base import WorkflowGraph, WorkflowNode
import asyncio
from app.utils.logger import logger

class WorkflowExecutor:
    """Executes a workflow graph"""
    
    def __init__(self, graph: WorkflowGraph):
        self.graph = graph
        self.node_results: Dict[str, Dict[str, Any]] = {}
    
    async def execute_node(self, node: WorkflowNode):
        """Execute a single node"""
        # Get input values from connected nodes
        for conn in self.graph.connections:
            if conn.to_node == node.node_id:
                if conn.from_node not in self.node_results:
                    raise ValueError(f"Node {conn.from_node} has not been executed yet")
                    
                source_value = self.node_results[conn.from_node][conn.from_port]
                node.input_values[conn.to_port] = source_value
        
        # Execute the node
        try:
            logger.info(f"Executing node {node.node_id}")
            result = await node.process()
            self.node_results[node.node_id] = result
            logger.info(f"Node {node.node_id} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing node {node.node_id}: {str(e)}")
            raise Exception(f"Node {node.node_id}: {str(e)}") from e
    
    async def execute(self) -> Dict[str, Dict[str, Any]]:
        """Execute the entire workflow"""
        execution_order = self.graph.get_execution_order()
        
        for node_id in execution_order:
            node = self.graph.nodes[node_id]
            await self.execute_node(node)
        
        return self.node_results
    
    def get_node_result(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a specific node"""
        return self.node_results.get(node_id)
