from app.workflow.base import WorkflowNode
from typing import Dict, Any, List
import os
import json

class TextRepeatNode(WorkflowNode):
    """Node that converts text into a list with optional repetition"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to convert into a list")
        self.add_input_port("repeat_count", "number", False, default_value=1, tooltip="Number of times to repeat the text (default: 1)")
        self.add_output_port("list", "array", tooltip="Array containing the repeated text")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        repeat_count = int(self.input_values.get("repeat_count", 1))
        
        if repeat_count < 1:
            raise ValueError("repeat_count must be a positive integer")
            
        # Convert text into list with specified number of repetitions
        return {
            "list": [text] * repeat_count
        }


class TextCombinerNode(WorkflowNode):
    """Node for combining text using a template prompt with variables"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("prompt", "string", True, tooltip="Template with variables like {text_a}, {text_b}, {text_c}")
        self.add_input_port("text_a", "string", False, default_value="", tooltip="Text value for variable {text_a}")
        self.add_input_port("text_b", "string", False, default_value="", tooltip="Text value for variable {text_b}")
        self.add_input_port("text_c", "string", False, default_value="", tooltip="Text value for variable {text_c}")
        
        # Output ports
        self.add_output_port("combined_text", "string", tooltip="Text with variables replaced by their values")
        self.add_output_port("used_variables", "object", tooltip="Object showing which variables were used in the template")
    
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
            
            # Replace only specific variables, not all curly braces
            # This avoids conflicts with JSON or other curly brace usage in the prompt
            combined_text = prompt
            if used_vars["text_a"]:
                combined_text = combined_text.replace("{text_a}", str(text_a))
            if used_vars["text_b"]:
                combined_text = combined_text.replace("{text_b}", str(text_b))
            if used_vars["text_c"]:
                combined_text = combined_text.replace("{text_c}", str(text_c))
            
            return {
                "combined_text": combined_text,
                "used_variables": used_vars
            }
            
        except Exception as e:
            raise Exception(f"Error combining text: {str(e)}")


class LoadTextFromFileNode(WorkflowNode):
    """Node for loading text content from a file using relative path"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("file_path", "string", True, tooltip="Relative path to the text file")
        
        # Output ports
        self.add_output_port("text", "string", tooltip="Content of the loaded text file")
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            file_path = self.input_values.get("file_path", "")
            
            if not file_path:
                raise ValueError("file_path cannot be empty")
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            return {
                "text": text_content
            }
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File loading error: {str(e)}")
        except UnicodeDecodeError as e:
            raise ValueError(f"File encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading text from file: {str(e)}")

class TextStripNode(WorkflowNode):
    """Node that strips whitespace and newlines from both ends of text.
    Useful for cleaning up text input by removing leading and trailing spaces, tabs, and newlines."""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to strip")
        self.add_output_port("text", "string", tooltip="Text with leading and trailing whitespace removed")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        
        # Strip whitespace and newlines from both ends
        if isinstance(text, str):
            stripped_text = text.strip()
        else:
            # Convert to string first if not already a string, then strip
            stripped_text = str(text).strip()
            
        return {"text": stripped_text}


class TextRemoveEmptyLinesNode(WorkflowNode):
    """Node that removes empty lines and lines containing only whitespace from text.
    Useful for cleaning up text by removing blank lines while preserving content structure."""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to clean up")
        self.add_output_port("text", "string", tooltip="Text with empty lines removed")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        
        if not isinstance(text, str):
            text = str(text)
        
        # Split into lines, filter out empty/whitespace-only lines, then rejoin
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        cleaned_text = '\n'.join(non_empty_lines)
            
        return {"text": cleaned_text}


class TextSplitNode(WorkflowNode):
    """Node that splits text using a specified delimiter.
    Returns an array of text segments split by the delimiter."""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="Text to split")
        self.add_input_port("delimiter", "string", False, default_value="\n", tooltip="Delimiter to split by (default: \\n)")
        self.add_input_port("max_splits", "number", False, tooltip="Maximum number of segments to create (default: unlimited)")
        self.add_output_port("segments", "array", tooltip="Array of text segments after splitting")
        self.add_output_port("count", "number", tooltip="Number of segments created")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        delimiter = self.input_values.get("delimiter", "\n")
        max_splits = self.input_values.get("max_splits")
        
        if not isinstance(text, str):
            text = str(text)
        
        # Handle common escape sequences
        delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
        
        # Split the text
        if max_splits is not None:
            max_splits = int(max_splits)
            if max_splits < 0:
                raise ValueError("max_splits must be non-negative")
            # Note: split(delimiter, max_splits) performs at most max_splits splits,
            # which results in at most max_splits+1 segments
            # If user wants exactly max_splits segments, we need max_splits-1 as the split parameter
            if max_splits == 0:
                segments = [text]  # No splitting, return original text as single segment
            else:
                segments = text.split(delimiter, max_splits - 1)
        else:
            segments = text.split(delimiter)
            
        return {
            "segments": segments,
            "count": len(segments)
        }


class TextReplaceNode(WorkflowNode):
    """Node that replaces text with specified count and direction.
    Supports replacing from start, end, or all occurrences."""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True, tooltip="The original text where replacements will be made")
        self.add_input_port("old_text", "string", True, tooltip="The substring to search for and replace")
        self.add_input_port("new_text", "string", False, tooltip="The text to replace matches with. Leave empty to remove matches")
        self.add_input_port("count", "number", False, tooltip="Maximum number of replacements to make. Use -1 or leave empty for unlimited")
        self.add_input_port("direction", "string", False, options=["all", "start", "end"], tooltip="Direction to perform replacements: 'all' for everywhere, 'start' from beginning, 'end' from end")
        self.add_output_port("replaced_text", "string", tooltip="The text after performing all replacements")
        self.add_output_port("replacement_count", "number", tooltip="The actual number of replacements that were made")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        text = self.input_values["text"]
        old_text = self.input_values["old_text"]
        new_text = self.input_values.get("new_text", "")
        count = self.input_values.get("count", -1)
        direction = self.input_values.get("direction", "all").lower()
        
        if not isinstance(text, str):
            text = str(text)
        
        if not isinstance(old_text, str):
            old_text = str(old_text)
            
        if not isinstance(new_text, str):
            new_text = str(new_text)
        
        if count is not None:
            count = int(count)
        
        # Validate direction
        if direction not in ["start", "end", "all"]:
            raise ValueError("direction must be 'start', 'end', or 'all'")
        
        # If old_text is empty, return original text
        if not old_text:
            return {
                "replaced_text": text,
                "replacement_count": 0
            }
        
        replacement_count = 0
        
        if direction == "all" or count == -1:
            # Replace all occurrences
            if count == -1:
                replaced_text = text.replace(old_text, new_text)
                replacement_count = text.count(old_text)
            else:
                replaced_text = text.replace(old_text, new_text, count)
                replacement_count = min(text.count(old_text), count)
                
        elif direction == "start":
            # Replace from start
            replaced_text = text
            current_pos = 0
            
            for _ in range(count if count > 0 else float('inf')):
                pos = replaced_text.find(old_text, current_pos)
                if pos == -1:
                    break
                replaced_text = replaced_text[:pos] + new_text + replaced_text[pos + len(old_text):]
                current_pos = pos + len(new_text)
                replacement_count += 1
                
        elif direction == "end":
            # Replace from end
            replaced_text = text
            
            for _ in range(count if count > 0 else float('inf')):
                pos = replaced_text.rfind(old_text)
                if pos == -1:
                    break
                replaced_text = replaced_text[:pos] + new_text + replaced_text[pos + len(old_text):]
                replacement_count += 1
            
        return {
            "replaced_text": replaced_text,
            "replacement_count": replacement_count
        }

class TextToDictNode(WorkflowNode):
    """Node that converts text input to dictionary output.
    Supports JSON string parsing and key-value pair parsing with customizable separators."""
    
    category = "text_process"
    
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
    
    category = "text_process"
    
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

