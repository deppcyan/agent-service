import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from collections import defaultdict
from ..schemas.api import JobState, WebhookResponse
from ..core.logger import logger
from ..core.utils import calculate_wait_time
import aiohttp

class JobManager:
    """Manages job queues and states"""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        # Job queues
        self.download_queue: asyncio.Queue = asyncio.Queue()
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        
        # Job states
        self.job_states: Dict[str, JobState] = {}
        
        # Job statistics
        self.job_stats = defaultdict(int)
        
        # Concurrency control
        self.max_concurrent_jobs = max_concurrent_jobs
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_jobs)
        
        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_job(self, job_state: JobState) -> Dict[str, Any]:
        """Add a new job to the queue"""
        # Store job state
        self.job_states[job_state.id] = job_state
        
        # Add to download queue
        await self.download_queue.put({"job_id": job_state.id})
        
        # Calculate queue stats
        current_queue_size = len([job for job in self.job_states.values() 
                                if job.status in ['pending', 'processing']])
        estimated_wait_time = calculate_wait_time(self.job_states)
        
        return {
            "id": job_state.id,
            "pod_id": job_state.pod_id,
            "queue_position": current_queue_size,
            "estimated_wait_time": estimated_wait_time,
            "pod_url": job_state.pod_url
        }
    
    def get_job_state(self, job_id: str) -> Optional[JobState]:
        """Get current state of a job"""
        return self.job_states.get(job_id)
    
    async def update_job_state(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update job state and send webhook if status changes"""
        if job_id not in self.job_states:
            return
            
        job_state = self.job_states[job_id]
        old_status = job_state.status
        
        # Update state
        for key, value in updates.items():
            setattr(job_state, key, value)
        
        # Send webhook if status changed
        if old_status != job_state.status:
            await self._send_webhook(job_id)
            
            # Update statistics
            if job_state.status in ['completed', 'failed']:
                self.job_stats[job_state.status] += 1
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a pending job"""
        if job_id not in self.job_states:
            raise ValueError("Job not found")
            
        job_state = self.job_states[job_id]
        if job_state.status != "pending":
            raise ValueError("Can only cancel pending jobs")
        
        # Cancel any active task
        if job_id in self.active_tasks:
            self.active_tasks[job_id].cancel()
            del self.active_tasks[job_id]
        
        # Update state and send webhook
        await self.update_job_state(job_id, {
            "status": "cancelled",
            "error": "Job cancelled by user"
        })
        
        # Remove from states
        del self.job_states[job_id]
        
        return {
            "status": "cancelled",
            "job_id": job_id
        }
    
    async def purge_queue(self) -> Dict[str, Any]:
        """Purge all pending jobs from queue"""
        pending_jobs = [job_id for job_id, job in self.job_states.items() 
                       if job.status == "pending"]
        
        for job_id in pending_jobs:
            await self.cancel_job(job_id)
        
        return {
            "removed": len(pending_jobs),
            "status": "completed"
        }
    
    async def _send_webhook(self, job_id: str) -> None:
        """Send webhook notification"""
        job_state = self.job_states[job_id]
        if not job_state.webhook_url:
            return
            
        # Prepare webhook payload
        webhook_response = WebhookResponse(
            id=job_state.id,
            created_at=job_state.created_at,
            status=job_state.status,
            model=job_state.model,
            input=job_state.input,
            webhook_url=job_state.webhook_url,
            options=job_state.options,
            stream=True,
            output_url=job_state.output_url,
            local_url=job_state.local_url,
            output_wasabi_url=job_state.output_wasabi_url,
            error=job_state.error
        )
        
        # Send webhook
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(job_state.webhook_url, 
                                     json=webhook_response.model_dump()) as response:
                    if response.status != 200:
                        logger.error(f"Webhook failed with status {response.status}", 
                                   extra={"job_id": job_id})
        except Exception as e:
            logger.error(f"Failed to send webhook: {str(e)}", 
                        extra={"job_id": job_id})
    
    def get_health_stats(self) -> Dict[str, Any]:
        """Get current health statistics"""
        current_in_progress = len([job for job in self.job_states.values() 
                                 if job.status == 'processing'])
        current_queue_size = len([job for job in self.job_states.values() 
                                if job.status == 'pending'])
        
        return {
            "status": "ok",
            "jobs": {
                "completed": self.job_stats["completed"],
                "failed": self.job_stats["failed"],
                "inProgress": current_in_progress,
                "inQueue": current_queue_size
            }
        }
    
    async def start_job_processors(self) -> None:
        """Start background job processors"""
        asyncio.create_task(self._process_download_queue())
        for _ in range(self.max_concurrent_jobs):
            asyncio.create_task(self._process_job_queue())
    
    async def _process_download_queue(self) -> None:
        """Process download queue"""
        while True:
            try:
                job_info = await self.download_queue.get()
                job_id = job_info["job_id"]
                
                # Create task for downloading
                task = asyncio.create_task(self._handle_download(job_id))
                self.active_tasks[job_id] = task
                
                # Wait for download to complete
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Download cancelled for job {job_id}", 
                              extra={"job_id": job_id})
                except Exception as e:
                    logger.error(f"Download failed: {str(e)}", 
                               extra={"job_id": job_id})
                finally:
                    if job_id in self.active_tasks:
                        del self.active_tasks[job_id]
                    
                self.download_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in download queue processor: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_job_queue(self) -> None:
        """Process job queue"""
        while True:
            try:
                job_info = await self.processing_queue.get()
                job_id = job_info["job_id"]
                
                async with self.processing_semaphore:
                    # Create task for processing
                    task = asyncio.create_task(self._handle_processing(job_id))
                    self.active_tasks[job_id] = task
                    
                    # Wait for processing to complete
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"Processing cancelled for job {job_id}", 
                                  extra={"job_id": job_id})
                    except Exception as e:
                        logger.error(f"Processing failed: {str(e)}", 
                                   extra={"job_id": job_id})
                    finally:
                        if job_id in self.active_tasks:
                            del self.active_tasks[job_id]
                
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in job queue processor: {str(e)}")
                await asyncio.sleep(1)
    
    async def _handle_download(self, job_id: str) -> None:
        """Handle file downloads for a job"""
        # This will be implemented in the workflow
        pass
    
    async def _handle_processing(self, job_id: str) -> None:
        """Handle job processing"""
        # This will be implemented in the workflow
        pass

# Create global job manager instance
job_manager = JobManager()
