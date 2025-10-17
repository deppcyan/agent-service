from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AsyncWorkflow(ABC):
    """Base class for async workflows"""
    
    def __init__(self, name: str):
        self.name = name
        self._task: Optional[Any] = None
    
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
