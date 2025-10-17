import os
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timezone
import uuid
from typing import Dict, Any

from app.core.logger import logger, pod_id
from app.core.utils import verify_api_key, init_service_url, get_service_url
from app.config.services import config
from app.core.job_manager import job_manager
from app.core.storage.file_manager import output_file_manager
from app.core.callback_manager import callback_manager
from app.core.concurrency import concurrency_manager
from app.schemas.api import (
    GenerateRequest, JobResponse, JobState, FileInfo,
    HealthResponse, CancelResponse, PurgeResponse
)

app = FastAPI()

# Service name mapping
SERVICE_NAMES = {
    "qwen-vl": "qwen_vl",
    "qwen-edit": "qwen_edit",
    "wan-i2v": "wan_i2v",
    "wan-talk": "wan_talk",
    "concat-upscale": "video_concat"
}

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
   
    # Initialize service URL
    init_service_url()
    
    # Configure rate limits and concurrency for services
    for service_name, service_config in config.services.items():
        concurrency_manager.configure_rate_limit(
            service_name,
            service_config.rate_limit["calls"],
            service_config.rate_limit["period"]
        )
        concurrency_manager.configure_concurrency(
            service_name,
            service_config.max_concurrent
        )
    
    # Get API key from environment
    api_key = os.getenv('DIGEN_API_KEY')
    if not api_key:
        raise ValueError("DIGEN_API_KEY environment variable not set")
    
    # Initialize workflows with service URLs and callback URLs
    # Initialize workflow registry
    from app.config.workflows import workflow_registry
    
@app.post("/webhook/{service_name}")
async def handle_webhook(
    service_name: str,
    request: Request
):
    """
    统一的 webhook 处理接口
    
    Args:
        service_name: 服务名称
        request: webhook 请求
    """
    # 验证服务名称
    if service_name not in SERVICE_NAMES:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
    
    try:
        # 获取请求数据
        data = await request.json()
        
        # 获取标准化的服务名称
        normalized_service = SERVICE_NAMES[service_name]
        
        # 获取 job ID
        job_id = data.get("id")
        if not job_id:
            raise HTTPException(status_code=400, detail="Missing job ID in webhook data")
        
        logger.info(
            f"Received webhook from {service_name} for job {job_id}",
            extra={"job_id": job_id}
        )
        
        # 处理回调
        await callback_manager.handle_callback(normalized_service, data)
        
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(
            f"Invalid webhook data from {service_name}: {str(e)}",
            extra={"job_id": data.get("id", "unknown")}
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(
            f"Error processing webhook from {service_name}: {str(e)}",
            extra={"job_id": data.get("id", "unknown")}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/v1/generate", response_model=JobResponse)
async def generate(
    request: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start a new generation job"""
    job_id = str(uuid.uuid4())
    logger.info(f"New request: {request.model_dump_json()}", extra={"job_id": job_id})
    
    # Create job state
    job_state = JobState(
        id=job_id,
        created_at=datetime.now(timezone.utc),
        status="pending",
        model=request.model,
        input=[item.model_dump() for item in request.input],
        webhook_url=request.webhookUrl,
        options=request.options.model_dump(),
        pod_id=pod_id,
        pod_url=get_service_url()  # 使用 getter 函数确保 URL 已初始化
    )
    
    # Add job to queue
    return await job_manager.add_job(job_state)

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

@app.get("/ready")
async def ready_check():
    """Check if service is ready to handle requests"""
    # For now, just return true if the service is running
    return {"ready": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)