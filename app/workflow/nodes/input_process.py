from typing import Dict, Any, List, Optional
from app.workflow.base import WorkflowNode
import json

class CreateInputNode(WorkflowNode):
    """创建模型输入对象列表
    例如: "image.jpg" -> [{"type": "image", "url": "image.jpg"}]"""
    
    category = "input"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("url", "string", True)  # URL or file path
        self.add_input_port("type", "string", True)  # Input type (image, audio, video)
        
        # Output ports
        self.add_output_port("output", "array")
        
    async def process(self) -> Dict[str, Any]:
        url = self.input_values["url"]
        input_type = self.input_values["type"]
        
        result = [{
            "type": input_type,
            "url": url
        }]
        
        return {"output": result}

class MergeInputNode(WorkflowNode):
    """合并多个输入对象列表
    例如: 
    list1: [{"type": "image", "url": "a.jpg"}]
    list2: [{"type": "audio", "url": "b.mp3"}]
    ->
    [{"type": "image", "url": "a.jpg"}, {"type": "audio", "url": "b.mp3"}]"""
    
    category = "input"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("input", "array", True)  # Array of input lists
        
        # Output ports
        self.add_output_port("output", "array")
        
    async def process(self) -> Dict[str, Any]:
        input_lists = self.input_values["input"]
        
        if not input_lists:
            raise ValueError("输入列表为空")
            
        # 合并所有输入列表
        result = []
        for input_list in input_lists:
            if not isinstance(input_list, list):
                raise ValueError("输入必须是列表的列表")
            result.extend(input_list)
            
        return {"output": result}
