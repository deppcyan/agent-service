from typing import Dict, Any
from app.workflow.node_api import SyncDigenAPINode


class QwenLLMNode(SyncDigenAPINode):
    """Node for Qwen LLM service"""
    
    service_name = "qwen-llm"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("system_prompt", "string", False, "You are a helpful assistant.")
        self.add_input_port("prompt", "string", True)
        self.add_input_port("max_tokens", "number", False, 256)
        self.add_input_port("temperature", "number", False, 0.7)
        self.add_input_port("top_p", "number", False, 0.9)
        self.add_input_port("model", "string", False, "Qwen3-30B-A3B-Instruct-2507-FP4")
        
        # Output ports
        self.add_output_port("content", "string")
        self.add_output_port("usage", "object")
        self.add_output_port("status", "string")
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for the LLM service"""
        messages = [
            {
                "role": "system",
                "content": input_data.get("system_prompt", "You are a helpful assistant.")
            },
            {
                "role": "user",
                "content": input_data["prompt"]
            }
        ]
        
        request = {
            "model": input_data.get("model", "Qwen3-30B-A3B-Instruct-2507-FP4"),
            "messages": messages,
            "max_tokens": input_data.get("max_tokens", 256),
            "temperature": input_data.get("temperature", 0.7),
            "top_p": input_data.get("top_p", 0.9),
            "stream": False
        }
        
        return request
    
    async def _transform_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the service response into node output format"""
        # Check status first
        if "error" in response_data:
            raise Exception(f"QwenLLM service failed: {response_data['error']}")
            
        # Process the response
        choices = response_data.get("choices", [])
        if not choices:
            raise Exception("No choices in response")
            
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        return {
            "status": "completed",
            "content": content,
            "usage": response_data.get("usage", {})
        }