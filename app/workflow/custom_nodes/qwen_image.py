from typing import Dict, Any, Optional
from app.workflow.api_base import AsyncAPIServiceNode

class QwenImageNode(AsyncAPIServiceNode):
    """Node for QwenImage service"""
    
    service_name = "qwen-image"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        
        # Output ports
        self.add_output_port("output_url", "string")
        self.add_output_port("options", "object")
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        request = {
            "model": "qwen-image",
            "options": {
                "prompt": input_data.get("prompt", ""),
                "width": input_data.get("width", 768),
                "height": input_data.get("height", 768)
            },
            "webhookUrl": input_data.get("callback_url")
        }
        
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        status = callback_data.get("status")
        if status == "completed":
            return {
                "output_url": callback_data.get("localUrls", [None])[0],
                "options": callback_data.get("options", {})
            }
        elif status == "failed":
            raise Exception(callback_data.get("error", "Unknown error"))
        else:
            raise Exception(f"Unexpected status: {status}")
