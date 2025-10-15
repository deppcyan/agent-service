import os
import json
import asyncio
import aiohttp
import aioboto3
import numpy as np
from PIL import Image
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Header
from logger_config import logger, pod_id, gpu_vendor, novita_region
import socket

def get_local_ip() -> str:
    """
    获取本机IP地址
    
    Returns:
        str: 本机IP地址，如果无法获取则返回'0.0.0.0'
    """
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 连接一个外部地址（不需要真实连接）
            s.connect(('8.8.8.8', 80))
            # 获取本机IP
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Failed to get local IP: {str(e)}", extra={"job_id": "system"})
        return '0.0.0.0'

# 常量
LORA_DIR = "ComfyUI/models/loras"  # LoRA模型存储路径
COMFYUI_SERVER = "http://127.0.0.1:8188"

# 用于记录处理时间统计
processing_stats = {
    "total_processing_time": 0.0,  # 总处理时间（秒）
    "total_video_duration": 0.0,   # 总视频时长（秒）
    "samples_count": 0             # 样本数量
}

def parse_resolution(resolution: str) -> tuple[int, int]:
    """解析分辨率字符串，返回宽度和高度"""
    try:
        width, height = map(int, resolution.split('x'))
        return width, height
    except (ValueError, AttributeError):
        # 默认分辨率 480x832
        return 480, 832

def calculate_aspect_ratio(height: int, width: int, target_width: int, target_height: int, vae_stride=(4, 8, 8), patch_size=(1, 2, 2)):
    """
    计算调整后的高度和宽度，使用与Wan 2.1模型相同的算法
    
    参数:
        height (int): 原始图片的高度
        width (int): 原始图片的宽度
        target_width (int): 目标宽度
        target_height (int): 目标高度
        vae_stride (tuple): VAE模型的步长，默认为(4, 8, 8)
        patch_size (tuple): 模型的patch大小，默认为(1, 2, 2)
    
    返回:
        tuple: (调整后的高度, 调整后的宽度, 潜在高度, 潜在宽度)
    """
    # 计算目标面积
    max_area = target_width * target_height
    
    # 计算原始图片的宽高比
    aspect_ratio = height / width
    
    # 计算潜在空间的高度和宽度
    lat_h = round(
        np.sqrt(max_area * aspect_ratio) // vae_stride[1] //
        patch_size[1] * patch_size[1])
    lat_w = round(
        np.sqrt(max_area / aspect_ratio) // vae_stride[2] //
        patch_size[2] * patch_size[2])
    
    # 将潜在空间的尺寸转换回像素空间
    h = lat_h * vae_stride[1]
    w = lat_w * vae_stride[2]
    
    return h, w, lat_h, lat_w

async def process_image(image_path: str, job_id: str, options: Optional[Dict] = None):
    """Resize image if needed, maintaining aspect ratio"""
    with Image.open(image_path) as img:
        width, height = img.size
        
        # 从options中获取resolution，如果没有则使用默认值
        resolution = options.get('resolution') if options else None
        target_width, target_height = parse_resolution(resolution)
        
        h, w, lat_h, lat_w = calculate_aspect_ratio(height, width, target_width, target_height)
        
        logger.info(f"Image dimensions: source={width}x{height}, target={target_width}x{target_height}, output={w}x{h}, latent={lat_w}x{lat_h}",
                  extra={"job_id": job_id})
        
        return width, height, h, w, lat_h, lat_w

def calculate_wait_time(job_states: Dict[str, Any]) -> float:
    """
    计算预估等待时间
    
    Args:
        job_states: 当前任务状态字典
    
    Returns:
        float: 预估等待时间（秒）
    """
    if processing_stats["samples_count"] == 0:
        # 如果没有历史数据，使用保守估计：假设每秒视频需要60秒处理时间
        avg_processing_time_per_second = 60.0
    else:
        avg_processing_time_per_second = (
            processing_stats["total_processing_time"] / 
            processing_stats["total_video_duration"]
        )
    
    # 计算队列中所有任务的预估处理时间
    queue_processing_time = 0
    for job_id in list(job_states.keys()):
        if job_states[job_id]['status'] in ['pending', 'processing']:
            # Get duration with a default value of 5 seconds if options or duration doesn't exist
            options = job_states[job_id].get('options')
            job_duration = 5  # default duration
            if options is not None and 'duration' in options:
                job_duration = options['duration'] or 5  # use 5 if duration is None
            queue_processing_time += job_duration * avg_processing_time_per_second
    
    return queue_processing_time

async def download_file(url: str, local_path: str, job_id: str = "system") -> str:
    """
    异步文件下载方法，支持 S3 和 HTTP(S) URL
    
    Args:
        url: 文件的URL地址（支持 S3 和 HTTP(S)）
        local_path: 保存文件的本地路径
        job_id: 用于日志记录的任务ID
    
    Returns:
        str: 下载文件的本地路径
    
    Raises:
        Exception: 当下载失败时抛出异常
    """
    try:
        # 创建目标文件夹（如果不存在）
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        
        # 检查是否是 S3 URL
        parsed_url = urlparse(url)
        if '.s3.' in parsed_url.netloc or '.amazonaws.com' in parsed_url.netloc:
            # 异步 S3 下载
            bucket_name = parsed_url.netloc.split('.')[0]
            key = parsed_url.path.lstrip('/')
            
            logger.info(f"Downloading from S3: {url}", extra={"job_id": job_id})
            
            session = aioboto3.Session()
            async with session.client('s3') as s3_client:
                await s3_client.download_file(bucket_name, key, local_path)
        else:
            # HTTP(S) 下载
            logger.info(f"Downloading from HTTP(S): {url}", extra={"job_id": job_id})
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP download failed with status {response.status}")
                    
                    # 异步写入文件
                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                            f.write(chunk)
        
        logger.info(f"File downloaded successfully to {local_path}", extra={"job_id": job_id})
        return local_path
        
    except Exception as e:
        error_msg = f"Failed to download file: {str(e)}"
        logger.error(error_msg, extra={"job_id": job_id})
        # 如果下载失败，清理可能部分下载的文件
        if os.path.exists(local_path):
            os.remove(local_path)
        raise Exception(error_msg)

async def download_from_s3(url: str, local_path: str, job_id: str = "system"):
    """从 S3 下载文件到本地"""
    return await download_file(url, local_path, job_id)

async def upload_to_s3(local_path: str, bucket_name: str, job_id: str = "system", custom_url: str = None) -> str:
    """
    异步上传文件到 S3 并返回 URL
    
    Args:
        local_path: 要上传的本地文件路径
        bucket_name: 默认 S3 存储桶名称（当未提供 custom_url 时使用）
        job_id: 用于日志记录的任务ID
        custom_url: 可选的自定义 S3 URL。如果提供，文件将上传到此 URL 并设置公共读取权限。
                   如果上传失败，将回退到默认位置。
    
    Returns:
        str: 上传文件的 URL
    """
    session = aioboto3.Session()
    
    if custom_url:
        # 解析自定义 URL 以提取存储桶和键
        parsed_url = urlparse(custom_url)
        custom_bucket = parsed_url.netloc.split('.')[0]  # 从 URL 提取存储桶名称
        custom_key = parsed_url.path.lstrip('/')  # 移除路径前的斜杠
        
        logger.info(f"Using custom upload URL: {custom_url}", extra={"job_id": job_id})
        
        try:
            async with session.client('s3') as s3_client:
                await s3_client.upload_file(
                    local_path, 
                    custom_bucket, 
                    custom_key, 
                    ExtraArgs={
                        'ACL': 'public-read',
                        'ContentType': 'video/mp4'
                    }
                )
            logger.info(f"Successfully uploaded to custom URL: {custom_url}", extra={"job_id": job_id})
            return custom_url
        except Exception as e:
            logger.error(f"Failed to upload to custom S3 URL: {str(e)}", extra={"job_id": job_id})
            logger.info(f"Falling back to default upload location", extra={"job_id": job_id})
            # 如果自定义上传失败，回退到默认上传
    
    # 获取当前日期并格式化为 YYYYMMDD
    current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
    # 获取原始文件扩展名
    original_ext = os.path.splitext(local_path)[1]
    # 使用 job_id 作为文件名，保留原始扩展名
    file_name = f"{job_id}{original_ext}"
    key = f"{current_date}/{file_name}"
    
    try:
        async with session.client('s3') as s3_client:
            await s3_client.upload_file(local_path, bucket_name, key)
        return f"https://{bucket_name}.s3.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}", extra={"job_id": job_id})
        raise Exception(f"Failed to upload to S3: {str(e)}")

expected_api_key = os.getenv('DIGEN_API_KEY', "e7fca923-c9f0-4874-a8f6-b1b4a22ef28a")
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

async def send_webhook(url: str, payload: dict):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                return response.status == 200
        except:
            return False

def update_processing_stats(processing_time: float, video_duration: float):
    """更新处理时间统计"""
    processing_stats["total_processing_time"] += processing_time
    processing_stats["total_video_duration"] += video_duration
    processing_stats["samples_count"] += 1 

def get_service_url() -> str:
    """
    根据不同条件生成服务URL
    
    Returns:
        str: 服务的完整URL
        
    环境变量:
        DIGEN_PROXY_URL: 直接指定的代理URL（可选）
        DIGEN_SERVICE_PORT: 服务端口（可选，默认8000）
        LOCAL_IP: 本地IP地址（可选，默认0.0.0.0）
    """
    # 优先使用DIGEN_PROXY_URL
    if os.getenv('DIGEN_PROXY_URL'):
        return os.getenv('DIGEN_PROXY_URL').rstrip('/')
    
    # 获取端口配置
    port = os.getenv('DIGEN_SERVICE_PORT', '8000')
    
    # 根据gpu_vendor生成不同的URL
    if gpu_vendor == 'runpod':
        return f"https://{pod_id}-{port}.proxy.runpod.net"
    elif gpu_vendor == 'novita':
        return f"https://{pod_id}-{port}.{novita_region}.gpu-instance.novita.ai"
    else:
        # 本地地址
        local_ip = os.getenv('LOCAL_IP') or get_local_ip()
        return f"http://{local_ip}:{port}"

def get_local_file_url(pod_id: str, file_id: str) -> str:
    """
    生成本地文件访问URL
    
    Args:
        pod_id: RunPod的pod ID
        file_id: 文件ID
        
    Returns:
        str: 文件的完整访问URL
    """
    base_url = get_service_url()
    return f"{base_url}/files/{file_id}" 