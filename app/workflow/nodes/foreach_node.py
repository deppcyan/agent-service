from typing import Dict, Any, List, Optional
from app.workflow.base import WorkflowNode, WorkflowGraph, NodeConnection
from app.workflow.executor import WorkflowExecutor
from app.utils.logger import logger
import copy


class ForEachNode(WorkflowNode):
    """
    ForEach node that enables dynamic workflow execution.
    
    This node iterates over a list of items and executes a sub-workflow for each item.
    Each iteration can access the current item through a special context variable.
    Results from all iterations are collected and returned as a list.
    
    Features:
    - Dynamic execution: Creates and executes workflow instances for each item
    - Result collection: Stores results from each iteration
    - Error handling: Can continue on errors or stop at first failure
    - Progress tracking: Reports success/failure counts
    - Parallel execution: Optionally execute iterations in parallel
    
    Usage:
    1. Define a sub-workflow with nodes that will process each item
    2. Connect the ForEachNode's outputs to the sub-workflow's inputs
    3. The sub-workflow can access the current item via the item_value output
    4. Specify which node's output to collect as results
    """
    
    category = "control"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("items", "array", True, 
                           tooltip="List of items to iterate over")
        self.add_input_port("sub_workflow", "object", True,
                           tooltip="Sub-workflow definition (nodes and connections)")
        self.add_input_port("result_node_id", "string", True,
                           tooltip="ID of the node in sub-workflow whose output to collect")
        self.add_input_port("result_port_name", "string", False, default_value="result",
                           tooltip="Name of the output port to collect (default: 'result')")
        self.add_input_port("parallel", "boolean", False, default_value=False,
                           tooltip="Execute iterations in parallel (default: False)")
        self.add_input_port("continue_on_error", "boolean", False, default_value=True,
                           tooltip="Continue processing if an iteration fails (default: True)")
        self.add_input_port("max_iterations", "number", False,
                           tooltip="Maximum number of iterations to run (default: unlimited)")
        
        # Output ports
        self.add_output_port("results", "array",
                            tooltip="List of results from each successful iteration")
        self.add_output_port("item_value", "any",
                            tooltip="Current item being processed (for connecting to sub-workflow)")
        self.add_output_port("current_index", "number",
                            tooltip="Index of current item being processed")
        self.add_output_port("total_count", "number",
                            tooltip="Total number of items processed")
        self.add_output_port("success_count", "number",
                            tooltip="Number of successful iterations")
        self.add_output_port("error_count", "number",
                            tooltip="Number of failed iterations")
        self.add_output_port("errors", "array",
                            tooltip="List of errors that occurred")
        
        # Internal state for sub-workflow execution
        self._sub_graph: Optional[WorkflowGraph] = None
    
    def _build_sub_workflow(self, sub_workflow_def: Dict[str, Any]) -> WorkflowGraph:
        """
        Build a WorkflowGraph from a sub-workflow definition.
        
        Args:
            sub_workflow_def: Dictionary containing:
                - nodes: List of node definitions
                - connections: List of connection definitions
        
        Returns:
            WorkflowGraph: Constructed workflow graph
        """
        from app.workflow.registry import node_registry
        
        graph = WorkflowGraph()
        
        # Create nodes
        nodes_def = sub_workflow_def.get("nodes", [])
        for node_def in nodes_def:
            node_type = node_def.get("type")
            node_id = node_def.get("id")
            
            # Create node instance
            node = node_registry.create_node(node_type, node_id)
            
            # Set input values if provided
            input_values = node_def.get("input_values", {})
            node.input_values.update(input_values)
            
            graph.add_node(node)
        
        # Create connections
        connections_def = sub_workflow_def.get("connections", [])
        for conn_def in connections_def:
            graph.connect(
                from_node=conn_def["from_node"],
                from_port=conn_def["from_port"],
                to_node=conn_def["to_node"],
                to_port=conn_def["to_port"]
            )
        
        return graph
    
    async def _execute_iteration(self, 
                                 item: Any, 
                                 index: int,
                                 sub_workflow_def: Dict[str, Any],
                                 result_node_id: str,
                                 result_port_name: str) -> Dict[str, Any]:
        """
        Execute a single iteration of the sub-workflow.
        
        Args:
            item: Current item to process
            index: Index of current item
            sub_workflow_def: Sub-workflow definition
            result_node_id: Node ID to collect result from
            result_port_name: Port name to collect result from
        
        Returns:
            Dictionary containing:
                - success: Whether iteration succeeded
                - result: Result value (if successful)
                - error: Error message (if failed)
                - index: Item index
                - item: Original item
        """
        try:
            # Build sub-workflow graph for this iteration
            graph = self._build_sub_workflow(sub_workflow_def)
            
            # Inject the current item value into nodes that need it
            # Look for nodes with an input port that should receive the foreach item
            for node in graph.nodes.values():
                # Check if node has a port named "foreach_item" or similar
                if "foreach_item" in node.input_ports:
                    node.input_values["foreach_item"] = item
                if "foreach_index" in node.input_ports:
                    node.input_values["foreach_index"] = index
            
            # Execute sub-workflow
            executor = WorkflowExecutor(graph, task_id=self.task_id)
            await executor.execute()
            
            # Get result from specified node
            node_results = executor.get_node_result(result_node_id)
            if node_results is None:
                raise ValueError(f"Result node '{result_node_id}' not found in execution results")
            
            if result_port_name not in node_results:
                raise ValueError(f"Result port '{result_port_name}' not found in node '{result_node_id}' outputs")
            
            result_value = node_results[result_port_name]
            
            return {
                "success": True,
                "result": result_value,
                "error": None,
                "index": index,
                "item": item
            }
            
        except Exception as e:
            logger.error(f"ForEach iteration {index} failed: {str(e)}", 
                        extra=self.get_log_extra())
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "index": index,
                "item": item
            }
    
    async def process(self) -> Dict[str, Any]:
        """
        Process all items through the sub-workflow.
        
        Returns:
            Dictionary with results, counts, and errors
        """
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        items = self.input_values["items"]
        sub_workflow_def = self.input_values["sub_workflow"]
        result_node_id = self.input_values["result_node_id"]
        result_port_name = self.input_values.get("result_port_name", "result")
        parallel = self.input_values.get("parallel", False)
        continue_on_error = self.input_values.get("continue_on_error", True)
        max_iterations = self.input_values.get("max_iterations")
        
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        
        # Limit iterations if max_iterations is specified
        items_to_process = items
        if max_iterations is not None:
            max_iterations = int(max_iterations)
            items_to_process = items[:max_iterations]
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        
        logger.info(f"ForEach starting: processing {len(items_to_process)} items",
                   extra=self.get_log_extra())
        
        if parallel:
            # Parallel execution
            import asyncio
            tasks = [
                self._execute_iteration(
                    item, index, sub_workflow_def, 
                    result_node_id, result_port_name
                )
                for index, item in enumerate(items_to_process)
            ]
            iteration_results = await asyncio.gather(*tasks)
            
            # Process results
            for iter_result in iteration_results:
                if iter_result["success"]:
                    results.append(iter_result["result"])
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "index": iter_result["index"],
                        "item": iter_result["item"],
                        "error": iter_result["error"]
                    })
        else:
            # Sequential execution
            for index, item in enumerate(items_to_process):
                iter_result = await self._execute_iteration(
                    item, index, sub_workflow_def,
                    result_node_id, result_port_name
                )
                
                if iter_result["success"]:
                    results.append(iter_result["result"])
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "index": iter_result["index"],
                        "item": iter_result["item"],
                        "error": iter_result["error"]
                    })
                    
                    # Stop on error if continue_on_error is False
                    if not continue_on_error:
                        logger.warning(f"ForEach stopped at iteration {index} due to error",
                                     extra=self.get_log_extra())
                        break
        
        logger.info(f"ForEach completed: {success_count} succeeded, {error_count} failed",
                   extra=self.get_log_extra())
        
        return {
            "results": results,
            "item_value": items_to_process[-1] if items_to_process else None,
            "current_index": len(items_to_process) - 1 if items_to_process else -1,
            "total_count": len(items_to_process),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }


class ForEachItemNode(WorkflowNode):
    """
    Helper node that receives the current item in a ForEach iteration.
    
    This node should be used as the starting point in a ForEach sub-workflow.
    It receives the item being processed and makes it available to downstream nodes.
    """
    
    category = "control"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports - receives data from ForEach context
        self.add_input_port("foreach_item", "any", True,
                           tooltip="Current item from ForEach loop")
        self.add_input_port("foreach_index", "number", False,
                           tooltip="Index of current item in ForEach loop")
        
        # Output ports - passes data to rest of sub-workflow
        self.add_output_port("item", "any",
                            tooltip="Current item being processed")
        self.add_output_port("index", "number",
                            tooltip="Index of current item")
    
    async def process(self) -> Dict[str, Any]:
        """Pass through the ForEach context values"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        item = self.input_values["foreach_item"]
        index = self.input_values.get("foreach_index", 0)
        
        return {
            "item": item,
            "index": index
        }

