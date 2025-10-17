from typing import Dict, Any, List, Type, Optional
from pydantic import BaseModel
import yaml
from ..core.base import ServiceNode, Workflow
from ..services.nodes import QwenVLNode, WanI2VNode, QwenEditNode, VideoConcatNode

class NodeConfig(BaseModel):
    type: str
    api_url: str
    api_key: str
    options: Optional[Dict[str, Any]] = None

class WorkflowConfig(BaseModel):
    name: str
    description: str
    nodes: List[NodeConfig]
    steps: List[Dict[str, Any]]

class WorkflowRegistry:
    """Registry for workflow configurations and node types"""
    
    def __init__(self):
        self.node_types: Dict[str, Type[ServiceNode]] = {
            "qwen-vl": QwenVLNode,
            "wan-i2v": WanI2VNode,
            "qwen-edit": QwenEditNode,
            "concat-upscale": VideoConcatNode
        }
        self.workflows: Dict[str, WorkflowConfig] = {}
    
    def register_node_type(self, name: str, node_class: Type[ServiceNode]) -> None:
        """Register a new node type"""
        self.node_types[name] = node_class
    
    def load_workflow_config(self, config_path: str) -> None:
        """Load workflow configurations from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        for workflow_data in config_data['workflows']:
            workflow_config = WorkflowConfig(**workflow_data)
            self.workflows[workflow_config.name] = workflow_config
    
    def create_workflow(self, name: str, api_key: str) -> Optional[Workflow]:
        """Create a workflow instance from configuration"""
        config = self.workflows.get(name)
        if not config:
            return None
            
        # Create service nodes
        services = {}
        for node_config in config.nodes:
            node_class = self.node_types.get(node_config.type)
            if not node_class:
                raise ValueError(f"Unknown node type: {node_config.type}")
                
            node = node_class(
                api_url=node_config.api_url,
                api_key=api_key
            )
            services[node_config.type] = node
        
        # Create workflow instance
        workflow_class = self._get_workflow_class(name)
        if not workflow_class:
            raise ValueError(f"No workflow class found for: {name}")
            
        return workflow_class(services)
    
    def _get_workflow_class(self, name: str) -> Optional[Type[Workflow]]:
        """Get the workflow class for a given name"""
        # This could be extended to support dynamic workflow class loading
        from ..workflows.image_to_video import ImageToVideoWorkflow
        workflow_classes = {
            "image_to_video": ImageToVideoWorkflow
        }
        return workflow_classes.get(name)

# Create global workflow registry
workflow_registry = WorkflowRegistry()
