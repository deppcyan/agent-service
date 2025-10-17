import httpx
from typing import Any, Dict, Optional
from app.services.base import AsyncServiceNode

class VideoConcatNode(AsyncServiceNode):
    def _get_service_name(self) -> str:
        return "concat-upscale"
        
    def _prepare_request(self, input_data: Dict[str, Any], callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for the service"""
        payload = {
            "model": self.service_name,
            "input": [{"type": "video", "url": url} for url in input_data["video_urls"]],
            "options": input_data.get("options", {})
        }
        if callback_url:
            payload["webhookUrl"] = callback_url
        return payload
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data"""
        # 视频拼接服务会返回最终的视频URL
        return {
            "output_url": callback_data.get("output_url"),
            "status": callback_data.get("status", "completed")
        }
