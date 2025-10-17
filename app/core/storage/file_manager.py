import os
import uuid
import shutil
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from logging import getLogger

logger = getLogger(__name__)

class OutputFileManager:
    """Manages output files with automatic cleanup"""
    
    def __init__(self, storage_dir: str = "storage/outputs", max_age_hours: int = 1):
        self.storage_dir = storage_dir
        self.max_age_hours = max_age_hours
        self.file_info: Dict[str, Dict] = {}
        self._ensure_storage_dir()
        self._cleanup_task = None
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def start_cleanup(self):
        """Start the cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def stop_cleanup(self):
        """Stop the cleanup task"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            self._cleanup_task = None
    
    def _is_file_expired(self, creation_time: datetime) -> bool:
        """Check if a file has expired"""
        now = datetime.now(timezone.utc)
        age = now - creation_time
        return age > timedelta(hours=self.max_age_hours)
    
    async def _cleanup_loop(self):
        """Periodic cleanup loop for expired files"""
        while True:
            try:
                expired_files = []
                
                # Check for expired files
                for file_id, info in list(self.file_info.items()):
                    if self._is_file_expired(info['created_at']):
                        file_path = os.path.join(self.storage_dir, info['filename'])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            expired_files.append(file_id)
                
                # Remove expired files from records
                for file_id in expired_files:
                    del self.file_info[file_id]
                
                if expired_files:
                    logger.info(f"Cleaned up {len(expired_files)} expired files")
                
                # Check every 5 minutes
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def store_file(self, source_path: str, job_id: str) -> str:
        """
        Store a file and return its ID
        
        Args:
            source_path: Source file path
            job_id: Job ID
        
        Returns:
            str: File ID for future access
        """
        try:
            file_id = str(uuid.uuid4())
            original_ext = os.path.splitext(source_path)[1]
            new_filename = f"{file_id}{original_ext}"
            new_path = os.path.join(self.storage_dir, new_filename)
            
            # Copy file to storage directory
            shutil.copy2(source_path, new_path)
            
            # Record file information
            self.file_info[file_id] = {
                'filename': new_filename,
                'created_at': datetime.now(timezone.utc),
                'job_id': job_id
            }
            
            logger.info(f"Stored file {new_filename} for job {job_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error storing file: {str(e)}")
            raise
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path if file exists and hasn't expired"""
        if file_id not in self.file_info:
            return None
            
        info = self.file_info[file_id]
        if self._is_file_expired(info['created_at']):
            return None
            
        file_path = os.path.join(self.storage_dir, info['filename'])
        if not os.path.exists(file_path):
            return None
            
        return file_path
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information"""
        return self.file_info.get(file_id)
    
    def get_expiration_time(self, file_id: str) -> Optional[datetime]:
        """Get file expiration time"""
        info = self.file_info.get(file_id)
        if info:
            return info['created_at'] + timedelta(hours=self.max_age_hours)
        return None

class InputFileManager:
    """Manages input file caching"""
    
    def __init__(self, storage_dir: str = "storage/inputs"):
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_cache_filename(self, url: str) -> str:
        """
        Generate cache filename from URL
        Uses the last part of the URL as filename, or MD5 hash if no filename
        """
        import hashlib
        
        filename = os.path.basename(url)
        if not filename or filename.endswith('/'):
            md5 = hashlib.md5(url.encode()).hexdigest()
            ext = os.path.splitext(url)[1]
            if not ext:
                ext = '.bin'
            filename = f"{md5}{ext}"
        
        return filename
    
    def get_cached_file(self, url: str) -> Optional[str]:
        """Get cached file path if exists"""
        filename = self._get_cache_filename(url)
        file_path = os.path.join(self.storage_dir, filename)
        
        if os.path.exists(file_path):
            return file_path
        return None
    
    async def cache_file(self, url: str, source_path: str) -> str:
        """
        Cache a file and return its path
        
        Args:
            url: Original file URL
            source_path: Source file path
        
        Returns:
            str: Cached file path
        """
        try:
            filename = self._get_cache_filename(url)
            new_path = os.path.join(self.storage_dir, filename)
            
            # Only copy if file doesn't exist
            if not os.path.exists(new_path):
                shutil.copy2(source_path, new_path)
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error caching file: {str(e)}")
            raise

# Create global instances
output_file_manager = OutputFileManager()
input_file_manager = InputFileManager()
