from calendar import TUESDAY
import json
import uuid
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from app.utils.logger import logger
from app.workflow.config import WorkflowConfig
from app.workflow.executor import WorkflowExecutor
from app.workflow.registry import node_registry

class WorkflowManager:
    """Manages workflow configurations and their lifecycle"""
    
    def __init__(self, workflows_dir: str = "app/config/workflows"):
        self.workflows_dir = workflows_dir
        self.workflows: Dict[str, WorkflowConfig] = {}
        # Store active workflow tasks
        self.active_tasks: Dict[str, Tuple[asyncio.Task, WorkflowExecutor]] = {}
        # Store completed tasks with their results
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        # Load built-in nodes
        node_registry.load_builtin_nodes()

    def create_workflow_executor(self, workflow_config: WorkflowConfig) -> WorkflowExecutor:
        """Create a workflow executor from configuration"""
        try:
            # Convert configuration to graph and create executor
            graph = workflow_config.to_graph()
            executor = WorkflowExecutor(graph)
            return executor
            
        except Exception as e:
            logger.error(f"Error creating workflow executor: {str(e)}")
            raise

    async def execute_workflow(self, workflow_json: Dict[str, Any], webhook_url: Optional[str] = None) -> str:
        """Execute a workflow asynchronously with webhook callback
        
        Args:
            workflow_json: The workflow configuration in JSON format
            input_data: Input data for the workflow
            webhook_url: Optional URL to call when workflow completes
            
        Returns:
            str: Task ID for tracking the workflow execution
        """
        try:
            # Create workflow config from JSON
            workflow_config = WorkflowConfig.from_dict(workflow_json)
            
            # Create executor
            executor = self.create_workflow_executor(workflow_config)
            
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Create and store the task
            task = asyncio.create_task(self._execute_and_callback(task_id, executor, webhook_url))
            self.active_tasks[task_id] = (task, executor)
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error starting workflow execution: {str(e)}")
            raise

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status and result of a task
        
        Args:
            task_id: The ID of the task to check
            
        Returns:
            Optional[Dict[str, Any]]: Task status and result if found, None if task not found
            The returned dictionary contains:
            - status: "running" | "completed" | "error" | "cancelled" | "not_found"
            - result: Dictionary of node results (available in all states)
            - error: Error message (only present if status is "error")
        """
        # First check active tasks
        if task_id in self.active_tasks:
            _, executor = self.active_tasks[task_id]
            return {
                "status": "running",
                "result": executor.node_results  # 使用统一的 result 字段
            }
            
        # Then check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
            
        # Return not found status instead of None
        return {
            "status": "not_found",
            "result": {}
        }

    def _update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None, error: str = None, store_result: bool = True) -> None:
        """Update task status and manage task storage
        
        Args:
            task_id: The ID of the task to update
            status: New status ("completed", "error", "cancelled")
            result: Optional result data
            error: Optional error message
            store_result: If True, store result in completed_tasks (default: True)
        """
        # Remove from active tasks if present
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
        # Store in completed tasks only if store_result is True
        if store_result:
            self.completed_tasks[task_id] = {
                "status": status,
                "result": result or {},
            }
            if error:
                self.completed_tasks[task_id]["error"] = error

    async def cancel_workflow(self, task_id: str) -> bool:
        """Cancel a running workflow
        
        Args:
            task_id: The ID of the task to cancel
            
        Returns:
            bool: True if task was cancelled, False if task not found
        """
        if task_id not in self.active_tasks:
            return False
            
        task, executor = self.active_tasks[task_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        return True

    async def _execute_and_callback(self, task_id: str, executor: WorkflowExecutor, webhook_url: Optional[str] = None) -> None:
        """Execute workflow and call webhook when complete"""
        try:
            # Execute workflow
            result = await executor.execute()
            
            # Update status and call webhook if provided
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "completed",
                        "result": result
                    })
                self._update_task_status(task_id, "completed", result, store_result=False)
            else:
                self._update_task_status(task_id, "completed", result, store_result=True)
                    
        except asyncio.CancelledError:
            # Handle cancellation
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "cancelled"
                    })
                self._update_task_status(task_id, "cancelled", store_result=False)
            else:
                self._update_task_status(task_id, "cancelled", store_result=True)
            raise
            
        except Exception as e:
            # Handle execution error
            error_msg = str(e)
            logger.error(f"Error executing workflow {task_id}: {error_msg}")
            
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "error",
                        "error": error_msg
                    })
                self._update_task_status(task_id, "error", error=error_msg, store_result=False)
            else:
                self._update_task_status(task_id, "error", error=error_msg, store_result=True)

# Create global workflow manager instance
workflow_manager = WorkflowManager()
