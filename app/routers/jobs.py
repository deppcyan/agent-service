from fastapi import APIRouter, HTTPException, Depends, Request
from app.utils.utils import verify_api_key
from app.utils.logger import logger
from app.core.job_manager import job_manager
from app.core.callback_manager import callback_manager
from app.schemas.api import (
    GenerateRequest, JobResponse, CancelResponse, PurgeResponse
)

router = APIRouter(tags=["jobs"])

@router.post("/webhook")
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

@router.post("/v1/jobs/generate", response_model=JobResponse)
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
        webhook_url=request.webhook_url,
        options=request.options.model_dump()
    )

@router.post("/cancel/{job_id}", response_model=CancelResponse)
async def cancel_job(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Cancel a running job"""
    try:
        return await job_manager.cancel_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/purge-queue", response_model=PurgeResponse)
async def purge_queue(
    api_key: str = Depends(verify_api_key)
):
    """Purge all pending jobs from queue"""
    return await job_manager.purge_queue()
