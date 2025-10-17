from typing import Dict, Any, Optional
from .base import AsyncServiceNode

class QwenEditNode(AsyncServiceNode):
    """QwenEdit service node implementation"""
    
    def _get_service_name(self) -> str:
        return "qwen-edit"
    
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for QwenEdit service"""
        request = {
            "model": "qwen-edit",
            "input": [{"type": "image", "url": input_data["image_url"]}],
            "options": {
                "prompt": input_data.get("prompt", ""),
                "width": input_data.get("width", 768),
                "height": input_data.get("height", 768)
            }
        }
        
        if callback_url:
            request["webhookUrl"] = callback_url
        
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle QwenEdit service callback"""
        status = callback_data.get("status")
        if status == "completed":
            return {
                "status": "completed",
                "output_url": callback_data.get("localUrl", [None])[0],
                "options": callback_data.get("options", {})
            }
        elif status == "failed":
            raise Exception(callback_data.get("error", "Unknown error"))
        else:
            raise Exception(f"Unexpected status: {status}")