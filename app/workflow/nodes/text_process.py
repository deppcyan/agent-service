from app.workflow.base import WorkflowNode
from typing import Dict, Any, List
import os

class TextToListNode(WorkflowNode):
    """Custom node that converts a single text string into a single-element list"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("text", "string", True)
        self.add_input_port("repeat_count", "number", False, "Number of times to repeat the text (default: 1)")
        self.add_output_port("list", "array")  # Output will be string array
    
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


class ListToTextNode(WorkflowNode):
    """Custom node that converts a list into a single text string by taking the first element"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        self.add_input_port("list", "array", True)  # Input will be string array
        self.add_output_port("text", "string")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        input_list = self.input_values["list"]
        
        if not input_list:
            raise ValueError("Input list is empty")
            
        # Take first element from list and convert to text
        return {
            "text": input_list[0]
        }


class TextCombinerNode(WorkflowNode):
    """Node for combining text using a template prompt with variables"""
    
    category = "text_process"
    
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


class LoadTextFromFileNode(WorkflowNode):
    """Node for loading text content from a file using relative path"""
    
    category = "text_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("file_path", "string", True, "Relative path to the text file")
        
        # Output ports
        self.add_output_port("text", "string")
    
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
        self.add_input_port("text", "string", True, "Text to strip")
        self.add_output_port("text", "string")
    
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
        self.add_input_port("text", "string", True, "Text to clean up")
        self.add_output_port("text", "string")
    
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
        self.add_input_port("text", "string", True, "Text to split")
        self.add_input_port("delimiter", "string", False, "Delimiter to split by (default: \\n)")
        self.add_input_port("max_splits", "number", False, "Maximum number of splits (default: unlimited)")
        self.add_output_port("segments", "array")
        self.add_output_port("count", "number")
    
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
            segments = text.split(delimiter, max_splits)
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