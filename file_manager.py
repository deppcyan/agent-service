import os
import uuid
import shutil
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from logger_config import logger

class FileManager:
    """文件管理器，处理文件的存储、清理和访问"""
    
    def __init__(self, storage_dir: str = "storage/outputs", max_age_hours: int = 1):
        self.storage_dir = storage_dir
        self.max_age_hours = max_age_hours
        self.file_info = {}  # 存储文件信息，包括创建时间
        self._ensure_storage_dir()
        self._cleanup_task = None
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def start_cleanup(self):
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def stop_cleanup(self):
        """停止清理任务"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            self._cleanup_task = None
    
    def _is_file_expired(self, creation_time: datetime) -> bool:
        """检查文件是否过期"""
        now = datetime.now(timezone.utc)
        age = now - creation_time
        return age > timedelta(hours=self.max_age_hours)
    
    async def _cleanup_loop(self):
        """定期清理过期文件的循环"""
        while True:
            try:
                now = datetime.now(timezone.utc)
                expired_files = []
                
                # 检查过期文件
                for file_id, info in list(self.file_info.items()):
                    if self._is_file_expired(info['created_at']):
                        file_path = os.path.join(self.storage_dir, info['filename'])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            expired_files.append(file_id)
                
                # 从记录中移除过期文件
                for file_id in expired_files:
                    del self.file_info[file_id]
                
                if expired_files:
                    logger.info(f"Cleaned up {len(expired_files)} expired files", extra={"job_id": "system"})
                
                # 每5分钟检查一次
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled", extra={"job_id": "system"})
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}", extra={"job_id": "system"})
                await asyncio.sleep(60)
    
    def store_file(self, source_path: str, job_id: str) -> str:
        """
        存储文件并返回文件ID
        
        Args:
            source_path: 源文件路径
            job_id: 任务ID
        
        Returns:
            str: 文件ID，用于后续访问
        """
        try:
            # 生成唯一的文件ID和文件名
            file_id = str(uuid.uuid4())
            original_ext = os.path.splitext(source_path)[1]
            new_filename = f"{file_id}{original_ext}"
            new_path = os.path.join(self.storage_dir, new_filename)
            
            # 复制文件到存储目录
            shutil.copy2(source_path, new_path)
            
            # 记录文件信息
            self.file_info[file_id] = {
                'filename': new_filename,
                'created_at': datetime.now(timezone.utc),
                'job_id': job_id
            }
            
            logger.info(f"Stored file {new_filename} for job {job_id}", extra={"job_id": job_id})
            return file_id
            
        except Exception as e:
            logger.error(f"Error storing file: {str(e)}", extra={"job_id": job_id})
            raise
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """获取文件路径，如果文件存在且未过期"""
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
        """获取文件信息"""
        return self.file_info.get(file_id)
    
    def get_expiration_time(self, file_id: str) -> Optional[datetime]:
        """获取文件的过期时间"""
        info = self.file_info.get(file_id)
        if info:
            return info['created_at'] + timedelta(hours=self.max_age_hours)
        return None

class InputFileManager:
    """输入文件管理器，处理输入文件的缓存和访问"""
    
    def __init__(self, storage_dir: str = "storage/inputs"):
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_cache_filename(self, url: str) -> str:
        """
        根据URL生成缓存文件名
        使用URL的最后一部分作为文件名，如果URL中没有文件名，则使用URL的MD5哈希值
        """
        import hashlib
        
        # 获取URL的最后一部分作为文件名
        filename = os.path.basename(url)
        if not filename or filename.endswith('/'):
            # 如果URL没有文件名部分或以/结尾，使用URL的MD5哈希
            md5 = hashlib.md5(url.encode()).hexdigest()
            # 从URL中提取文件扩展名（如果有）
            ext = os.path.splitext(url)[1]
            if not ext:
                ext = '.bin'  # 默认扩展名
            filename = f"{md5}{ext}"
        
        return filename
    
    def get_cached_file(self, url: str) -> Optional[str]:
        """获取缓存的文件路径，如果文件存在"""
        filename = self._get_cache_filename(url)
        file_path = os.path.join(self.storage_dir, filename)
        
        if os.path.exists(file_path):
            return file_path
        return None
    
    def cache_file(self, url: str, source_path: str) -> str:
        """
        缓存文件并返回缓存的文件路径
        
        Args:
            url: 文件的原始URL
            source_path: 源文件路径
        
        Returns:
            str: 缓存的文件路径
        """
        try:
            filename = self._get_cache_filename(url)
            new_path = os.path.join(self.storage_dir, filename)
            
            # 如果文件不存在，才进行复制
            if not os.path.exists(new_path):
                # 复制文件到缓存目录
                shutil.copy2(source_path, new_path)
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error caching file: {str(e)}")
            raise

# 创建全局文件管理器实例
file_manager = FileManager()
input_file_manager = InputFileManager() 