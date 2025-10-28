from fastapi import APIRouter
from app.core.job_manager import job_manager
from app.schemas.api import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Get service health status"""
    return job_manager.get_health_stats()

@router.get("/ready")
async def ready_check():
    """Check if service is ready to handle requests"""
    # For now, just return true if the service is running
    return {"ready": True}
