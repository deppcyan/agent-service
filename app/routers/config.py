from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional

from app.core.config_manager import config_manager
from app.utils.utils import verify_api_key

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/status")
async def get_config_status(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    return config_manager.get_status()

@router.post("/refresh")
async def refresh_configs(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    try:
        ok = await config_manager.sync_from_remote()
        if not ok:
            raise HTTPException(status_code=500, detail="Refresh failed or remote URL not set")
        return {"status": "ok", "version": config_manager.get_status().get("version")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

