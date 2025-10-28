from typing import Dict, Any, Optional
from app.workflow.api_base import AsyncAPIServiceNode

class WanTalkNode(AsyncAPIServiceNode):
    """Node for WanTalk (Talking Head) service"""
    
    service_name = "wan-talk"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("image_url", "string", True)
        self.add_input_port("audio_url", "string", True)
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("audio_prompt", "string", False, "")
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        self.add_input_port("batch_size", "number", False, 1)
        self.add_input_port("output_format", "string", False, "mp4")
        self.add_input_port("duration", "number", False, 5)
        self.add_input_port("seed", "number", False, None)
        
        # Output ports
        self.add_output_port("output_url", "string")
        self.add_output_port("options", "object")
        self.add_output_port("status", "string")
    
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for WanTalk service"""
        request = {
            "model": "wan-talk",
            "input": [{"type": "image", "url": input_data["image_url"]}, {"type": "audio", "url": input_data["audio_url"]}],
            "options": {
                "prompt": input_data.get("prompt", ""),
                "audio_prompt": input_data.get("audio_prompt", ""),
                "width": input_data.get("width", 768),
                "height": input_data.get("height", 768),
                "batch_size": input_data.get("batch_size", 1),
                "output_format": input_data.get("output_format", "mp4"),
                "duration": input_data.get("duration", 5),
                "seed": input_data.get("seed")
            },
            "webhookUrl": input_data.get("callback_url")
        }
        
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WanTalk service callback"""
        status = callback_data.get("status")
        if status == "completed":
            return {
                "status": "completed",
                "output_url": callback_data.get("localUrls", [None])[0],
                "options": callback_data.get("options", {})
            }
        elif status == "failed":
            raise Exception(callback_data.get("error", "Unknown error"))
        else:
            raise Exception(f"Unexpected status: {status}")
