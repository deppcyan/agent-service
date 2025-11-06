from app.workflow.base import WorkflowNode
from typing import Dict, Any, List, Union


class ListRangeNode(WorkflowNode):
    """Node that extracts a range of elements from a list.
    Supports Python-style slicing with start and end indices."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True, tooltip="Input list to extract range from")
        self.add_input_port("start", "number", False, default_value=0, tooltip="Start index (inclusive, default: 0)")
        self.add_input_port("end", "number", False, default_value=None, tooltip="End index (exclusive, default: end of list)")
        self.add_output_port("result", "array", tooltip="List containing elements from start to end index")
        self.add_output_port("length", "number", tooltip="Length of the resulting list")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        start_value = self.input_values.get("start", 0)
        start = int(start_value) if start_value is not None else 0
        end = self.input_values.get("end")
        
        if not isinstance(input_list, list):
            raise ValueError("Input must be a list")
        
        # Handle negative indices
        list_length = len(input_list)
        if start < 0:
            start = max(0, list_length + start)
        
        if end is not None:
            end = int(end)
            if end < 0:
                end = max(0, list_length + end)
        else:
            end = list_length
        
        # Extract range
        result = input_list[start:end]
        
        return {
            "result": result,
            "length": len(result)
        }


class ListIndexNode(WorkflowNode):
    """Node that gets the value at a specific index in a list.
    Supports negative indices for accessing from the end."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True, tooltip="Input list to get value from")
        self.add_input_port("index", "number", True, default_value=0, tooltip="Index of the element to retrieve (supports negative indices)")
        self.add_output_port("value", "any", tooltip="Value at the specified index")
        self.add_output_port("exists", "boolean", tooltip="Whether the index exists in the list")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        index_value = self.input_values.get("index", 0)
        index = int(index_value) if index_value is not None else 0
        
        if not isinstance(input_list, list):
            raise ValueError("Input must be a list")
        
        # Check if index is valid
        list_length = len(input_list)
        
        # Handle negative indices
        actual_index = index
        if index < 0:
            actual_index = list_length + index
        
        # Check bounds
        if actual_index < 0 or actual_index >= list_length:
            return {
                "value": None,
                "exists": False
            }
        
        return {
            "value": input_list[actual_index],
            "exists": True
        }


class ListConcatNode(WorkflowNode):
    """Node that concatenates two lists into a single list.
    The second list is appended to the end of the first list."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list_a", "array", True, tooltip="First list")
        self.add_input_port("list_b", "array", True, tooltip="Second list to concatenate")
        self.add_output_port("result", "array", tooltip="Combined list (list_a + list_b)")
        self.add_output_port("length", "number", tooltip="Length of the combined list")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        list_a = self.input_values["list_a"]
        list_b = self.input_values["list_b"]
        
        if not isinstance(list_a, list):
            raise ValueError("list_a must be a list")
        if not isinstance(list_b, list):
            raise ValueError("list_b must be a list")
        
        # Concatenate lists
        result = list_a + list_b
        
        return {
            "result": result,
            "length": len(result)
        }


class ListAppendNode(WorkflowNode):
    """Node that appends a single value to a list.
    Creates a new list with the value added at the end."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True, tooltip="Input list to append to")
        self.add_input_port("value", "any", True, tooltip="Value to append to the list")
        self.add_output_port("result", "array", tooltip="New list with the value appended")
        self.add_output_port("length", "number", tooltip="Length of the resulting list")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        value = self.input_values["value"]
        
        if not isinstance(input_list, list):
            raise ValueError("Input must be a list")
        
        # Create new list with appended value
        result = input_list.copy()
        result.append(value)
        
        return {
            "result": result,
            "length": len(result)
        }


class ListCreateNode(WorkflowNode):
    """Node that creates a new list from individual values.
    Useful for building lists from separate inputs."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("value_1", "any", False, tooltip="First value (optional)")
        self.add_input_port("value_2", "any", False, tooltip="Second value (optional)")
        self.add_input_port("value_3", "any", False, tooltip="Third value (optional)")
        self.add_input_port("value_4", "any", False, tooltip="Fourth value (optional)")
        self.add_input_port("value_5", "any", False, tooltip="Fifth value (optional)")
        self.add_output_port("result", "array", tooltip="Created list from provided values")
        self.add_output_port("length", "number", tooltip="Length of the created list")
    
    async def process(self) -> Dict[str, Any]:
        result = []
        
        # Add values that are provided (not None and not empty string for optional ports)
        for i in range(1, 6):
            port_name = f"value_{i}"
            if port_name in self.input_values:
                value = self.input_values[port_name]
                if value is not None:
                    result.append(value)
        
        return {
            "result": result,
            "length": len(result)
        }


class ListLengthNode(WorkflowNode):
    """Node that returns the length of a list."""
    
    category = "list_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True, tooltip="Input list to get length of")
        self.add_output_port("length", "number", tooltip="Number of elements in the list")
        self.add_output_port("is_empty", "boolean", tooltip="Whether the list is empty")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        
        if not isinstance(input_list, list):
            raise ValueError("Input must be a list")
        
        length = len(input_list)
        
        return {
            "length": length,
            "is_empty": length == 0
        }
