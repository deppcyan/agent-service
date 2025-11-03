from app.workflow.base import WorkflowNode
from typing import Dict, Any
import json


class JsonParseNode(WorkflowNode):
    """将JSON字符串解析为JSON对象"""
    
    category = "json_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("json_string", "string", True, "JSON字符串")
        
        # 输出端口
        self.add_output_port("json_object", "object")  # 解析后的JSON对象
    
    async def process(self) -> Dict[str, Any]:
        """解析JSON字符串"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            json_string = self.input_values["json_string"]
            
            # 兼容性处理：去除可能的代码块标记
            text = json_string.strip()
            if text.startswith("```"):
                # Find the first newline to skip the ```json line
                first_newline = text.find("\n")
                if first_newline != -1:
                    # Find the last ``` and remove it
                    text = text[first_newline:].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
            else:
                text = json_string
            
            # 解析JSON字符串
            parsed_object = json.loads(text)
            
            return {
                "json_object": parsed_object
            }
                    
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {str(e)}")
        except Exception as e:
            raise Exception(f"Error parsing JSON: {str(e)}")


class JsonExtractNode(WorkflowNode):
    """从JSON对象中提取指定字段的值"""
    
    category = "json_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("json_object", "object", True, "JSON对象")
        self.add_input_port("key", "string", True, "要提取的字段名")
        
        # 输出端口
        self.add_output_port("value", "any")  # 提取的值
    
    async def process(self) -> Dict[str, Any]:
        """从JSON对象提取字段值"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            json_object = self.input_values["json_object"]
            key = self.input_values["key"]
            
            # 验证输入是字典
            if not isinstance(json_object, dict):
                raise ValueError("json_object must be a dictionary")
            
            # 提取字段值，如果不存在返回None
            value = json_object.get(key)
            
            return {
                "value": value
            }
                    
        except Exception as e:
            raise Exception(f"Error extracting value: {str(e)}")
