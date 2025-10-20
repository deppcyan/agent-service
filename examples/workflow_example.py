import asyncio
from app.workflow.registry import node_registry
from app.workflow.config import WorkflowConfig
from app.workflow.executor import WorkflowExecutor

async def main():
    # Load built-in nodes
    node_registry.load_builtin_nodes()
    
    # Create a workflow configuration
    workflow_config = WorkflowConfig.from_dict({
        "nodes": {
            "concat1": {
                "type": "TextConcatenateNode",
                "inputs": {
                    "text1": "Hello",
                    "text2": "World",
                    "separator": " "
                }
            },
            "upper1": {
                "type": "TextUppercaseNode"
            }
        },
        "connections": [
            {
                "from_node": "concat1",
                "from_port": "result",
                "to_node": "upper1",
                "to_port": "text"
            }
        ]
    })
    
    # Convert configuration to graph
    graph = workflow_config.to_graph()
    
    # Execute the workflow
    executor = WorkflowExecutor(graph)
    results = await executor.execute()
    
    # Print results
    print("Workflow Results:")
    for node_id, node_results in results.items():
        print(f"{node_id}: {node_results}")

if __name__ == "__main__":
    asyncio.run(main())
