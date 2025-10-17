import httpx
from typing import Any, Dict, Optional
from app.core.base import ServiceNode, ServiceResponse

class QwenVLNode(ServiceNode):
    def _get_model_name(self) -> str:
        return "qwen-vl"

    async def generate(self, input_data: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/generate",
                headers=headers,
                json={
                    "image_url": input_data.get("image_url"),
                    "prompt": input_data.get("prompt", ""),
                    "system_prompt": input_data.get("system_prompt", "")
                }
            )
            response.raise_for_status()
            return response.json()

    async def cancel(self, job_id: str) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_url}/cancel/{job_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
