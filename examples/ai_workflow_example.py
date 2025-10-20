import asyncio
import os
from app.workflow.registry import node_registry
from app.workflow.config import WorkflowConfig
from app.workflow.executor import WorkflowExecutor

# Example workflow configuration that combines multiple AI services
WORKFLOW_CONFIG = {
    "nodes": {
        "vl_node": {
            "type": "QwenVLNode",
            "inputs": {
                "api_url": "http://api.example.com/qwen-vl",
                "image_url": "https://example.com/image.jpg",
                "prompt": "Describe this image",
                "system_prompt": "You are a helpful assistant"
            }
        },
        "i2v_node": {
            "type": "WanI2VNode",
            "inputs": {
                "api_url": "http://api.example.com/wan-i2v",
                "image_url": "https://example.com/image.jpg",
                "prompt": "Convert this image to a dynamic video",
                "duration": 10,
                "output_format": "mp4"
            }
        },
        "video_concat": {
            "type": "VideoConcatNode",
            "inputs": {
                "api_url": "http://api.example.com/video",
                "video_urls": [
                    "https://example.com/video1.mp4",
                    "https://example.com/video2.mp4"
                ],
                "options": {
                    "transition": "fade",
                    "duration": 2
                }
            }
        }
    },
    "connections": []  # These nodes operate independently in this example
}

async def main():
    # Set API key for testing
    os.environ["AI_SERVICE_API_KEY"] = "your-api-key"
    
    # Load nodes
    node_registry.load_builtin_nodes()
    
    # Create workflow
    workflow_config = WorkflowConfig.from_dict(WORKFLOW_CONFIG)
    graph = workflow_config.to_graph()
    
    # Execute workflow
    executor = WorkflowExecutor(graph)
    try:
        results = await executor.execute()
        print("Workflow Results:")
        for node_id, node_results in results.items():
            print(f"\n{node_id}:")
            for key, value in node_results.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error executing workflow: {e}")

if __name__ == "__main__":
    asyncio.run(main())