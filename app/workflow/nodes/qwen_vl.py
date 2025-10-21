from typing import Dict, Any
from app.workflow.nodes.sync_api_service import SyncAPIServiceNode

class QwenVLNode(SyncAPIServiceNode):
    """Node for QwenVL service"""
    
    service_name = "qwen-vl"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("image_url", "string", True)
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("system_prompt", "string", False, "")
        self.add_input_port("seed", "number", False, 42)
        self.add_input_port("max_tokens", "number", False, 1024)  # Maximum number of tokens for text processing
        
        # Output ports
        self.add_output_port("response", "string")
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "image_url": input_data["image_url"],
            "prompt": input_data.get("prompt", ""),
            "system_prompt": input_data.get("system_prompt", ""),
            "seed": input_data.get("seed", 42),
            "max_tokens": input_data.get("max_tokens", 1024)
        }
    
    async def _transform_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        # Check status first
        status = response_data.get("status")
        if status != "success":
            error_msg = response_data.get("error", "Unknown error")
            raise Exception(f"QwenVL service failed: {error_msg}")
            
        # Extract enhanced_prompt
        enhanced_prompt = response_data.get("enhanced_prompt")
        if not enhanced_prompt:
            raise Exception("No enhanced_prompt in response")
            
        return {
            "response": enhanced_prompt
        }