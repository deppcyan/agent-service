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

    def create_workflow_executor(self, workflow_config: WorkflowConfig) -> Optional[WorkflowExecutor]:
        """Create a workflow executor from configuration"""
        try:
            # Convert configuration to graph and create executor
            graph = workflow_config.to_graph()
            executor = WorkflowExecutor(graph)
            return executor
            
        except Exception as e:
            logger.error(f"Error creating workflow executor: {str(e)}")
            return None

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
            if not executor:
                raise Exception("Failed to create workflow executor")
            
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
            
        del self.active_tasks[task_id]
        return True

    async def _execute_and_callback(self, task_id: str, executor: WorkflowExecutor, webhook_url: Optional[str] = None) -> None:
        """Execute workflow and call webhook when complete"""
        try:
            # Execute workflow
            result = await executor.execute()
            
            # Call webhook if provided
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "completed",
                        "result": result
                    })
                    
        except asyncio.CancelledError:
            # Handle cancellation
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "cancelled"
                    })
            raise
            
        except Exception as e:
            # Handle execution error
            logger.error(f"Error executing workflow {task_id}: {str(e)}")
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={
                        "task_id": task_id,
                        "status": "error",
                        "error": str(e)
                    })
                    
        finally:
            # Store task result and clean up active task
            if task_id in self.active_tasks:
                # Only store in completed_tasks if webhook_url is None
                if webhook_url is None:
                    if 'result' in locals():
                        self.completed_tasks[task_id] = {
                            "status": "completed",
                            "result": result  # 使用统一的 result 字段
                        }
                    elif 'e' in locals():  # Error case
                        self.completed_tasks[task_id] = {
                            "status": "error",
                            "result": {},  # 空结果
                            "error": str(e)
                        }
                    else:  # Cancelled case
                        self.completed_tasks[task_id] = {
                            "status": "cancelled",
                            "result": {}  # 空结果
                        }
                # Remove from active tasks
                del self.active_tasks[task_id]

# Create global workflow manager instance
workflow_manager = WorkflowManager()
