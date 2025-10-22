from typing import Dict, Any
from app.workflow.base import WorkflowNode


class TextCombinerNode(WorkflowNode):
    """Node for combining text using a template prompt with variables"""
    
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
