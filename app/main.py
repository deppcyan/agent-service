import os
import sys
from pathlib import Path

# 自动将 PYTHONPATH 设置为 app 的上层目录
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List

from app.utils.logger import logger, pod_id
from app.utils.utils import verify_api_key, init_service_url, get_service_url
from app.core.job_manager import job_manager
from app.storage.file_manager import output_file_manager
from app.core.callback_manager import callback_manager
from app.core.workflow_manager import workflow_manager
from app.core.model_config import load_model_configs
from app.schemas.api import (
    GenerateRequest, JobResponse, JobState, FileInfo,
    HealthResponse, CancelResponse, PurgeResponse,
    WorkflowRequest, NodeInfo, NodePortInfo
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    
    # Initialize service URL
    init_service_url()
    
    # Load model configurations
    load_model_configs("config/model_config.json")
    
    # Load workflow nodes
    from app.workflow.registry import node_registry
    node_registry.load_builtin_nodes()
    node_registry.load_custom_nodes("app/workflow/custom_nodes")
        
    # Startup complete
    yield
    
    # Cleanup on shutdown (if needed)
    pass

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.0.238:5173"],  # 允许前端开发服务器的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有headers
)
    
@app.post("/webhook")
async def handle_webhook(
    request: Request
):
    """
    统一的 webhook 处理接口
    
    Args:
        request: webhook 请求
    """
    
    try:
        # 获取请求数据
        data = await request.json()
        
        # 获取 job ID
        job_id = data.get("id")
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job ID in webhook data")
        
        # 处理回调
        await callback_manager.handle_callback(data)
        
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(
            f"Invalid webhook data : {str(e)}",
            extra={"job_id": data.get("id", "unknown")}
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(
            f"Error processing webhook : {str(e)}",
            extra={"job_id": data.get("id", "unknown")}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/v1/workflow/webhook/{job_id}")
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

@app.post("/v1/generate", response_model=JobResponse)
async def generate(
    request: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start a new generation job"""
    logger.info(f"New request: {request.model_dump_json()}")
    
    # Add job to queue
    return await job_manager.add_job(
        model=request.model,
        input=[item.model_dump() for item in request.input],
        webhook_url=request.webhookUrl,
        options=request.options.model_dump()
    )

@app.get("/files/{file_id}")
async def get_file(file_id: str):
    """Get generated file"""
    file_path = output_file_manager.get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found or expired")
    return FileResponse(file_path)

@app.get("/files/{file_id}/info", response_model=FileInfo)
async def get_file_info(file_id: str):
    """Get file information"""
    file_info = output_file_manager.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or expired")
    
    return FileInfo(
        file_id=file_id,
        created_at=file_info['created_at'],
        job_id=file_info['job_id'],
        filename=file_info.get('filename', f"{file_id}.mp4"),
        expires_at=output_file_manager.get_expiration_time(file_id)
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get service health status"""
    return job_manager.get_health_stats()

@app.post("/cancel/{job_id}", response_model=CancelResponse)
async def cancel_job(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Cancel a running job"""
    try:
        return await job_manager.cancel_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/purge-queue", response_model=PurgeResponse)
async def purge_queue(
    api_key: str = Depends(verify_api_key)
):
    """Purge all pending jobs from queue"""
    return await job_manager.purge_queue()

@app.post("/v1/workflow/execute")
async def execute_workflow(
    request: WorkflowRequest,
    api_key: str = Depends(verify_api_key)
):
    """Execute a workflow directly with provided configuration"""
    try:
        task_id = await workflow_manager.execute_workflow(
            request.workflow,
            request.input_data,
            request.webhook_url
        )
        
        return {
            "task_id": task_id,
            "status": "accepted"
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/v1/workflow/cancel/{task_id}")
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

@app.get("/ready")
async def ready_check():
    """Check if service is ready to handle requests"""
    # For now, just return true if the service is running
    return {"ready": True}

@app.get("/v1/workflow/nodes")
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
        if not (module_path.startswith('nodes.') or module_path.startswith('custom_nodes.')):
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

if __name__ == "__main__":
    import uvicorn
    # port改了，webhook端口也需要改
    uvicorn.run(app, host="0.0.0.0", port=8001)