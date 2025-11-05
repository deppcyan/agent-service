import os
from typing import Dict, Any, Optional
import aiohttp
from abc import ABC, abstractmethod
from asyncio import CancelledError
from app.workflow.base import WorkflowNode
from app.utils.logger import logger
from app.core.callback_manager import callback_manager
from app.utils.utils import get_service_url
from app.core.api_url_config import api_url_config
import json

class BaseDigenAPINode(WorkflowNode, ABC):
    """Base class for Digen API service nodes"""
    
    category = "digen_services"
    
    def __init__(self, service_name: str, node_id: str = None):
        super().__init__(node_id)
        self.service_name = service_name
            
        # Get API key from environment variable
        self.api_key = os.getenv("DIGEN_SERVICES_API_KEY")
        if not self.api_key:
            raise ValueError("DIGEN_SERVICES_API_KEY environment variable not set")
        
    def get_api_url(self) -> str:
        """Get API URL for the service from configuration"""
        api_url = api_url_config.get_api_url(self.service_name)
        if not api_url:
            raise ValueError(f"API URL not found for service '{self.service_name}' in current environment")
        return api_url
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for the service. Must be implemented by child classes."""
        raise NotImplementedError("_prepare_request must be implemented by child classes")
        
    async def _make_request(self, data: Dict[str, Any], method: str = "POST", url: Optional[str] = None) -> Dict[str, Any]:
        """Make HTTP request to service"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        if url is None:
            url = self.get_api_url()
        
        async with aiohttp.ClientSession() as session:
            logger.info(f"{self.service_name}: Making {method} request to {url}")
            request_method = getattr(session, method.lower())
            async with request_method(url, headers=headers, json=data if method == "POST" else None) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"{self.service_name}: Service request failed: {error_text}")
                    raise Exception(f"Service call failed with status {response.status}: {error_text}")
                    
                response_data = await response.json()
                logger.info(f"{self.service_name}: Received response from service")
                return response_data

class AsyncDigenAPINode(BaseDigenAPINode):
    """Asynchronous Digen API service node that waits for callback"""
    
    def __init__(self, service_name: str, node_id: str = None):
        super().__init__(service_name, node_id)
        # Add callback-related input ports
        # callback_url is now automatically set from get_service_url()
        # cancel_url is now automatically constructed from response pod_url
        self.add_input_port("timeout", "number", False, default_value=60)
        
        # Initialize cancel_url variable
        self.cancel_url = None
    
    def get_callback_url(self) -> str:
        """Get the callback URL for this node"""
        return f"{get_service_url()}/webhook"
         
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data with callback URL.
        Must be implemented by child classes to include callback URL in request data.
        Use self.get_callback_url() to get the automatically generated callback URL.
        
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
        
    async def _cancel_job(self, job_id: str) -> None:
        """Cancel a running job by making a request to the cancel URL"""
        
        # Only cancel if we have a cancel URL from the response
        if not hasattr(self, 'cancel_url') or not self.cancel_url:
            logger.info(f"{self.service_name}: No cancel URL available, cannot cancel job {job_id}")
            raise CancelledError()
        
        cancel_url = f"{self.cancel_url}/{job_id}"
        
        try:
            await self._make_request({"job_id": job_id}, method="POST", url=cancel_url)
            logger.info(f"{self.service_name}: Successfully cancelled job {job_id}")
        except Exception as e:
            logger.error(f"{self.service_name}: Failed to cancel job {job_id}: {str(e)}")
            # We still want to raise CancelledError even if the cancel request failed
            # This ensures the workflow knows the task was cancelled
            raise CancelledError()
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        # Get timeout (callback URL is now automatically generated)
        timeout = self.input_values.get("timeout")
        logger.info(f"{self.service_name}: Using timeout value: {timeout} seconds")
        logger.info(f"{self.service_name}: Using callback URL: {self.get_callback_url()}")
        
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
            
            # Extract pod_url from response and construct cancel URL
            if response.get("pod_url"):
                pod_url = response["pod_url"].rstrip('/')
                self.cancel_url = f"{pod_url}/cancel"
                logger.info(f"{self.service_name}: Using cancel URL: {self.cancel_url}")
            else:
                # No pod_url in response means no cancellation capability
                self.cancel_url = None
                logger.info(f"{self.service_name}: No pod_url in response, cancellation not available")
            
            callback_manager.register_handler(
                job_id,
                self._handle_callback
            )
            
            callback_data = await callback_manager.wait_for_callback(job_id, timeout)
            
            # Handle callback data
            logger.debug(f"{self.service_name}: Processing callback data {json.dumps(callback_data, indent=4, ensure_ascii=False)}")
            result = await self._handle_callback(callback_data)
            
            return result
            
        except CancelledError:
            logger.info(f"{self.service_name}: Operation cancelled")
            # Only unregister and cancel if we got as far as registering (job_id exists in local scope)
            if 'job_id' in locals():
                callback_manager.unregister_handler(job_id)
                await self._cancel_job(job_id)
            raise
        except Exception as e:
            logger.error(f"{self.service_name}: Error processing request: {str(e)}")
            # Only unregister if we got as far as registering (job_id exists in local scope)
            if 'job_id' in locals():
                callback_manager.unregister_handler(job_id)
            raise

class SyncDigenAPINode(BaseDigenAPINode):
    """Synchronous Digen API service node that processes response immediately"""
    
    def __init__(self, service_name: str, node_id: str = None):
        super().__init__(service_name, node_id)
        
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
