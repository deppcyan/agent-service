import os
import socket
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from PIL import Image
import numpy as np
from fastapi import HTTPException, Header
from app.utils.logger import logger, pod_id, gpu_vendor, novita_region

# Global service URL
GLOBAL_SERVICE_URL: str = None

def init_service_url() -> str:
    """
    Initialize global service URL
    
    Returns:
        str: Service URL
    """
    global GLOBAL_SERVICE_URL
    
    if GLOBAL_SERVICE_URL is not None:
        return GLOBAL_SERVICE_URL
    
    # Priority use DIGEN_SERVICE_URL
    if os.getenv('DIGEN_SERVICE_URL'):
        GLOBAL_SERVICE_URL = os.getenv('DIGEN_SERVICE_URL').rstrip('/')
        logger.info(f"Using DIGEN_SERVICE_URL from environment: {GLOBAL_SERVICE_URL}", extra={"job_id": "system"})
        return GLOBAL_SERVICE_URL
    
    # Get port configuration
    port = os.getenv('DIGEN_SERVICE_PORT', '8000')
    
    # Local address
    local_ip = os.getenv('DIGEN_SERVICE_IP')
    if local_ip:
        logger.info(f"Using DIGEN_SERVICE_IP from environment: {local_ip}", extra={"job_id": "system"})
    else:
        local_ip = get_local_ip()
        logger.info(f"Using auto-detected local IP: {local_ip}", extra={"job_id": "system"})
    
    GLOBAL_SERVICE_URL = f"http://{local_ip}:{port}"
    logger.info(f"Service URL configured as: {GLOBAL_SERVICE_URL}", extra={"job_id": "system"})
    
    return GLOBAL_SERVICE_URL

def get_service_url() -> str:
    """
    Get service URL (uses cached value)
    
    Returns:
        str: Complete service URL
    """
    if GLOBAL_SERVICE_URL is None:
        url = init_service_url()
        return url
    return GLOBAL_SERVICE_URL

def get_local_ip() -> str:
    """
    Get local IP address
    
    Returns:
        str: Local IP address, returns '0.0.0.0' if unable to get
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Failed to get local IP: {str(e)}", extra={"job_id": "system"})
        return '0.0.0.0'

def parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse resolution string into width and height"""
    try:
        width, height = map(int, resolution.split('x'))
        return width, height
    except (ValueError, AttributeError):
        # Default resolution 480x832
        return 480, 832

def get_local_file_url(file_id: str) -> str:
    """
    Generate local file access URL
    
    Args:
        file_id: File ID
        
    Returns:
        str: Complete file access URL
    """
    return f"{get_service_url()}/files/{file_id}"

expected_api_key = os.getenv('DIGEN_API_KEY', "e7fca923-c9f0-4874-a8f6-b1b4a22ef28a")
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from request header"""
    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key