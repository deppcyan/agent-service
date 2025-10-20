from ..base import WorkflowNode
from typing import Dict, Any

class TextConcatenateNode(WorkflowNode):
    """Node that concatenates two text inputs"""
    
    category = "text"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text1", "string", True)
        self.add_input_port("text2", "string", True)
        self.add_input_port("separator", "string", False, " ")
        self.add_output_port("result", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text1 = self.input_values["text1"]
        text2 = self.input_values["text2"]
        separator = self.input_values.get("separator", " ")
        
        result = f"{text1}{separator}{text2}"
        return {"result": result}

class TextUppercaseNode(WorkflowNode):
    """Node that converts text to uppercase"""
    
    category = "text"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_output_port("result", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        return {"result": text.upper()}
