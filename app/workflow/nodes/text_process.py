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


class InputTextNode(WorkflowNode):
    """Custom node that passes through text input unchanged.
    This can be used as a starting point or marker in workflows."""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_output_port("text", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        
        # Simply pass through the input text
        return {
            "text": text
        }


class TextCombinerNode(WorkflowNode):
    """Node for combining text using a template prompt with variables"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("prompt", "string", True, "Template with variables like {text_a}, {text_b}, {text_c}")
        self.add_input_port("text_a", "string", False, "")
        self.add_input_port("text_b", "string", False, "")
        self.add_input_port("text_c", "string", False, "")
        
        # Output ports
        self.add_output_port("combined_text", "string")
        self.add_output_port("used_variables", "object")
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            prompt = self.input_values.get("prompt", "")
            text_a = self.input_values.get("text_a", "")
            text_b = self.input_values.get("text_b", "")
            text_c = self.input_values.get("text_c", "")
            
            # Track which variables were actually used in the prompt
            used_vars = {
                "text_a": "{text_a}" in prompt,
                "text_b": "{text_b}" in prompt,
                "text_c": "{text_c}" in prompt
            }
            
            # Format the prompt with the provided text values
            combined_text = prompt.format(
                text_a=text_a,
                text_b=text_b,
                text_c=text_c
            )
            
            return {
                "combined_text": combined_text,
                "used_variables": used_vars
            }
            
        except KeyError as e:
            raise ValueError(f"Invalid variable name in prompt: {str(e)}")
        except Exception as e:
            raise Exception(f"Error combining text: {str(e)}")
