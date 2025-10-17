from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from uuid import UUID

class ServiceResponse(BaseModel):
    id: str
    status: str
    pod_id: Optional[str] = None
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[float] = None
    pod_url: Optional[str] = None
    local_url: Optional[List[str]] = None
    error: Optional[str] = None

class ServiceNode(ABC):
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = self._get_model_name()

    @abstractmethod
    def _get_model_name(self) -> str:
        """Return the model name for this service node"""
        pass

    @abstractmethod
    async def generate(self, input_data: Dict[str, Any], webhook_url: Optional[str] = None) -> ServiceResponse:
        """Generate output using the service"""
        pass

    @abstractmethod
    async def cancel(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job"""
        pass

class Workflow(ABC):
    def __init__(self, name: str):
        self.name = name
        self.nodes: List[ServiceNode] = []
        self.job_ids: List[str] = []

    def add_node(self, node: ServiceNode) -> None:
        """Add a service node to the workflow"""
        self.nodes.append(node)

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Execute the workflow with the given input data"""
        pass

    async def cancel(self) -> List[Dict[str, Any]]:
        """Cancel all running jobs in the workflow"""
        results = []
        for node in self.nodes:
            for job_id in self.job_ids:
                try:
                    result = await node.cancel(job_id)
                    results.append(result)
                except Exception as e:
                    results.append({"status": "error", "job_id": job_id, "error": str(e)})
        return results
