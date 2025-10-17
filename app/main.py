from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime, timezone
import uuid
from typing import Dict, Any

from .core.logger import logger, pod_id
from .core.utils import verify_api_key, get_service_url
from .core.job_manager import job_manager
from .core.storage.file_manager import output_file_manager
from .schemas.api import (
    GenerateRequest, JobResponse, JobState, FileInfo,
    HealthResponse, CancelResponse, PurgeResponse
)
from .workflows.image_to_video import image_to_video_workflow

app = FastAPI()

# Workflow registry
WORKFLOWS = {
    "image-to-video": image_to_video_workflow
}

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    await job_manager.start_job_processors()

@app.post("/v1/generate", response_model=JobResponse)
async def generate(
    request: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start a new generation job"""
    job_id = str(uuid.uuid4())
    logger.info(f"New request: {request.model_dump_json()}", extra={"job_id": job_id})
    
    # Validate workflow
    if request.model not in WORKFLOWS:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {request.model}")
    
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
        pod_url=get_service_url()
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
    uvicorn.run(app, host="0.0.0.0", port=8000)