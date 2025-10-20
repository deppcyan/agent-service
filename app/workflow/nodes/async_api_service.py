from typing import Dict, Any, Optional
from app.workflow.nodes.api_service_base import APIServiceNode
from app.utils.logger import logger
from app.core.callback_manager import callback_manager

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
            
            # Register callback handler
            logger.debug(f"Registering callback handler for URL: {callback_url}",
                       extra={"service": self.service_name})
            callback_manager.register_handler(
                self.service_name,
                self.node_id,
                self._handle_callback
            )
            
            # Make request
            await self._make_request(request_data)
            
            # Wait for callback
            logger.info("Waiting for callback",
                      extra={"service": self.service_name})
            callback_data = await callback_manager.wait_for_callback(self.node_id, timeout)
            
            # Handle callback data
            logger.debug("Processing callback data",
                       extra={"service": self.service_name})
            result = await self._handle_callback(callback_data)
            
            logger.info("Request completed successfully",
                      extra={"service": self.service_name})
            return result
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}",
                       extra={"service": self.service_name})
            callback_manager.unregister_handler(self.node_id)
            raise
