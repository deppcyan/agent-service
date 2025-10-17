from typing import Dict, Any, Optional
from .base import AsyncServiceNode

class WanI2VNode(AsyncServiceNode):
    """WanI2V service node implementation"""
    
    def _get_service_name(self) -> str:
        return "wan-i2v"
    
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for WanI2V service"""
        request = {
            "model": "wan-i2v",
            "input": [{"type": "image", "url": input_data["image_url"]}],
            "options": {
                "prompt": input_data.get("prompt", ""),
                "width": input_data.get("width", 768),
                "height": input_data.get("height", 768),
                "batch_size": input_data.get("batch_size", 1),
                "output_format": input_data.get("output_format", "mp4"),
                "duration": input_data.get("duration", 5),
                "seed": input_data.get("seed", None)
            }
        }
        
        if callback_url:
            request["webhookUrl"] = callback_url
        
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WanI2V service callback"""
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