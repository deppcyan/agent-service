import os
import re
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any, Tuple
import aioboto3
from app.utils.logger import logger

class S3Provider(ABC):
    """Abstract base class for S3 storage providers"""
    
    @abstractmethod
    async def upload_file(self, file_path: str, key: str, bucket: str, region: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Upload a file to S3 and return its URL"""
        pass
    
    @abstractmethod
    async def download_file(self, key: str, destination_path: str, bucket: str, region: str) -> None:
        """Download a file from S3"""
        pass
    
    @abstractmethod
    async def get_presigned_url(self, key: str, bucket: str, region: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for a file"""
        pass
    
    @abstractmethod
    def parse_s3_url(self, url: str) -> Tuple[str, str, str]:
        """Parse S3 URL to extract bucket, region, and key"""
        pass

class AWSS3Provider(S3Provider):
    """AWS S3 storage provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.access_key_id = config["access_key_id"]
        self.secret_access_key = config["secret_access_key"]
        self.default_region = config.get("region", "us-west-1")
        # Cache sessions by region to avoid creating new ones for each request
        self._session_cache: Dict[str, aioboto3.Session] = {}
    
    def _get_session(self, region: str) -> aioboto3.Session:
        """Get cached aioboto3 session for specific region"""
        if region not in self._session_cache:
            self._session_cache[region] = aioboto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
            logger.debug(f"Created new AWS session for region: {region}")
        return self._session_cache[region]
    
    def clear_session_cache(self) -> None:
        """Clear cached sessions (useful for cleanup or credential refresh)"""
        self._session_cache.clear()
        logger.debug("Cleared AWS session cache")
    
    def get_cached_regions(self) -> list[str]:
        """Get list of regions with cached sessions"""
        return list(self._session_cache.keys())
    
    def parse_s3_url(self, url: str) -> Tuple[str, str, str]:
        """Parse AWS S3 URL to extract bucket, region, and key"""
        # Support multiple AWS S3 URL formats:
        # https://bucket.s3.region.amazonaws.com/key
        
        patterns = [
            # Virtual hosted-style: https://bucket.s3.region.amazonaws.com/key
            r'https://([^.]+)\.s3\.([^.]+)\.amazonaws\.com/(.+)'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.match(pattern, url)
            if match:
                if i == 0:  # Virtual hosted-style with region
                    bucket, region, key = match.groups()
                elif i == 1:  # Virtual hosted-style legacy
                    bucket, key = match.groups()
                    region = "us-east-1"  # Default region for legacy URLs
                elif i == 2:  # Path-style with region
                    region, bucket, key = match.groups()
                elif i == 3:  # Path-style legacy
                    bucket, key = match.groups()
                    region = "us-east-1"  # Default region for legacy URLs
                
                return bucket, region, key
        
        raise ValueError(f"Invalid AWS S3 URL format: {url}")
    
    async def upload_file(self, file_path: str, key: str, bucket: str, region: str, options: Optional[Dict[str, Any]] = None) -> str:
        session = self._get_session(region)
        async with session.client('s3') as s3:
            try:
                extra_args = options or {}
                await s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
                return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            except Exception as e:
                logger.error(f"Error uploading file to AWS S3: {str(e)}")
                raise
    
    async def download_file(self, key: str, destination_path: str, bucket: str, region: str) -> None:
        session = self._get_session(region)
        async with session.client('s3') as s3:
            try:
                await s3.download_file(bucket, key, destination_path)
            except Exception as e:
                logger.error(f"Error downloading file from AWS S3: {str(e)}")
                raise
    
    async def get_presigned_url(self, key: str, bucket: str, region: str, expires_in: int = 3600) -> str:
        session = self._get_session(region)
        async with session.client('s3') as s3:
            try:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.error(f"Error generating presigned URL: {str(e)}")
                raise

class WasabiProvider(S3Provider):
    """Wasabi storage provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.access_key_id = config["access_key_id"]
        self.secret_access_key = config["secret_access_key"]
        self.default_region = config.get("region", "us-west-1")
        # Cache sessions by region to avoid creating new ones for each request
        self._session_cache: Dict[str, aioboto3.Session] = {}
    
    def _get_session(self, region: str) -> aioboto3.Session:
        """Get cached aioboto3 session for specific region"""
        if region not in self._session_cache:
            self._session_cache[region] = aioboto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
            logger.debug(f"Created new Wasabi session for region: {region}")
        return self._session_cache[region]
    
    def clear_session_cache(self) -> None:
        """Clear cached sessions (useful for cleanup or credential refresh)"""
        self._session_cache.clear()
        logger.debug("Cleared Wasabi session cache")
    
    def get_cached_regions(self) -> list[str]:
        """Get list of regions with cached sessions"""
        return list(self._session_cache.keys())
    
    def _get_endpoint_url(self, region: str) -> str:
        """Get Wasabi endpoint URL for specific region"""
        return f"https://s3.{region}.wasabisys.com"
    
    def parse_s3_url(self, url: str) -> Tuple[str, str, str]:
        """Parse Wasabi S3 URL to extract bucket, region, and key"""
        # Support Wasabi URL formats:
        # https://s3.region.wasabisys.com/bucket/key
        
        patterns = [
            # Path-style: https://s3.region.wasabisys.com/bucket/key
            r'https://s3\.([^.]+)\.wasabisys\.com/([^/]+)/(.+)'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.match(pattern, url)
            if match:
                if i == 0:  # Virtual hosted-style
                    bucket, region, key = match.groups()
                elif i == 1:  # Path-style
                    region, bucket, key = match.groups()
                
                return bucket, region, key
        
        raise ValueError(f"Invalid Wasabi S3 URL format: {url}")
    
    async def upload_file(self, file_path: str, key: str, bucket: str, region: str, options: Optional[Dict[str, Any]] = None) -> str:
        session = self._get_session(region)
        endpoint_url = self._get_endpoint_url(region)
        async with session.client('s3', endpoint_url=endpoint_url) as s3:
            try:
                extra_args = options or {}
                await s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
                return f"https://s3.{region}.wasabisys.com/{bucket}/{key}"
            except Exception as e:
                logger.error(f"Error uploading file to Wasabi: {str(e)}")
                raise
    
    async def download_file(self, key: str, destination_path: str, bucket: str, region: str) -> None:
        session = self._get_session(region)
        endpoint_url = self._get_endpoint_url(region)
        async with session.client('s3', endpoint_url=endpoint_url) as s3:
            try:
                await s3.download_file(bucket, key, destination_path)
            except Exception as e:
                logger.error(f"Error downloading file from Wasabi: {str(e)}")
                raise
    
    async def get_presigned_url(self, key: str, bucket: str, region: str, expires_in: int = 3600) -> str:
        session = self._get_session(region)
        endpoint_url = self._get_endpoint_url(region)
        async with session.client('s3', endpoint_url=endpoint_url) as s3:
            try:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
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
            available_providers = list(self.providers.keys())
            if not available_providers:
                raise ValueError(f"Storage provider '{name}' not registered. No S3 providers are configured. Please check your environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY).")
            else:
                raise ValueError(f"Storage provider '{name}' not registered. Available providers: {available_providers}")
        return self.providers[name]
    
    def detect_provider_from_url(self, url: str) -> str:
        """Detect storage provider from URL"""
        if "amazonaws.com" in url:
            return "aws"
        elif "wasabisys.com" in url:
            return "wasabi"
        else:
            raise ValueError(f"Cannot detect storage provider from URL: {url}")
    
    async def upload_file_from_url(self, file_path: str, s3_url: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Upload file using S3 URL to determine bucket and region"""
        provider_name = self.detect_provider_from_url(s3_url)
        provider = self.get_provider(provider_name)
        bucket, region, key = provider.parse_s3_url(s3_url)
        return await provider.upload_file(file_path, key, bucket, region, options)
    
    async def download_file_from_url(self, s3_url: str, destination_path: str) -> None:
        """Download file using S3 URL to determine bucket and region"""
        provider_name = self.detect_provider_from_url(s3_url)
        provider = self.get_provider(provider_name)
        bucket, region, key = provider.parse_s3_url(s3_url)
        await provider.download_file(key, destination_path, bucket, region)
    
    async def get_presigned_url_from_url(self, s3_url: str, expires_in: int = 3600) -> str:
        """Get presigned URL using S3 URL to determine bucket and region"""
        provider_name = self.detect_provider_from_url(s3_url)
        provider = self.get_provider(provider_name)
        bucket, region, key = provider.parse_s3_url(s3_url)
        return await provider.get_presigned_url(key, bucket, region, expires_in)
    
    def clear_all_session_caches(self) -> None:
        """Clear session caches for all registered providers"""
        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'clear_session_cache'):
                provider.clear_session_cache()
                logger.debug(f"Cleared session cache for provider: {provider_name}")
    
    def get_session_cache_stats(self) -> Dict[str, list[str]]:
        """Get session cache statistics for all providers"""
        stats = {}
        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'get_cached_regions'):
                stats[provider_name] = provider.get_cached_regions()
            else:
                stats[provider_name] = []
        return stats

def init_s3_providers() -> None:
    """Initialize S3 providers from environment variables"""
    # AWS S3 configuration
    aws_config = {
        "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region": os.getenv("AWS_REGION", "us-west-1")  # Default region, can be overridden by URL parsing
    }
    
    # Wasabi configuration
    wasabi_config = {
        "access_key_id": os.getenv("WASABI_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID")),
        "secret_access_key": os.getenv("WASABI_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY")),
        "region": os.getenv("WASABI_REGION", "us-west-1")  # Default region, can be overridden by URL parsing
    }
    
    # Register AWS provider if credentials are available
    if aws_config["access_key_id"] and aws_config["secret_access_key"]:
        try:
            s3_manager.register_provider("aws", aws_config)
            logger.info("AWS S3 provider registered successfully")
        except Exception as e:
            logger.error(f"Failed to register AWS S3 provider: {e}")
    else:
        logger.warning("AWS S3 credentials not found in environment variables")
    
    # Register Wasabi provider if credentials are available
    if wasabi_config["access_key_id"] and wasabi_config["secret_access_key"]:
        try:
            s3_manager.register_provider("wasabi", wasabi_config)
            logger.info("Wasabi provider registered successfully")
        except Exception as e:
            logger.error(f"Failed to register Wasabi provider: {e}")
    else:
        logger.info("Wasabi credentials not found, skipping Wasabi provider registration")

# Create global S3 manager instance
s3_manager = S3Manager()