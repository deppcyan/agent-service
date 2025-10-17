import httpx
from typing import Any, Dict, Optional
from ...core.base import ServiceNode, ServiceResponse

class VideoConcatNode(ServiceNode):
    def _get_model_name(self) -> str:
        return "concat-upscale"

    async def generate(self, input_data: Dict[str, Any], webhook_url: Optional[str] = None) -> ServiceResponse:
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "input": [{"type": "video", "url": url} for url in input_data["video_urls"]],
            "options": input_data.get("options", {})
        }
        if webhook_url:
            payload["webhookUrl"] = webhook_url

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/generate",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return ServiceResponse(
                id=data["id"],
                status="pending",
                pod_id=data.get("pod_id"),
                queue_position=data.get("queuePosition"),
                estimated_wait_time=data.get("estimatedWaitTime"),
                pod_url=data.get("pod_url")
            )

    async def cancel(self, job_id: str) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_url}/cancel/{job_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
