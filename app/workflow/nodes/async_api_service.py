from typing import Dict, Any, Optional
from app.workflow.nodes.api_service_base import APIServiceNode
from app.utils.logger import logger
from app.core.callback_manager import callback_manager
import json

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
        callback_url = self.input_values["callback_url"]
        timeout = self.input_values.get("timeout")
        
        try:
            # Prepare request data
            request_data = self._prepare_request(self.input_values)
            
            # Make request first to get job id
            response = await self._make_request(request_data)
            
            # Extract job id from response
            if not response.get("id"):
                raise ValueError("No job id returned from service")
            job_id = response["id"]
            logger.info(f"{self.service_name}: Got job id: {job_id}")
            
            # Register callback handler with job id
            logger.debug(f"{self.service_name}: Registering callback handler for job: {job_id}")
            callback_manager.register_handler(
                job_id,
                self._handle_callback
            )
            
            # Wait for callback
            logger.info(f"{self.service_name}: Waiting for callback for job: {job_id}")
            callback_data = await callback_manager.wait_for_callback(job_id, timeout)
            
            # Handle callback data
            logger.debug(f"{self.service_name}: Processing callback data {json.dumps(callback_data, indent=4)}")
            result = await self._handle_callback(callback_data)
            
            logger.info("{self.service_name}: Request completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"{self.service_name}: Error processing request: {str(e)}")
            # Only unregister if we got as far as registering (job_id exists in local scope)
            if 'job_id' in locals():
                callback_manager.unregister_handler(job_id)
            raise
