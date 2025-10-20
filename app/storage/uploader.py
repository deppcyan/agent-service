import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
from app.utils.logger import logger
from .s3_manager import s3_manager

class FileUploader:
    """Handles file uploads to various S3 providers"""
    
    def __init__(self):
        self.default_provider = "aws"  # Default to AWS S3
    
    def set_default_provider(self, provider: str):
        """Set default storage provider"""
        if provider not in ["aws", "wasabi"]:
            raise ValueError(f"Unsupported storage provider: {provider}")
        self.default_provider = provider
    
    @staticmethod
    def parse_custom_url(url: str) -> tuple[str, str, str]:
        """Parse custom S3 URL into provider, bucket, and key"""
        parsed_url = urlparse(url)
        
        # Determine provider and bucket
        if '.wasabisys.com' in parsed_url.netloc:
            provider = 'wasabi'
            bucket = parsed_url.netloc.split('.')[0]
        elif '.amazonaws.com' in parsed_url.netloc:
            provider = 'aws'
            bucket = parsed_url.netloc.split('.')[0]
        else:
            raise ValueError(f"Unsupported S3 URL format: {url}")
            
        key = parsed_url.path.lstrip('/')
        return provider, bucket, key
    
    def _generate_key(self, local_path: str, job_id: str) -> str:
        """Generate S3 key for file"""
        # Get current date in YYYYMMDD format
        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
        # Get original file extension
        original_ext = os.path.splitext(local_path)[1]
        # Use job_id as filename
        file_name = f"{job_id}{original_ext}"
        return f"{current_date}/{file_name}"
    
    async def upload(
        self,
        local_path: str,
        job_id: str,
        provider: Optional[str] = None,
        custom_url: Optional[str] = None,
        content_type: Optional[str] = None,
        acl: Optional[str] = None
    ) -> str:
        """
        Upload file to S3
        
        Args:
            local_path: Local file path
            job_id: Job ID for logging and naming
            provider: Storage provider (aws/wasabi), defaults to self.default_provider
            custom_url: Optional custom S3 URL to upload to
            content_type: Optional content type
            acl: Optional ACL (e.g., 'public-read')
            
        Returns:
            str: URL of uploaded file
        """
        try:
            if custom_url:
                # Parse custom URL
                target_provider, bucket, key = self.parse_custom_url(custom_url)
                logger.info(f"Using custom upload URL: {custom_url}", extra={"job_id": job_id})
            else:
                # Use default provider and generate key
                target_provider = provider or self.default_provider
                s3_provider = s3_manager.get_provider(target_provider)
                key = self._generate_key(local_path, job_id)
                
                # Get bucket from provider config
                if target_provider == "aws":
                    bucket = s3_manager.get_provider("aws").bucket
                else:
                    bucket = s3_manager.get_provider("wasabi").bucket
            
            # Prepare upload options
            upload_options = {}
            if content_type:
                upload_options['ContentType'] = content_type
            if acl:
                upload_options['ACL'] = acl
            
            # Get provider and upload
            s3_provider = s3_manager.get_provider(target_provider)
            url = await s3_provider.upload_file(local_path, key, upload_options)
            
            logger.info(f"Successfully uploaded to {url}", extra={"job_id": job_id})
            return url
            
        except Exception as e:
            error_msg = f"Failed to upload file: {str(e)}"
            logger.error(error_msg, extra={"job_id": job_id})
            raise Exception(error_msg)
    
    async def upload_to_aws(self, local_path: str, job_id: str, **kwargs) -> str:
        """Convenience method to upload to AWS S3"""
        return await self.upload(local_path, job_id, provider="aws", **kwargs)
    
    async def upload_to_wasabi(self, local_path: str, job_id: str, **kwargs) -> str:
        """Convenience method to upload to Wasabi"""
        return await self.upload(local_path, job_id, provider="wasabi", **kwargs)

# Create global uploader instance
uploader = FileUploader()
