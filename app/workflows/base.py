from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
from ..core.logger import logger
from ..core.storage.downloader import downloader
from ..core.storage.uploader import uploader
from ..core.storage.file_manager import input_file_manager, output_file_manager
from ..core.job_manager import job_manager

class AsyncWorkflow(ABC):
    """Base class for async workflows"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def download_inputs(self, job_id: str) -> Dict[str, str]:
        """Download input files"""
        pass
    
    @abstractmethod
    async def process_job(self, job_id: str, input_files: Dict[str, str]) -> Dict[str, Any]:
        """Process the job"""
        pass
    
    @abstractmethod
    async def upload_outputs(self, job_id: str, output_files: Dict[str, str]) -> Dict[str, str]:
        """Upload output files"""
        pass
    
    async def cleanup(self, job_id: str, files: List[str]) -> None:
        """Clean up temporary files"""
        try:
            await output_file_manager.cleanup_local(files)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}", extra={"job_id": job_id})
    
    async def execute(self, job_id: str) -> None:
        """Execute the workflow"""
        try:
            # Update job status to processing
            await job_manager.update_job_state(job_id, {"status": "processing"})
            
            # Download input files
            input_files = await self.download_inputs(job_id)
            
            # Process the job
            output_files = await self.process_job(job_id, input_files)
            
            # Upload output files
            urls = await self.upload_outputs(job_id, output_files)
            
            # Update job state with output URLs
            await job_manager.update_job_state(job_id, {
                "status": "completed",
                "output_url": urls.get("aws"),
                "output_wasabi_url": urls.get("wasabi"),
                "local_url": urls.get("local")
            })
            
            # Clean up
            all_files = list(input_files.values()) + list(output_files.values())
            await self.cleanup(job_id, all_files)
            
        except asyncio.CancelledError:
            logger.info(f"Workflow cancelled", extra={"job_id": job_id})
            raise
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(error_msg, extra={"job_id": job_id})
            await job_manager.update_job_state(job_id, {
                "status": "failed",
                "error": error_msg
            })
            raise
