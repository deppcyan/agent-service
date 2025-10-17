import os
import boto3
from typing import List, Optional
from .config import get_settings
from uuid import uuid4

class FileManager:
    def __init__(self):
        settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET
        self.local_storage = "storage"
        os.makedirs(self.local_storage, exist_ok=True)

    def generate_local_path(self, prefix: str = "", extension: str = "") -> str:
        """Generate a unique local file path"""
        filename = f"{uuid4()}{extension}"
        if prefix:
            filename = f"{prefix}_{filename}"
        return os.path.join(self.local_storage, filename)

    async def save_to_local(self, content: bytes, prefix: str = "", extension: str = "") -> str:
        """Save content to local storage and return the path"""
        local_path = self.generate_local_path(prefix, extension)
        with open(local_path, "wb") as f:
            f.write(content)
        return local_path

    async def upload_to_s3(self, local_path: str) -> str:
        """Upload file to S3 and return the URL"""
        filename = os.path.basename(local_path)
        self.s3_client.upload_file(local_path, self.bucket, filename)
        return f"https://{self.bucket}.s3.{get_settings().AWS_REGION}.amazonaws.com/{filename}"

    async def cleanup_local(self, paths: List[str]) -> None:
        """Clean up local files"""
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
