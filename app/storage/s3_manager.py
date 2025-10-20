import os
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any
import aioboto3
from app.utils.logger import logger

class S3Provider(ABC):
    """Abstract base class for S3 storage providers"""
    
    @abstractmethod
    async def upload_file(self, file_path: str, key: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Upload a file to S3 and return its URL"""
        pass
    
    @abstractmethod
    async def download_file(self, key: str, destination_path: str) -> None:
        """Download a file from S3"""
        pass
    
    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for a file"""
        pass
    
    @property
    @abstractmethod
    def bucket(self) -> str:
        """Get the bucket name"""
        pass
    
    @property
    @abstractmethod
    def region(self) -> str:
        """Get the region name"""
        pass

class AWSS3Provider(S3Provider):
    """AWS S3 storage provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self._bucket = config["bucket"]
        self._region = config["region"]
        self.session = aioboto3.Session(
            aws_access_key_id=config["access_key_id"],
            aws_secret_access_key=config["secret_access_key"],
            region_name=config["region"]
        )
    
    @property
    def bucket(self) -> str:
        return self._bucket
    
    @property
    def region(self) -> str:
        return self._region
    
    async def upload_file(self, file_path: str, key: str, options: Optional[Dict[str, Any]] = None) -> str:
        async with self.session.client('s3') as s3:
            try:
                extra_args = options or {}
                await s3.upload_file(file_path, self.bucket, key, ExtraArgs=extra_args)
                return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            except Exception as e:
                logger.error(f"Error uploading file to AWS S3: {str(e)}")
                raise
    
    async def download_file(self, key: str, destination_path: str) -> None:
        async with self.session.client('s3') as s3:
            try:
                await s3.download_file(self.bucket, key, destination_path)
            except Exception as e:
                logger.error(f"Error downloading file from AWS S3: {str(e)}")
                raise
    
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        async with self.session.client('s3') as s3:
            try:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.error(f"Error generating presigned URL: {str(e)}")
                raise

class WasabiProvider(S3Provider):
    """Wasabi storage provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self._bucket = config["bucket"]
        self._region = config["region"]
        self.session = aioboto3.Session(
            aws_access_key_id=config["access_key_id"],
            aws_secret_access_key=config["secret_access_key"],
            region_name=config["region"]
        )
        # Wasabi endpoint URL format
        self.endpoint_url = f"https://s3.{self.region}.wasabisys.com"
    
    @property
    def bucket(self) -> str:
        return self._bucket
    
    @property
    def region(self) -> str:
        return self._region
    
    async def upload_file(self, file_path: str, key: str, options: Optional[Dict[str, Any]] = None) -> str:
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
            try:
                extra_args = options or {}
                await s3.upload_file(file_path, self.bucket, key, ExtraArgs=extra_args)
                return f"https://{self.bucket}.s3.{self.region}.wasabisys.com/{key}"
            except Exception as e:
                logger.error(f"Error uploading file to Wasabi: {str(e)}")
                raise
    
    async def download_file(self, key: str, destination_path: str) -> None:
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
            try:
                await s3.download_file(self.bucket, key, destination_path)
            except Exception as e:
                logger.error(f"Error downloading file from Wasabi: {str(e)}")
                raise
    
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
            try:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.error(f"Error generating presigned URL: {str(e)}")
                raise

class S3Manager:
    """Factory class for managing S3 storage providers"""
    
    def __init__(self):
        self.providers: Dict[str, S3Provider] = {}
    
    def register_provider(self, name: str, config: Dict[str, Any]) -> None:
        """Register a new storage provider"""
        if name == "aws":
            self.providers[name] = AWSS3Provider(config)
        elif name == "wasabi":
            self.providers[name] = WasabiProvider(config)
        else:
            raise ValueError(f"Unsupported storage provider: {name}")
    
    def get_provider(self, name: str) -> S3Provider:
        """Get a registered storage provider"""
        if name not in self.providers:
            raise ValueError(f"Storage provider not registered: {name}")
        return self.providers[name]

# Create global S3 manager instance
s3_manager = S3Manager()