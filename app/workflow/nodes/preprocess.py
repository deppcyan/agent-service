from app.workflow.base import WorkflowNode
from typing import Dict, Any, List
import random

class PreprocessNode(WorkflowNode):
    """Node that preprocesses user input and options for downstream nodes"""
    
    category = "preprocessing"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("input", "list", True)  # List of InputItems
        self.add_input_port("options", "dict", True)  # Options object
        
        # Input type output ports
        self.add_output_port("image_url", "string")
        self.add_output_port("image_urls", "list")
        self.add_output_port("video_url", "string")
        self.add_output_port("video_urls", "list")
        self.add_output_port("audio_url", "string")
        self.add_output_port("audio_urls", "list")
        
        # Options output ports
        self.add_output_port("prompt", "string")
        self.add_output_port("seed", "number")
        self.add_output_port("duration", "number")
        self.add_output_port("upload_url", "string")
        self.add_output_port("upload_wasabi_url", "string")
        self.add_output_port("resolution", "string")
        self.add_output_port("crf", "number")
        self.add_output_port("width", "number")
        self.add_output_port("height", "number")
    
    def _consolidate_inputs(self, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate inputs of the same type into single/list parameters"""
        type_map = {}
        
        # Group inputs by type
        for item in inputs:
            item_type = item.get("type")
            if item_type not in type_map:
                type_map[item_type] = []
            type_map[item_type].append(item.get("url"))
        
        # Convert to singular/plural form based on count
        result = {}
        for item_type, values in type_map.items():
            if len(values) == 1:
                # Single item - use singular form (e.g., image_url)
                result[f"{item_type}_url"] = values[0]
            else:
                # Multiple items - use plural form (e.g., image_urls)
                result[f"{item_type}_urls"] = values
                
        return result
    
    def _process_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process options and handle special cases like seed"""
        processed_options = dict(options)  # Create a copy to avoid modifying original
        
        # Generate random seed if not provided
        if "seed" not in processed_options or processed_options["seed"] is None:
            processed_options["seed"] = random.randint(1, 1000000)
            
        return processed_options
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["input"]
        options = self.input_values["options"]
        
        # Process inputs and options
        consolidated_inputs = self._consolidate_inputs(input_list)
        processed_options = self._process_options(options)
        
        # Initialize output with None values
        output = {
            "image_url": None,
            "image_urls": None,
            "video_url": None,
            "video_urls": None,
            "audio_url": None,
            "audio_urls": None,
            "prompt": processed_options.get("prompt"),
            "seed": processed_options.get("seed"),
            "duration": processed_options.get("duration"),
            "upload_url": processed_options.get("upload_url"),
            "upload_wasabi_url": processed_options.get("upload_wasabi_url"),
            "resolution": processed_options.get("resolution"),
            "crf": processed_options.get("crf"),
            "width": processed_options.get("width"),
            "height": processed_options.get("height")
        }
        
        # Update with consolidated inputs
        output.update(consolidated_inputs)
        
        # Remove None values
        return {k: v for k, v in output.items() if v is not None}
