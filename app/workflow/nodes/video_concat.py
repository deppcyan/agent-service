from typing import Dict, Any, List, Optional
from app.workflow.nodes.async_api_service import AsyncAPIServiceNode

class VideoConcatNode(AsyncAPIServiceNode):
    """Node for video concatenation service"""
    
    service_name = "video-concat"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("video_urls", "array", True)
        self.add_input_port("fps", "number", False, 25)  # Output video frame rate
        self.add_input_port("audio_support", "boolean", False, False)  # Whether to support audio in output video
        
        # Output ports
        self.add_output_port("output_url", "string")
        self.add_output_port("status", "string")
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for the service"""
        # Set model based on audio_support flag
        model = "concat-upscale-audio" if input_data.get("audio_support", False) else "concat-upscale"
        
        payload = {
            "model": model,
            "input": [{"type": "video", "url": url} for url in input_data["video_urls"]],
            "options": {
                "fps": input_data.get("fps", 25)
            },
            "webhookUrl": input_data.get("callback_url")
        }
        
        return payload
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data"""
        return {
            "output_url": callback_data.get("localUrls", [None])[0],
            "status": callback_data.get("status", "completed")
        }