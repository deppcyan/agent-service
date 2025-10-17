from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.logger import logger

class AsyncWorkflow(ABC):
    """Base class for async workflows"""
    
    def __init__(self, name: str):
        self.name = name
        self._task: Optional[Any] = None
        
    def _log_request(self, job_id: str, step_name: str, request_data: Dict[str, Any]) -> None:
        """Log request data for a workflow step"""
        logger.info(
            f"Workflow step request: {step_name}",
            extra={
                "job_id": job_id,
                "workflow": self.name,
                "step": step_name,
                "request": request_data
            }
        )
        
    def _log_response(self, job_id: str, step_name: str, response_data: Dict[str, Any]) -> None:
        """Log response data for a workflow step"""
        logger.info(
            f"Workflow step response: {step_name}",
            extra={
                "job_id": job_id,
                "workflow": self.name,
                "step": step_name,
                "response": response_data
            }
        )
    
    @abstractmethod
    async def execute(self, job_id: str, input_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with given input data and options
        
        Args:
            job_id: Unique identifier for this job
            input_data: Input data for the workflow
            options: Additional options to control workflow behavior
            
        Returns:
            Dict containing workflow results
        """
        pass
    
    async def cancel(self) -> None:
        """Cancel the currently running workflow if any"""
        if self._task is not None:
            self._task.cancel()
            self._task = None
