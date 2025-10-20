import os
from typing import Dict, Any, Optional
import aiohttp
from app.workflow.base import WorkflowNode
from app.utils.logger import logger
from app.core.callback_manager import callback_manager

class APIServiceNode(WorkflowNode):
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
        self.add_input_port("callback_url", "string", False)
        self.add_input_port("timeout", "number", False)
        
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for the service. Must be implemented by child classes."""
        raise NotImplementedError("_prepare_request must be implemented by child classes")
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data. Must be implemented by child classes."""
        raise NotImplementedError("_handle_callback must be implemented by child classes")
        
    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to service"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.input_values['api_url']}/v1/generate"
        
        async with aiohttp.ClientSession() as session:
            logger.info(f"Making POST request to {url}", 
                       extra={"service": self.service_name})
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Service request failed: {error_text}",
                               extra={"service": self.service_name})
                    raise Exception(f"Service call failed with status {response.status}: {error_text}")
                    
                response_data = await response.json()
                logger.info("Received response from service", 
                          extra={"service": self.service_name})
                return response_data
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        # Get callback URL and timeout if provided
        callback_url = self.input_values.get("callback_url")
        timeout = self.input_values.get("timeout")
        
        # Prepare request data
        request_data = self._prepare_request(self.input_values, callback_url)
        
        # Register callback handler if callback URL is provided
        if callback_url:
            logger.debug(f"Registering callback handler for URL: {callback_url}",
                       extra={"service": self.service_name})
            callback_manager.register_handler(
                self.service_name,
                self.node_id,
                self._handle_callback
            )
        
        try:
            # Make request
            response = await self._make_request(request_data)
            
            # If no callback URL, return response directly
            if not callback_url:
                logger.info("Request completed (no callback)",
                          extra={"service": self.service_name})
                return response
            
            # Wait for callback
            logger.info("Waiting for callback",
                      extra={"service": self.service_name})
            callback_data = await callback_manager.wait_for_callback(self.node_id, timeout)
            
            # Handle callback data
            logger.debug("Processing callback data",
                       extra={"service": self.service_name})
            result = await self._handle_callback(callback_data)
            
            logger.info("Request completed (with callback)",
                      extra={"service": self.service_name})
            return result
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}",
                       extra={"service": self.service_name})
            if callback_url:
                callback_manager.unregister_handler(self.node_id)
            raise
