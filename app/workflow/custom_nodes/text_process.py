from app.workflow.base import WorkflowNode
from typing import Dict, Any, List

class TextToListNode(WorkflowNode):
    """Custom node that converts a single text string into a single-element list"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_output_port("list", "array")  # Output will be string array
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        
        # Convert single text into single-element list
        return {
            "list": [text]
        }


class ListToTextNode(WorkflowNode):
    """Custom node that converts a list into a single text string by taking the first element"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True)  # Input will be string array
        self.add_output_port("text", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        
        if not input_list:
            raise ValueError("Input list is empty")
            
        # Take first element from list and convert to text
        return {
            "text": input_list[0]
        }
