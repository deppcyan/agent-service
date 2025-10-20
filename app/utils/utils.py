import os
import socket
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from PIL import Image
import numpy as np
from fastapi import HTTPException, Header
from .logger import logger, pod_id, gpu_vendor, novita_region

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
    
    # Priority use DIGEN_PROXY_URL
    if os.getenv('DIGEN_PROXY_URL'):
        GLOBAL_SERVICE_URL = os.getenv('DIGEN_PROXY_URL').rstrip('/')
        return GLOBAL_SERVICE_URL
    
    # Get port configuration
    port = os.getenv('DIGEN_SERVICE_PORT', '8000')
    
    # Generate URL based on gpu_vendor
    if gpu_vendor == 'runpod':
        GLOBAL_SERVICE_URL = f"https://{pod_id}-{port}.proxy.runpod.net"
    elif gpu_vendor == 'novita':
        GLOBAL_SERVICE_URL = f"https://{pod_id}-{port}.{novita_region}.gpu-instance.novita.ai"
    else:
        # Local address
        local_ip = os.getenv('LOCAL_IP') or get_local_ip()
        GLOBAL_SERVICE_URL = f"http://{local_ip}:{port}"
    
    return GLOBAL_SERVICE_URL

def get_service_url() -> str:
    """
    Get service URL (uses cached value)
    
    Returns:
        str: Complete service URL
    """
    if GLOBAL_SERVICE_URL is None:
        return init_service_url()
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

def calculate_aspect_ratio(
    height: int,
    width: int,
    target_width: int,
    target_height: int,
    vae_stride=(4, 8, 8),
    patch_size=(1, 2, 2)
) -> tuple[int, int, int, int]:
    """
    Calculate adjusted height and width using Wan 2.1 model algorithm
    
    Args:
        height: Original image height
        width: Original image width
        target_width: Target width
        target_height: Target height
        vae_stride: VAE model stride, default (4, 8, 8)
        patch_size: Model patch size, default (1, 2, 2)
    
    Returns:
        tuple: (adjusted height, adjusted width, latent height, latent width)
    """
    # Calculate target area
    max_area = target_width * target_height
    
    # Calculate aspect ratio
    aspect_ratio = height / width
    
    # Calculate latent space dimensions
    lat_h = round(
        np.sqrt(max_area * aspect_ratio) // vae_stride[1] //
        patch_size[1] * patch_size[1])
    lat_w = round(
        np.sqrt(max_area / aspect_ratio) // vae_stride[2] //
        patch_size[2] * patch_size[2])
    
    # Convert latent dimensions back to pixel space
    h = lat_h * vae_stride[1]
    w = lat_w * vae_stride[2]
    
    return h, w, lat_h, lat_w

async def process_image(image_path: str, job_id: str, options: Optional[Dict] = None) -> tuple[int, int, int, int, int, int]:
    """
    Process image and calculate dimensions
    
    Args:
        image_path: Path to image file
        job_id: Job ID for logging
        options: Optional processing options
        
    Returns:
        tuple: (original width, original height, adjusted height, adjusted width, latent height, latent width)
    """
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Get resolution from options or use default
        resolution = options.get('resolution') if options else None
        target_width, target_height = parse_resolution(resolution)
        
        h, w, lat_h, lat_w = calculate_aspect_ratio(height, width, target_width, target_height)
        
        logger.info(
            f"Image dimensions: source={width}x{height}, target={target_width}x{target_height}, "
            f"output={w}x{h}, latent={lat_w}x{lat_h}",
            extra={"job_id": job_id}
        )
        
        return width, height, h, w, lat_h, lat_w

def calculate_wait_time(job_states: Dict[str, Any], avg_processing_time: float = 60.0) -> float:
    """
    Calculate estimated wait time
    
    Args:
        job_states: Current job states dictionary
        avg_processing_time: Average processing time per second of video
    
    Returns:
        float: Estimated wait time in seconds
    """
    # Calculate queue processing time
    queue_processing_time = 0
    for job_id, state in job_states.items():
        if state['status'] in ['pending', 'processing']:
            # Get duration with default of 5 seconds
            options = state.get('options', {})
            job_duration = options.get('duration', 5) or 5
            queue_processing_time += job_duration * avg_processing_time
    
    return queue_processing_time

async def send_webhook(url: str, payload: dict) -> bool:
    """
    Send webhook notification
    
    Args:
        url: Webhook URL
        payload: Data to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                return response.status == 200
        except:
            return False

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