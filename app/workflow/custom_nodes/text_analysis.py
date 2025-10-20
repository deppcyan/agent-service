from app.workflow.base import WorkflowNode
from typing import Dict, Any

class WordCountNode(WorkflowNode):
    """Custom node that counts words in text"""
    
    category = "text_analysis"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_output_port("word_count", "number")
        self.add_output_port("char_count", "number")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        words = text.split()
        
        return {
            "word_count": len(words),
            "char_count": len(text)
        }
