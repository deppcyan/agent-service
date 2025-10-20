from typing import Dict, Type, Optional
from .base import WorkflowNode
import importlib
import inspect
import os
import sys
from pathlib import Path

class NodeRegistry:
    """Registry for workflow nodes"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NodeRegistry, cls).__new__(cls)
            cls._instance._nodes: Dict[str, Type[WorkflowNode]] = {}
            cls._instance._categories: Dict[str, str] = {}
        return cls._instance
    
    def register_node(self, node_class: Type[WorkflowNode], category: str = "default"):
        """Register a node class"""
        node_name = node_class.__name__
        self._nodes[node_name] = node_class
        self._categories[node_name] = category
    
    def get_node_class(self, node_name: str) -> Optional[Type[WorkflowNode]]:
        """Get a node class by name"""
        return self._nodes.get(node_name)
    
    def create_node(self, node_name: str, node_id: Optional[str] = None) -> WorkflowNode:
        """Create a new instance of a node"""
        node_class = self.get_node_class(node_name)
        if node_class is None:
            raise ValueError(f"Node type {node_name} not found")
        return node_class(node_id)
    
    def get_categories(self) -> Dict[str, list]:
        """Get all registered nodes grouped by category"""
        categories = {}
        for node_name, category in self._categories.items():
            if category not in categories:
                categories[category] = []
            categories[category].append(node_name)
        return categories
    
    def load_builtin_nodes(self):
        """Load all built-in nodes from the nodes directory"""
        nodes_dir = Path(__file__).parent / "nodes"
        if not nodes_dir.exists():
            return
            
        # Add nodes directory to Python path
        sys.path.append(str(nodes_dir.parent))
        
        # Load all Python files in the nodes directory
        for file in nodes_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            try:
                # Import the module
                module_name = f"nodes.{file.stem}"
                module = importlib.import_module(module_name)
                
                # Find and register all WorkflowNode classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, WorkflowNode) and 
                        obj != WorkflowNode):
                        category = getattr(obj, "category", "default")
                        self.register_node(obj, category)
                        
            except Exception as e:
                print(f"Error loading node module {file}: {e}")
    
    def load_custom_nodes(self, custom_nodes_dir: str):
        """Load custom nodes from the specified directory"""
        nodes_dir = Path(custom_nodes_dir)
        if not nodes_dir.exists():
            return
            
        # Add custom nodes directory to Python path
        sys.path.append(str(nodes_dir.parent))
        
        # Load all Python files in the custom nodes directory
        for file in nodes_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            try:
                # Import the module
                module_name = f"{nodes_dir.name}.{file.stem}"
                module = importlib.import_module(module_name)
                
                # Find and register all WorkflowNode classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, WorkflowNode) and 
                        obj != WorkflowNode):
                        category = getattr(obj, "category", "custom")
                        self.register_node(obj, category)
                        
            except Exception as e:
                print(f"Error loading custom node module {file}: {e}")

# Global instance
node_registry = NodeRegistry()
