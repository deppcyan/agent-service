from typing import Dict, Any, List, Union, Optional, Literal
from enum import Enum
from app.workflow.api_base import AsyncDigenAPINode
from app.utils.logger import logger

class InputType(str, Enum):
    """Supported input types for model service"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class ModelInput:
    """Model input data validator"""
    def __init__(self, input_data: List[Dict[str, str]]):
        self.input_data = input_data
        
    def validate(self) -> bool:
        """Validate input data format"""
        if not isinstance(self.input_data, list):
            raise ValueError("Input must be a list of input objects")
            
        for item in self.input_data:
            if not isinstance(item, dict):
                raise ValueError("Each input item must be a dictionary")
                
            if "type" not in item or "url" not in item:
                raise ValueError("Each input item must have 'type' and 'url' fields")
                
            if item["type"] not in [t.value for t in InputType]:
                raise ValueError(f"Input type must be one of: {[t.value for t in InputType]}")
                
            if not isinstance(item["url"], str):
                raise ValueError("URL must be a string")
                
        return True

class ModelServiceNode(AsyncDigenAPINode):
    """Node for general model service that supports various models"""
    
    def __init__(self, node_id: str = None):
        super().__init__("model-service", node_id)
        
        # Required input ports
        self.add_input_port("model", "string", True)  # Model name/identifier
        self.add_input_port("input", "array", True)  # Array of input objects
        
        # Optional input ports for common options
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("audio_prompt", "string", False, "")
        self.add_input_port("negative_prompt", "string", False, "")
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        self.add_input_port("batch_size", "number", False, 1)
        self.add_input_port("output_format", "string", False, None)
        self.add_input_port("seed", "number", False, None)
        self.add_input_port("extra_options", "object", False, {})  # For model-specific options
        
        # Output ports
        self.add_output_port("local_urls", "array")  # List of local output URLs
        self.add_output_port("wasabi_urls", "array")  # List of Wasabi output URLs
        self.add_output_port("aws_urls", "array")  # List of AWS output URLs
        self.add_output_port("options", "object")  # Options used for generation
        self.add_output_port("status", "string")  # Status of the request
        self.add_output_port("metadata", "object")  # Additional metadata from the model
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for model service"""
        # Validate input format
        model_input = ModelInput(input_data["input"])
        model_input.validate()
        
        # Basic options that are common across models
        options = {
            "prompt": input_data.get("prompt", ""),
            "negative_prompt": input_data.get("negative_prompt", ""),
            "audio_prompt": input_data.get("audio_prompt", ""),
            "width": input_data.get("width", 768),
            "height": input_data.get("height", 768),
            "batch_size": input_data.get("batch_size", 1),
            "seed": input_data.get("seed")
        }
        
        # Add output format if specified
        if input_data.get("output_format"):
            options["output_format"] = input_data["output_format"]
            
        # Add any extra model-specific options
        extra_options = input_data.get("extra_options", {})
        options.update(extra_options)
        
        # Construct the request
        request = {
            "model": input_data["model"],
            "input": input_data["input"],
            "options": options,
            "webhookUrl": input_data.get("callback_url")
        }
        
        logger.debug(f"Prepared request for model {input_data['model']}: {request}")
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle model service callback"""
        status = callback_data.get("status")
        
        if status == "completed":
            # Get all output URLs
            return {
                "status": "completed",
                "local_urls": callback_data.get("local_outputs", []),
                "wasabi_urls": callback_data.get("wasabi_outputs", []),
                "aws_urls": callback_data.get("outputs", []),
                "options": callback_data.get("options", {}),
                "metadata": callback_data.get("metadata", {})
            }
        elif status == "failed":
            error_msg = callback_data.get("error", "Unknown error")
            logger.error(f"Model service failed: {error_msg}")
            raise Exception(error_msg)
        else:
            raise Exception(f"Unexpected status: {status}")
