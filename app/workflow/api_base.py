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

class AsyncAPIServiceNode(APIServiceNode):
    """Asynchronous API service node that waits for callback"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        # Add callback-related input ports
        self.add_input_port("callback_url", "string", True)
        self.add_input_port("timeout", "number", False)
         
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data with callback URL.
        Must be implemented by child classes to include callback URL in request data.
        
        Args:
            input_data: Node input values
            
        Returns:
            Request data including callback URL
        """
        raise NotImplementedError("_prepare_request must be implemented by child classes")
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle callback data from the service.
        Must be implemented by child classes.
        
        Args:
            callback_data: Data received in the callback
            
        Returns:
            Processed callback data in the desired output format
        """
        raise NotImplementedError("_handle_callback must be implemented by child classes")
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        # Get callback URL and timeout
        timeout = self.input_values.get("timeout")
        logger.info(f"{self.service_name}: Using timeout value: {timeout} seconds")
        
        try:
            # Prepare request data
            request_data = self._prepare_request(self.input_values)
            logger.debug(f"{self.service_name}: Prepared request data: {json.dumps(request_data, indent=4, ensure_ascii=False)}")
            
            # Make request first to get job id
            response = await self._make_request(request_data)
            
            # Extract job id from response
            if not response.get("id"):
                raise ValueError("No job id returned from service")
            job_id = response["id"]
            
            callback_manager.register_handler(
                job_id,
                self._handle_callback
            )
            
            callback_data = await callback_manager.wait_for_callback(job_id, timeout)
            
            # Handle callback data
            logger.debug(f"{self.service_name}: Processing callback data {json.dumps(callback_data, indent=4, ensure_ascii=False)}")
            result = await self._handle_callback(callback_data)
            
            return result
            
        except Exception as e:
            logger.error(f"{self.service_name}: Error processing request: {str(e)}")
            # Only unregister if we got as far as registering (job_id exists in local scope)
            if 'job_id' in locals():
                callback_manager.unregister_handler(job_id)
            raise

class SyncAPIServiceNode(APIServiceNode):
    """Synchronous API service node that processes response immediately"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
    async def _transform_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the API response into the desired output format.
        Must be implemented by child classes.
        
        Args:
            response_data: Raw API response data
            
        Returns:
            Transformed response data in the desired output format
        """
        raise NotImplementedError("_transform_response must be implemented by child classes")
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            # Prepare request data
            request_data = self._prepare_request(self.input_values)
            logger.debug(f"{self.service_name}: Prepared request data: {json.dumps(request_data, indent=4, ensure_ascii=False)}")
            
            # Make request
            response = await self._make_request(request_data)
            logger.debug(f"{self.service_name}: Received response from service: {json.dumps(response, indent=4, ensure_ascii=False)}")
            
            result = await self._transform_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"{self.service_name}: Error processing request: {str(e)}")
            raise
