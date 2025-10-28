from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.storage.file_manager import output_file_manager
from app.schemas.api import FileInfo

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{file_id}")
async def get_file(file_id: str):
    """Get generated file"""
    file_path = output_file_manager.get_file_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found or expired")
    return FileResponse(file_path)

@router.get("/{file_id}/info", response_model=FileInfo)
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
