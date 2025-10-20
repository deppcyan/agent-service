import os
from typing import Dict, Any, Optional
import aiohttp
from abc import ABC, abstractmethod
from app.workflow.base import WorkflowNode
from app.utils.logger import logger
from app.core.callback_manager import callback_manager

class APIServiceNode(WorkflowNode, ABC):
    """Base class for API service nodes"""
    
    category = "api_services"
    service_name: str = None  # Should be set by child classes
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        if not self.service_name:
            raise ValueError("service_name must be set by child classes")
            
        # Get API key from environment variable
        self.api_key = os.getenv("DIGEN_API_KEY")
        if not self.api_key:
            raise ValueError("DIGEN_API_KEY environment variable not set")
            
        # Common input ports for API services
        self.add_input_port("api_url", "string", True)
        
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for the service. Must be implemented by child classes."""
        raise NotImplementedError("_prepare_request must be implemented by child classes")
        
    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to service"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.input_values['api_url']}"
        
        async with aiohttp.ClientSession() as session:
            logger.info(f"{self.service_name}: Making POST request to {url}")
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"{self.service_name}: Service request failed: {error_text}")
                    raise Exception(f"Service call failed with status {response.status}: {error_text}")
                    
                response_data = await response.json()
                logger.info(f"{self.service_name}:  Received response from service")
                return response_data
                
    @abstractmethod
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs. Must be implemented by child classes."""
        pass