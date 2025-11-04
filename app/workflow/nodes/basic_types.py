from app.workflow.base import WorkflowNode
from typing import Dict, Any
import json
import re

class TextInputNode(WorkflowNode):
    """Node that passes through text input unchanged.
    This can be used as a starting point or marker in workflows."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Enter the text content that will be passed through unchanged")
        self.add_output_port("text", "string", tooltip="The same text that was provided as input")
    
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
        self.add_input_port("value", "number", True, default_value=0, tooltip="Enter an integer number (whole number without decimal places)")
        self.add_output_port("value", "number", tooltip="The same integer value that was provided as input")
    
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
        self.add_input_port("value", "number", True, default_value=0.0, tooltip="Enter a decimal number (number with decimal places)")
        self.add_output_port("value", "number", tooltip="The same decimal value that was provided as input")
    
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
        self.add_input_port("value", "boolean", True, default_value=False, tooltip="Boolean value (true or false)")
        self.add_output_port("value", "boolean", tooltip="The same boolean value that was provided as input")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Value should already be boolean due to port type,
        # but we'll ensure it explicitly
        return {"value": bool(value)}


class IntToTextNode(WorkflowNode):
    """Node that converts integer input to text output.
    Useful for formatting numbers as strings in workflows."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "number", True, tooltip="Integer value to convert to text")
        self.add_output_port("text", "string", tooltip="Text representation of the integer value")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Ensure value is an integer and convert to string
        try:
            int_value = int(value)
            text_value = str(int_value)
        except (ValueError, TypeError):
            raise ValueError(f"Input value '{value}' cannot be converted to integer")
            
        return {"text": text_value}


class FloatToTextNode(WorkflowNode):
    """Node that converts float input to text output.
    Useful for formatting decimal numbers as strings in workflows."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "number", True, tooltip="Float value to convert to text")
        self.add_output_port("text", "string", tooltip="Text representation of the float value")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        value = self.input_values["value"]
        
        # Ensure value is a float and convert to string
        try:
            float_value = float(value)
            text_value = str(float_value)
        except (ValueError, TypeError):
            raise ValueError(f"Input value '{value}' cannot be converted to float")
            
        return {"text": text_value}


class MathOperationNode(WorkflowNode):
    """Node that performs basic mathematical operations on two numbers.
    Supports addition, subtraction, multiplication, and division.
    Accepts both integers and floating-point numbers as input."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("a", "number", True, default_value=0, tooltip="First number operand (integer or float)")
        self.add_input_port("b", "number", True, default_value=0, tooltip="Second number operand (integer or float)")
        self.add_input_port("operation", "string", True, default_value="add", 
                           options=["add", "subtract", "multiply", "divide"],
                           tooltip="Mathematical operation to perform: add (+), subtract (-), multiply (*), divide (/)")
        self.add_output_port("result", "number", tooltip="Result of the mathematical operation")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        a = self.input_values["a"]
        b = self.input_values["b"]
        operation = self.input_values["operation"]
        
        # Convert values to numbers (int or float)
        try:
            # Try to convert to float first to handle both int and float inputs
            num_a = float(a)
            num_b = float(b)
            
            # If the float values are whole numbers, convert to int for cleaner output
            if num_a.is_integer():
                num_a = int(num_a)
            if num_b.is_integer():
                num_b = int(num_b)
                
        except (ValueError, TypeError):
            raise ValueError(f"Input values must be convertible to numbers: a='{a}', b='{b}'")
        
        # Perform the operation
        if operation == "add":
            result = num_a + num_b
        elif operation == "subtract":
            result = num_a - num_b
        elif operation == "multiply":
            result = num_a * num_b
        elif operation == "divide":
            if num_b == 0:
                raise ValueError("Division by zero is not allowed")
            result = num_a / num_b
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # If result is a whole number, return as int for cleaner output
        if isinstance(result, float) and result.is_integer():
            result = int(result)
            
        return {"result": result}


class TextToDictNode(WorkflowNode):
    """Node that converts text input to dictionary output.
    Supports JSON string parsing and key-value pair parsing with customizable separators."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to convert to dictionary (JSON string or key-value pairs)")
        self.add_input_port("format", "string", False, "json", 
                           options=["json", "key_value"],
                           tooltip="Format of input text: 'json' for JSON string, 'key_value' for key-value pairs")
        self.add_input_port("separator", "string", False, "\n",
                           tooltip="Separator for key-value pairs (default: newline). Only used when format is 'key_value'")
        self.add_input_port("key_value_delimiter", "string", False, ":",
                           tooltip="Delimiter between key and value (default: colon). Only used when format is 'key_value'")
        self.add_output_port("dict", "any", tooltip="Dictionary parsed from the input text")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        format_type = self.input_values.get("format", "json")
        separator = self.input_values.get("separator", "\n")
        key_value_delimiter = self.input_values.get("key_value_delimiter", ":")
        
        try:
            if format_type == "json":
                # Parse as JSON
                result_dict = json.loads(text)
                if not isinstance(result_dict, dict):
                    raise ValueError("JSON text must represent a dictionary/object")
            
            elif format_type == "key_value":
                # Parse as key-value pairs
                result_dict = {}
                lines = text.split(separator)
                
                for line in lines:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    
                    if key_value_delimiter not in line:
                        raise ValueError(f"Line '{line}' does not contain delimiter '{key_value_delimiter}'")
                    
                    key, value = line.split(key_value_delimiter, 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Try to parse value as JSON for nested structures
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        # If not valid JSON, keep as string
                        pass
                    
                    result_dict[key] = value
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing text to dictionary: {str(e)}")
            
        return {"dict": result_dict}


class TextToListNode(WorkflowNode):
    """Node that converts text input to list output.
    Supports JSON array parsing and delimiter-based splitting with customizable separators."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to convert to list (JSON array or delimited string)")
        self.add_input_port("format", "string", False, "json",
                           options=["json", "delimited"],
                           tooltip="Format of input text: 'json' for JSON array, 'delimited' for separated values")
        self.add_input_port("delimiter", "string", False, ",",
                           tooltip="Delimiter for splitting text (default: comma). Only used when format is 'delimited'")
        self.add_input_port("trim_items", "boolean", False, True,
                           tooltip="Whether to trim whitespace from each item. Only used when format is 'delimited'")
        self.add_input_port("skip_empty", "boolean", False, True,
                           tooltip="Whether to skip empty items after splitting. Only used when format is 'delimited'")
        self.add_output_port("list", "any", tooltip="List parsed from the input text")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        format_type = self.input_values.get("format", "json")
        delimiter = self.input_values.get("delimiter", ",")
        trim_items = self.input_values.get("trim_items", True)
        skip_empty = self.input_values.get("skip_empty", True)
        
        try:
            if format_type == "json":
                # Parse as JSON array
                result_list = json.loads(text)
                if not isinstance(result_list, list):
                    raise ValueError("JSON text must represent an array/list")
            
            elif format_type == "delimited":
                # Split by delimiter
                items = text.split(delimiter)
                result_list = []
                
                for item in items:
                    if trim_items:
                        item = item.strip()
                    
                    if skip_empty and not item:
                        continue
                    
                    # Try to parse item as JSON for nested structures
                    try:
                        parsed_item = json.loads(item)
                        result_list.append(parsed_item)
                    except (json.JSONDecodeError, ValueError):
                        # If not valid JSON, keep as string
                        result_list.append(item)
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing text to list: {str(e)}")
            
        return {"list": result_list}


# 使用示例：

"""
# TextToDictNode 示例

# 1. JSON 格式转换
text_to_dict_node = TextToDictNode()
text_to_dict_node.input_values = {
    "text": '{"name": "John", "age": 30, "city": "New York"}',
    "format": "json"
}
result = await text_to_dict_node.process()
# 输出: {"dict": {"name": "John", "age": 30, "city": "New York"}}

# 2. 键值对格式转换（默认分隔符）
text_to_dict_node.input_values = {
    "text": "name: John\nage: 30\ncity: New York",
    "format": "key_value",
    "separator": "\n",
    "key_value_delimiter": ":"
}
result = await text_to_dict_node.process()
# 输出: {"dict": {"name": "John", "age": "30", "city": "New York"}}

# 3. 键值对格式转换（自定义分隔符）
text_to_dict_node.input_values = {
    "text": "name=John|age=30|city=New York",
    "format": "key_value",
    "separator": "|",
    "key_value_delimiter": "="
}
result = await text_to_dict_node.process()
# 输出: {"dict": {"name": "John", "age": "30", "city": "New York"}}

# TextToListNode 示例

# 1. JSON 数组格式转换
text_to_list_node = TextToListNode()
text_to_list_node.input_values = {
    "text": '["apple", "banana", "orange"]',
    "format": "json"
}
result = await text_to_list_node.process()
# 输出: {"list": ["apple", "banana", "orange"]}

# 2. 分隔符格式转换（默认逗号分隔）
text_to_list_node.input_values = {
    "text": "apple, banana, orange",
    "format": "delimited",
    "delimiter": ",",
    "trim_items": True,
    "skip_empty": True
}
result = await text_to_list_node.process()
# 输出: {"list": ["apple", "banana", "orange"]}

# 3. 分隔符格式转换（自定义分隔符）
text_to_list_node.input_values = {
    "text": "apple|banana|orange",
    "format": "delimited",
    "delimiter": "|",
    "trim_items": True,
    "skip_empty": True
}
result = await text_to_list_node.process()
# 输出: {"list": ["apple", "banana", "orange"]}

# 4. 混合数据类型（JSON 解析）
text_to_list_node.input_values = {
    "text": '"hello", 123, true, {"key": "value"}',
    "format": "delimited",
    "delimiter": ",",
    "trim_items": True,
    "skip_empty": True
}
result = await text_to_list_node.process()
# 输出: {"list": ["hello", 123, true, {"key": "value"}]}
"""

