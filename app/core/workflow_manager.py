import json
from typing import Dict, Any, Optional
from pathlib import Path
from app.utils.logger import logger
from app.workflow.config import WorkflowConfig
from app.workflow.executor import WorkflowExecutor
from app.workflow.registry import node_registry

class WorkflowManager:
    """Manages workflow configurations and their lifecycle"""
    
    def __init__(self, workflows_dir: str = "app/config/workflows"):
        self.workflows_dir = workflows_dir
        self.workflows: Dict[str, WorkflowConfig] = {}
        # Load built-in nodes
        node_registry.load_builtin_nodes()
        # Load workflow configurations
        self.load_workflows()
    
    def load_workflows(self) -> None:
        """Load all workflow configurations from the workflows directory"""
        workflow_path = Path(self.workflows_dir)
        if not workflow_path.exists():
            logger.warning(f"Workflows directory not found: {self.workflows_dir}")
            return
            
        for file in workflow_path.glob("*.json"):
            try:
                # Load workflow configuration
                with open(file, 'r') as f:
                    config_data = json.load(f)
                workflow_config = WorkflowConfig.from_dict(config_data)
                
                # Get workflow name from file name
                name = file.stem
                self.workflows[name] = workflow_config
                logger.info(f"Loaded workflow configuration: {name}")
                
            except Exception as e:
                logger.error(f"Error loading workflow config from {file}: {str(e)}")
    
    def get_workflow(self, name: str) -> Optional[WorkflowConfig]:
        """Get workflow configuration by name"""
        return self.workflows.get(name)
    
    def list_workflows(self) -> Dict[str, WorkflowConfig]:
        """List all available workflows"""
        return self.workflows
    
    def reload_workflows(self) -> None:
        """Reload all workflow configurations"""
        self.workflows.clear()
        self.load_workflows()
        
    def create_workflow_executor(self, name: str, input_data: Dict[str, Any]) -> Optional[WorkflowExecutor]:
        """Create a workflow executor from configuration"""
        workflow_config = self.get_workflow(name)
        if not workflow_config:
            return None
            
        try:
            # Update input values in the configuration
            for node_id, node_config in workflow_config.nodes.items():
                if node_config.get("inputs") is None:
                    node_config["inputs"] = {}
                node_config["inputs"].update(input_data)
            
            # Convert configuration to graph and create executor
            graph = workflow_config.to_graph()
            executor = WorkflowExecutor(graph)
            return executor
            
        except Exception as e:
            logger.error(f"Error creating workflow executor for {name}: {str(e)}")
            return None

# Create global workflow manager instance
workflow_manager = WorkflowManager()
