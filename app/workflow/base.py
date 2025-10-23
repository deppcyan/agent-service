from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class NodePort:
    """Represents an input or output port on a node"""
    name: str
    port_type: str
    required: bool = True
    default_value: Any = None

class WorkflowNode:
    """Base class for all workflow nodes"""
    
    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or str(uuid4())
        self.input_ports: Dict[str, NodePort] = {}
        self.output_ports: Dict[str, NodePort] = {}
        self.input_values: Dict[str, Any] = {}
        self.output_values: Dict[str, Any] = {}
    
    def add_input_port(self, name: str, port_type: str, required: bool = True, default_value: Any = None):
        """Add an input port to the node"""
        self.input_ports[name] = NodePort(name, port_type, required, default_value)
    
    def add_output_port(self, name: str, port_type: str):
        """Add an output port to the node"""
        self.output_ports[name] = NodePort(name, port_type, True)
    
    async def process(self) -> Dict[str, Any]:
        """Process the node's inputs and return outputs"""
        raise NotImplementedError("Nodes must implement process()")
    
    def validate_inputs(self) -> bool:
        """Validate that all required inputs are present"""
        from app.utils.logger import logger
        
        for port in self.input_ports.values():
            if port.required and port.name not in self.input_values:
                if port.default_value is None:
                    logger.error(f"Required input '{port.name}' is missing for node '{self.__class__.__name__}'")
                    return False
                self.input_values[port.name] = port.default_value
        return True

class NodeConnection:
    """Represents a connection between two node ports"""
    
    def __init__(self, 
                 from_node: str,
                 from_port: str, 
                 to_node: str,
                 to_port: str):
        self.from_node = from_node
        self.from_port = from_port
        self.to_node = to_node
        self.to_port = to_port

class WorkflowGraph:
    """Represents a workflow as a directed graph of nodes"""
    
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.connections: List[NodeConnection] = []
    
    def add_node(self, node: WorkflowNode) -> str:
        """Add a node to the graph"""
        self.nodes[node.node_id] = node
        return node.node_id
    
    def connect(self, 
                from_node: str,
                from_port: str, 
                to_node: str,
                to_port: str):
        """Connect two nodes together"""
        from app.utils.logger import logger
        
        # Validate nodes exist
        if from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' does not exist in the graph")
        if to_node not in self.nodes:
            raise ValueError(f"Target node '{to_node}' does not exist in the graph")
            
        # Validate ports exist
        source_node = self.nodes[from_node]
        target_node = self.nodes[to_node]
                
        if from_port not in source_node.output_ports:
            raise ValueError(f"Output port '{from_port}' not found on source node '{source_node.__class__.__name__}[{from_node}]'")
        if to_port not in target_node.input_ports:
            raise ValueError(f"Input port '{to_port}' not found on target node '{target_node.__class__.__name__}[{to_node}]'")
            
        # Validate port types match
        source_type = source_node.output_ports[from_port].port_type
        target_type = target_node.input_ports[to_port].port_type
        if source_type != target_type:
            raise ValueError(f"Port types must match: {source_node.__class__.__name__}[{from_node}].{from_port}({source_type}) -> {target_node.__class__.__name__}[{to_node}].{to_port}({target_type})")
            
        # Add connection
        connection = NodeConnection(from_node, from_port, to_node, to_port)
        self.connections.append(connection)
    
    def get_node_dependencies(self, node_id: str) -> Set[str]:
        """Get all nodes that must execute before the given node"""
        deps = set()
        for conn in self.connections:
            if conn.to_node == node_id:
                deps.add(conn.from_node)
                deps.update(self.get_node_dependencies(conn.from_node))
        return deps
    
    def get_execution_order(self) -> List[str]:
        """Get the order in which nodes should be executed"""
        executed = set()
        execution_order = []
        
        def visit_node(node_id: str):
            if node_id in executed:
                return
            deps = self.get_node_dependencies(node_id)
            for dep in deps:
                if dep not in executed:
                    visit_node(dep)
            executed.add(node_id)
            execution_order.append(node_id)
        
        for node_id in self.nodes:
            visit_node(node_id)
            
        return execution_order
