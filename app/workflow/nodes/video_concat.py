from typing import Dict, Any, List, Optional
from app.workflow.nodes.async_api_service import AsyncAPIServiceNode

class VideoConcatNode(AsyncAPIServiceNode):
    """Node for video concatenation service"""
    
    service_name = "video-concat"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("video_urls", "array", True)
        self.add_input_port("options", "object", False, {})
        
        # Output ports
        self.add_output_port("output_url", "string")
        self.add_output_port("status", "string")
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for the service"""
        payload = {
            "model": "concat-upscale",
            "input": [{"type": "video", "url": url} for url in input_data["video_urls"]],
            "options": input_data.get("options", {}),
            "webhookUrl": input_data.get("callback_url")
        }
        
        return payload
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data"""
        return {
            "output_url": callback_data.get("localUrls", [None])[0],
            "status": callback_data.get("status", "completed")
        }