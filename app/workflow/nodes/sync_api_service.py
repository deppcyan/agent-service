from typing import Dict, Any
from app.workflow.nodes.api_service_base import APIServiceNode
from app.utils.logger import logger
import json

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
            
            # Make request
            response = await self._make_request(request_data)
            
            # Transform response
            logger.debug(f"{self.service_name}: Transforming response data: {json.dumps(response, indent=4)}")
            result = await self._transform_response(response)
            
            logger.info(f"{self.service_name}: Request completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"{self.service_name}: Error processing request: {str(e)}")
            raise
