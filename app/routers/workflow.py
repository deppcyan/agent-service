from fastapi import APIRouter, HTTPException, Depends, Request, Body
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path

from app.utils.logger import logger
from app.utils.utils import verify_api_key
from app.core.workflow_manager import workflow_manager
from app.core.job_manager import job_manager
from app.schemas.api import WorkflowRequest, NodeInfo, NodePortInfo

# Define workflow storage path
WORKFLOW_DIR = Path("user/workflow")
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/v1/workflow", tags=["workflow"])

@router.post("/execute")
async def execute_workflow(
    request: WorkflowRequest,
    api_key: str = Depends(verify_api_key)
):
    """Execute a workflow directly with provided configuration"""
    try:
        task_id = await workflow_manager.execute_workflow(
            request.workflow,
            request.webhook_url
        )
        
        return {
            "task_id": task_id,
            "status": "accepted"
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook/{job_id}")
async def handle_workflow_webhook(
    job_id: str,
    request: Request
):
    """
    Webhook handler for workflow callbacks
    
    Args:
        job_id: ID of the job associated with this workflow
        request: webhook request containing workflow execution results
    """
    try:
        # Get request data
        data = await request.json()
        
        # Get task ID and status
        task_id = data.get("task_id")
        if not task_id:
            raise HTTPException(status_code=400, detail="Missing task_id in webhook data")
            
        status = data.get("status")
        result = data.get("result")
        error = data.get("error")
        
        # Update job state
        await job_manager._handle_workflow_callback(job_id, status, result, error)
                
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(
            f"Invalid workflow webhook data: {str(e)}",
            extra={"task_id": data.get("task_id", "unknown")}
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(
            f"Error processing workflow webhook: {str(e)}",
            extra={"task_id": data.get("task_id", "unknown")}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cancel/{task_id}")
async def cancel_workflow(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Cancel a running workflow"""
    cancelled = await workflow_manager.cancel_workflow(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Workflow task not found")
        
    return {
        "task_id": task_id,
        "status": "cancelled"
    }

@router.get("/status/{task_id}")
async def get_workflow_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get the status and result of a workflow task
    
    Args:
        task_id: The ID of the workflow task to check
        
    Returns:
        Dict containing:
        - status: "running" | "completed" | "error" | "cancelled" | "not_found"
        - result: Dictionary of node results
        - error: Error message (only present if status is "error")
    """
    status = workflow_manager.get_task_status(task_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Workflow task not found")
    return status

@router.get("/nodes")
async def get_available_nodes():
    """Get all available node types and their structure"""
    from app.workflow.registry import node_registry
    import inspect
    
    result = {
        "nodes": [],
        "categories": {}
    }
    
    for node_name, node_class in node_registry._nodes.items():
        # 检查节点类的模块路径
        module_path = inspect.getmodule(node_class).__name__
        # 只处理 app/workflow/nodes 和 custom_nodes 目录下的节点
        if not (module_path.startswith('nodes.') or module_path.startswith('custom_nodes.') or
        module_path.startswith("app.workflow.nodes") or module_path.startswith("app.workflow.custom_nodes")):
            logger.debug(f"Skipping node {node_name} from module {module_path}")
            continue
            
        try:
            # Try to get port information from class attributes first
            input_ports = {}
            output_ports = {}
            
            # Try to create a temporary instance with a dummy node_id
            try:
                node = node_class("temp_node")
                input_ports = {
                    name: NodePortInfo(
                        name=port.name,
                        port_type=port.port_type,
                        required=port.required,
                        default_value=port.default_value
                    )
                    for name, port in node.input_ports.items()
                }
                
                output_ports = {
                    name: NodePortInfo(
                        name=port.name,
                        port_type=port.port_type,
                        required=True,
                        default_value=None
                    )
                    for name, port in node.output_ports.items()
                }
            except (TypeError, ValueError) as e:
                # If instance creation fails, try to get ports from class attributes
                logger.debug(f"Failed to create instance of {node_name}: {str(e)}")
                
                # Get ports from class attributes if they exist
                if hasattr(node_class, 'INPUT_PORTS'):
                    input_ports = {
                        name: NodePortInfo(
                            name=name,
                            port_type=port.get('type', 'any'),
                            required=port.get('required', True),
                            default_value=port.get('default', None)
                        )
                        for name, port in node_class.INPUT_PORTS.items()
                    }
                
                if hasattr(node_class, 'OUTPUT_PORTS'):
                    output_ports = {
                        name: NodePortInfo(
                            name=name,
                            port_type=port.get('type', 'any'),
                            required=True,
                            default_value=None
                        )
                        for name, port in node_class.OUTPUT_PORTS.items()
                    }
            
            # Only add the node if we have port information
            if input_ports or output_ports:
                category = node_registry._categories.get(node_name, "default")
                node_info = {
                    "name": node_name,
                    "category": category,
                    "input_ports": {
                        name: {
                            "name": port.name,
                            "port_type": port.port_type,
                            "required": port.required,
                            "default_value": port.default_value
                        }
                        for name, port in input_ports.items()
                    },
                    "output_ports": {
                        name: {
                            "name": port.name,
                            "port_type": port.port_type,
                            "required": port.required,
                            "default_value": port.default_value
                        }
                        for name, port in output_ports.items()
                    }
                }
                
                result["nodes"].append(node_info)
                
                # 更新类别信息
                if category not in result["categories"]:
                    result["categories"][category] = []
                result["categories"][category].append(node_name)
            else:
                logger.debug(f"Skipping {node_name}: No port information available")
                
        except Exception as e:
            # Log any unexpected errors and continue
            logger.error(f"Error processing node {node_name}: {str(e)}")
            continue
    
    return result

@router.get("/list")
async def list_workflows(
    api_key: str = Depends(verify_api_key)
):
    """List all saved workflows"""
    try:
        workflows = []
        for file in WORKFLOW_DIR.glob("*.json"):
            workflows.append({
                "name": file.stem,
                "path": str(file.relative_to(WORKFLOW_DIR)),
                "last_modified": os.path.getmtime(file)
            })
        return {
            "workflows": sorted(workflows, key=lambda x: x["last_modified"], reverse=True)
        }
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_name}")
async def get_workflow(
    workflow_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific saved workflow by name"""
    try:
        workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")
            
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
            
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading workflow {workflow_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_workflow(
    workflow_name: str,
    workflow: Dict[str, Any] = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Save a workflow with the given name"""
    try:
        # Sanitize workflow name
        workflow_name = workflow_name.replace("/", "_").replace("\\", "_")
        workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
        
        # Save workflow
        with open(workflow_path, "w") as f:
            json.dump(workflow, f, indent=2)
            
        return {
            "status": "success",
            "message": f"Workflow saved as '{workflow_name}'"
        }
    except Exception as e:
        logger.error(f"Error saving workflow {workflow_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{workflow_name}")
async def delete_workflow(
    workflow_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a specific workflow by name"""
    try:
        # Sanitize workflow name
        workflow_name = workflow_name.replace("/", "_").replace("\\", "_")
        workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
        
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")
            
        # Delete the workflow file
        workflow_path.unlink()
        
        return {
            "status": "success",
            "message": f"Workflow '{workflow_name}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
