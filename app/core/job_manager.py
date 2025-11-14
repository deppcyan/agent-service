import asyncio
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from collections import defaultdict
from app.schemas.api import JobState, WebhookResponse
from app.utils.logger import logger, pod_id
from app.utils.utils import get_service_url
from app.workflow.executor import WorkflowExecutor
from app.core.model_config import get_model_config
from app.core.preprocess import preprocess_job
import aiohttp

class JobManager:
    """Manages job queues and states"""
    
    def __init__(self):
        # Job states
        self.job_states: Dict[str, JobState] = {}
        
        # Job statistics
        self.job_stats = defaultdict(int)
        
        # Processing time statistics
        self.processing_times: List[float] = []  # Store recent processing times
        self.max_processing_times = 10  # Keep last 10 processing times
        
        # Workflow manager
        from app.core.workflow_manager import workflow_manager
        self.workflow_manager = workflow_manager
    
    async def add_job(self, model: str, input: List[Dict[str, Any]], webhook_url: Optional[str] = None, options: Optional[Dict[str, Any]] = None, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Add a new job and start workflow execution"""
        try:
            # Get model configuration
            model_config = get_model_config(model)
            
            # Use provided job_id or generate new task ID
            task_id = job_id or str(uuid.uuid4())
            
            # Create job state with task ID as job ID
            job_state = JobState(
                id=task_id,
                created_at=datetime.now(timezone.utc),
                status="pending",
                model=model,
                input=input,
                webhook_url=webhook_url,
                options=options or {},
                pod_id=pod_id,
                pod_url=get_service_url(),
                workflow_task_id=task_id
            )
            
            # Store job state
            self.job_states[task_id] = job_state
            
            # Preprocess job data
            preprocessed_data = await preprocess_job(
                {
                    'model': model,
                    'options': options or {},
                    'input': input
                },
                model_config,
                task_id
            )
            
            # Create local webhook URL for workflow callback
            local_webhook_url = f"http://localhost:8001/v1/workflow/webhook/{job_state.id}"
            
            # Start workflow execution with webhook callback and preprocessed data
            workflow_task_id = await self.workflow_manager.execute_workflow(
                preprocessed_data["workflow"],
                local_webhook_url,
                task_id  # Pass the job task_id to workflow execution
            )
            
        except Exception as e:
            # Update job state with error
            await self.update_job_state(job_state.id, {
                "status": "failed",
                "error": str(e)
            })
            raise
        
        # Update job state with task ID
        job_state.workflow_task_id = workflow_task_id
        
        # Calculate queue stats
        current_queue_size = len([job for job in self.job_states.values() 
                                if job.status in ['pending', 'processing']])
        estimated_wait_time = self.calculate_wait_time()
        
        return {
            "id": task_id,
            "pod_id": pod_id,
            "queue_position": current_queue_size,
            "estimated_wait_time": estimated_wait_time,
            "pod_url": get_service_url()
        }
    
    def get_job_state(self, job_id: str) -> Optional[JobState]:
        """Get current state of a job"""
        return self.job_states.get(job_id)
    
    def calculate_wait_time(self) -> float:
        """
        Calculate estimated wait time based on historical processing times
        
        Returns:
            float: Estimated wait time in seconds
        """
        # Get average processing time from historical data
        if self.processing_times:
            avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        else:
            # Default to 60 seconds if no historical data
            avg_processing_time = 60.0
        
        # Calculate queue processing time
        queue_processing_time = 0
        for job_id, state in self.job_states.items():
            if state.status in ['pending', 'processing']:
                queue_processing_time += avg_processing_time
        
        return queue_processing_time
    
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
                
                # Record processing time for completed jobs
                if job_state.status == 'completed' and hasattr(job_state, 'completed_at'):
                    processing_time = (job_state.completed_at - job_state.created_at).total_seconds()
                    self.processing_times.append(processing_time)
                    
                    # Keep only the last N processing times
                    if len(self.processing_times) > self.max_processing_times:
                        self.processing_times = self.processing_times[-self.max_processing_times:]
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a job in any state"""
        if job_id not in self.job_states:
            raise ValueError("Job not found")
            
        job_state = self.job_states[job_id]
        if job_state.status in ['completed', 'failed', 'cancelled']:
            raise ValueError(f"Cannot cancel job in {job_state.status} state")
        
        # Cancel workflow task if exists
        if hasattr(job_state, 'workflow_task_id'):
            await self.workflow_manager.cancel_workflow(job_state.workflow_task_id)
        
        # Update state with cancellation time
        updates = {
            "status": "cancelled",
            "error": "Job cancelled by user",
            "completed_at": datetime.now(timezone.utc)
        }
        await self.update_job_state(job_id, updates)
        
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
            created_at=job_state.created_at.isoformat(),
            status=job_state.status,
            model=job_state.model,
            input=job_state.input,
            webhook_url=job_state.webhook_url,
            options=job_state.options,
            stream=False,
            aws_urls=job_state.aws_urls,
            local_urls=job_state.local_urls,
            wasabi_urls=job_state.wasabi_urls,
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
    
    async def _handle_workflow_callback(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """Handle workflow completion callback"""
        if job_id not in self.job_states:
            return
            
        job_state = self.job_states[job_id]
        
        # Update job state based on workflow status
        updates = {
            "status": status,
            "completed_at": datetime.now(timezone.utc)
        }
        
        if status == "completed" and result:
            # Get model config to map outputs
            model_config = get_model_config(job_state.model)
            # Map outputs according to output_mapping
            for output_key, mapping in model_config.output_mapping.items():
                node_id = mapping["node_id"]
                output_key_name = mapping["output_key"]
                # Get the output value from the result using node_id
                if node_id in result and output_key_name in result[node_id]:
                    updates[output_key] = result[node_id][output_key_name]
        elif error:
            updates["error"] = error
            
        await self.update_job_state(job_id, updates)
        
        # Send webhook to user if URL was provided
        if hasattr(job_state, 'webhook_url') and job_state.webhook_url:
            webhook_response = WebhookResponse(
                id=job_state.id,
                created_at=job_state.created_at.isoformat(),
                status=status,
                model=job_state.model,
                input=job_state.input,
                webhook_url=job_state.webhook_url,
                options=job_state.options,
                stream=False,
                output_url=updates.get("output_url"),
                local_url=job_state.local_url,
                output_wasabi_url=job_state.output_wasabi_url,
                error=updates.get("error")
            )
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(job_state.webhook_url, 
                                        json=webhook_response.model_dump()) as response:
                        if response.status != 200:
                            logger.error(f"User webhook failed with status {response.status}", 
                                    extra={"job_id": job_id})
            except Exception as e:
                logger.error(f"Failed to send user webhook: {str(e)}", 
                            extra={"job_id": job_id})
        
        # Clean up job state if completed/failed/cancelled
        if status in ["completed", "failed", "cancelled"]:
            del self.job_states[job_id]

# Create global job manager instance
job_manager = JobManager()
