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


class TypeConvertNode(WorkflowNode):
    """Node that converts values between different data types.
    Supports conversion between float, int, and text types.
    This is a generic conversion node that can handle any type conversion."""
    
    category = "basic_types"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value", "any", True, tooltip="The value to convert (can be any type)")
        self.add_input_port("from_type", "string", True, default_value="text",
                           options=["float", "int", "text"],
                           tooltip="The current type of the input value: float, int, or text")
        self.add_input_port("to_type", "string", True, default_value="text",
                           options=["float", "int", "text"],
                           tooltip="The target type to convert to: float, int, or text")
        self.add_output_port("value", "any", tooltip="The converted value in the target type")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        value = self.input_values["value"]
        from_type = self.input_values["from_type"]
        to_type = self.input_values["to_type"]
        
        # Validate type options
        valid_types = ["float", "int", "text"]
        if from_type not in valid_types:
            raise ValueError(f"Invalid from_type: {from_type}. Must be one of {valid_types}")
        if to_type not in valid_types:
            raise ValueError(f"Invalid to_type: {to_type}. Must be one of {valid_types}")
        
        # If same type, return as-is
        if from_type == to_type:
            return {"value": value}
        
        # First, normalize the input value based on from_type
        try:
            if from_type == "int":
                # Ensure input is an integer
                normalized_value = int(value)
            elif from_type == "float":
                # Ensure input is a float
                normalized_value = float(value)
            elif from_type == "text":
                # Ensure input is a string
                normalized_value = str(value)
            else:
                raise ValueError(f"Unsupported from_type: {from_type}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot normalize value '{value}' as {from_type}: {str(e)}")
        
        # Then convert to target type
        try:
            if to_type == "int":
                # Convert to int (float to int may lose precision)
                result = int(normalized_value)
            elif to_type == "float":
                # Convert to float
                result = float(normalized_value)
            elif to_type == "text":
                # Convert to text (string)
                result = str(normalized_value)
            else:
                raise ValueError(f"Unsupported to_type: {to_type}")
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {from_type} value '{normalized_value}' to {to_type}: {str(e)}")
        
        return {"value": result}

