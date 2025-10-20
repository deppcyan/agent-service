from typing import Dict, Any, List
from pathlib import Path
import yaml
from .base import WorkflowGraph
from .registry import node_registry

class WorkflowConfig:
    """Configuration for a workflow"""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.nodes = config_data.get("nodes", {})
        self.connections = config_data.get("connections", [])
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "WorkflowConfig":
        """Load workflow configuration from a YAML file"""
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return cls(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "WorkflowConfig":
        """Create workflow configuration from a dictionary"""
        return cls(config_dict)
    
    def to_graph(self) -> WorkflowGraph:
        """Convert configuration to a workflow graph"""
        graph = WorkflowGraph()
        
        # Create nodes
        for node_id, node_config in self.nodes.items():
            node_type = node_config["type"]
            node = node_registry.create_node(node_type, node_id)
            
            # Set input values
            if "inputs" in node_config:
                for port_name, value in node_config["inputs"].items():
                    node.input_values[port_name] = value
            
            graph.add_node(node)
        
        # Create connections
        for connection in self.connections:
            graph.connect(
                connection["from_node"],
                connection["from_port"],
                connection["to_node"],
                connection["to_port"]
            )
        
        return graph
    
    def to_yaml(self, yaml_path: str):
        """Save workflow configuration to a YAML file"""
        config_data = {
            "nodes": self.nodes,
            "connections": self.connections
        }
        with open(yaml_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
