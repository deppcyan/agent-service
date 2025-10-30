import os
import aiohttp
from typing import Optional
from urllib.parse import urlparse
from app.utils.logger import logger
from .s3_manager import s3_manager

class FileDownloader:
    """Handles file downloads from various sources (HTTP, S3)"""
    
    @staticmethod
    def is_s3_url(url: str) -> bool:
        """Check if URL is an S3 URL"""
        parsed_url = urlparse(url)
        return '.s3.' in parsed_url.netloc or '.amazonaws.com' in parsed_url.netloc or '.wasabisys.com' in parsed_url.netloc
    
    
    @staticmethod
    async def download_from_http(url: str, local_path: str, job_id: str = "system") -> str:
        """Download file from HTTP(S) URL"""
        try:
            logger.info(f"Downloading from HTTP(S): {url}", extra={"job_id": job_id})
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP download failed with status {response.status}")
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                    
                    # Write file
                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            
            logger.info(f"File downloaded successfully to {local_path}", extra={"job_id": job_id})
            return local_path
            
        except Exception as e:
            error_msg = f"Failed to download file from HTTP: {str(e)}"
            logger.error(error_msg, extra={"job_id": job_id})
            if os.path.exists(local_path):
                os.remove(local_path)
            raise Exception(error_msg)
    
    @staticmethod
    async def download_from_s3(url: str, local_path: str, job_id: str = "system") -> str:
        """Download file from S3"""
        try:
            logger.info(f"Downloading from S3: {url}", extra={"job_id": job_id})
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            # Use the new S3Manager interface that parses URL automatically
            await s3_manager.download_file_from_url(url, local_path)
            
            logger.info(f"File downloaded successfully to {local_path}", extra={"job_id": job_id})
            return local_path
            
        except Exception as e:
            error_msg = f"Failed to download file from S3: {str(e)}"
            logger.error(error_msg, extra={"job_id": job_id})
            if os.path.exists(local_path):
                os.remove(local_path)
            raise Exception(error_msg)
    
    @staticmethod
    async def download(url: str, local_path: str, job_id: str = "system") -> str:
        """
        Download file from URL (automatically detects source type)
        
        Args:
            url: Source URL (HTTP or S3)
            local_path: Local path to save the file
            job_id: Job ID for logging
            
        Returns:
            str: Path to downloaded file
        """
        if FileDownloader.is_s3_url(url):
            return await FileDownloader.download_from_s3(url, local_path, job_id)
        else:
            return await FileDownloader.download_from_http(url, local_path, job_id)

# Create global downloader instance
downloader = FileDownloader()
