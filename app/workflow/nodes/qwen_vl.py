from typing import Dict, Any, Optional
from app.workflow.nodes.api_service_base import APIServiceNode

class QwenVLNode(APIServiceNode):
    """Node for QwenVL service"""
    
    service_name = "qwen-vl"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("image_url", "string", True)
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("system_prompt", "string", False, "")
        self.add_input_port("seed", "number", False, 42)
        
        # Output ports
        self.add_output_port("response", "object")
    
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        request_data = {
            "image_url": input_data["image_url"],
            "prompt": input_data.get("prompt", ""),
            "system_prompt": input_data.get("system_prompt", ""),
            "seed": input_data.get("seed", 42)
        }
        
        if callback_url:
            request_data["webhookUrl"] = callback_url
            
        return request_data
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"response": callback_data}