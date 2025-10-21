import os
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timezone
import uuid
from typing import Dict, Any

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
    WorkflowRequest
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

if __name__ == "__main__":
    import uvicorn
    # port改了，webhook端口也需要改
    uvicorn.run(app, host="0.0.0.0", port=8001)