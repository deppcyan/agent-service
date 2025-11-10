from typing import Dict, Any, Optional
from .base import WorkflowGraph, WorkflowNode
import asyncio
from app.utils.logger import logger

class WorkflowExecutor:
    """Executes a workflow graph"""
    
    def __init__(self, graph: WorkflowGraph, task_id: Optional[str] = None):
        self.graph = graph
        self.task_id = task_id
        self.node_results: Dict[str, Dict[str, Any]] = {}
    
    def _should_skip_node(self, node: WorkflowNode) -> bool:
        """
        检查是否应该跳过节点执行
        主要针对SwitchNode后的未激活分支
        
        跳过条件：
        只要有一个连线的输入是None就跳过节点
        
        例外：
        - MergeNode不跳过，因为它需要处理多个输入（包括None值）来选择第一个非空的输入
        - PassThroughNode不跳过，因为它需要根据控制信号决定是否透传数据
        """
        # MergeNode和PassThroughNode不跳过，它们专门用来处理可能为None的输入
        if node.__class__.__name__ in ['MergeNode', 'PassThroughNode']:
            return False
        
        # 检查所有连接到此节点的输入
        for conn in self.graph.connections:
            if conn.to_node == node.node_id:
                # 检查连接传入的值
                if conn.from_node in self.node_results:
                    source_value = self.node_results[conn.from_node][conn.from_port]
                    if source_value is None:
                        # 只要有一个连线输入为None，就跳过节点
                        return True
        
        return False

    async def execute_node(self, node: WorkflowNode):
        """Execute a single node"""
        # Set task_id context for the node
        node.task_id = self.task_id
        
        # Get input values from connected nodes
        for conn in self.graph.connections:
            if conn.to_node == node.node_id:
                if conn.from_node not in self.node_results:
                    raise ValueError(f"Node {conn.from_node} has not been executed yet")
                    
                source_value = self.node_results[conn.from_node][conn.from_port]
                node.input_values[conn.to_port] = source_value
        
        # Check if node should be skipped due to empty inputs
        if self._should_skip_node(node):
            extra = {'job_id': self.task_id} if self.task_id else {}
            logger.info(f"Skipping node {node.node_id} - all required inputs are None", extra=extra)
            
            # Create empty result with None values for all output ports
            empty_result = {}
            for port_name in node.output_ports.keys():
                empty_result[port_name] = None
            
            self.node_results[node.node_id] = empty_result
            return empty_result
        
        # Execute the node
        try:
            extra = {'job_id': self.task_id} if self.task_id else {}
            logger.info(f"Executing node {node.node_id}", extra=extra)
            result = await node.process()
            self.node_results[node.node_id] = result
            logger.info(f"Node {node.node_id} executed successfully", extra=extra)
            return result
        except Exception as e:
            extra = {'job_id': self.task_id} if self.task_id else {}
            logger.error(f"Error executing node {node.node_id}: {str(e)}", extra=extra)
            raise Exception(f"Node {node.node_id}: {str(e)}") from e
    
    async def execute(self) -> Dict[str, Dict[str, Any]]:
        """Execute the entire workflow"""
        extra = {'job_id': self.task_id} if self.task_id else {}
        execution_order = self.graph.get_execution_order()
        
        logger.info(f"Starting workflow execution with {len(execution_order)} nodes", extra=extra)
        
        for node_id in execution_order:
            node = self.graph.nodes[node_id]
            await self.execute_node(node)
        
        logger.info(f"Workflow execution completed successfully", extra=extra)
        return self.node_results
    
    def get_node_result(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a specific node"""
        return self.node_results.get(node_id)
