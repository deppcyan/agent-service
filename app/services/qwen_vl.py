import httpx
from typing import Any, Dict, Optional
from app.services.base import AsyncServiceNode

class QwenVLNode(AsyncServiceNode):
    def _get_service_name(self) -> str:
        return "qwen-vl"
        
    def _prepare_request(self, input_data: Dict[str, Any], callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for the service"""
        return {
            "image_url": input_data.get("image_url"),
            "prompt": input_data.get("prompt", ""),
            "system_prompt": input_data.get("system_prompt", ""),
            "seed": input_data.get("seed", 42),
        }
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data"""
        return callback_data  # QwenVL doesn't use callbacks, but we need to implement this
