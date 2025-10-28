from app.workflow.base import WorkflowNode
from typing import Dict, Any

class TextInputNode(WorkflowNode):
    """Node that passes through text input unchanged.
    This can be used as a starting point or marker in workflows."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_output_port("text", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        return {"text": text}


class IntInputNode(WorkflowNode):
    """Node that handles integer input and validation.
    Can be used to ensure numeric inputs are valid integers."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "number", True, "Integer value")
        self.add_output_port("value", "number")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Ensure value is an integer
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Input value '{value}' cannot be converted to integer")
            
        return {"value": int_value}


class FloatInputNode(WorkflowNode):
    """Node that handles floating point input and validation.
    Can be used to ensure numeric inputs are valid floats."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "number", True, "Float value")
        self.add_output_port("value", "number")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Ensure value is a float
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Input value '{value}' cannot be converted to float")
            
        return {"value": float_value}


class BoolInputNode(WorkflowNode):
    """Node that handles boolean input and validation.
    Can be used to ensure inputs are valid boolean values."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "boolean", True, "Boolean value")
        self.add_output_port("value", "boolean")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Value should already be boolean due to port type,
        # but we'll ensure it explicitly
        return {"value": bool(value)}
