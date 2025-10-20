import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from collections import defaultdict
from app.schemas.api import JobState, WebhookResponse
from app.utils.logger import logger, pod_id
from app.utils.utils import calculate_wait_time, get_service_url
from app.workflow.executor import WorkflowExecutor
import aiohttp

class JobManager:
    """Manages job queues and states"""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        # Job states
        self.job_states: Dict[str, JobState] = {}
        
        # Job statistics
        self.job_stats = defaultdict(int)
        
        # Concurrency control
        self.max_concurrent_jobs = max_concurrent_jobs
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_jobs)
        
        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Workflow manager
        from app.core.workflow_manager import workflow_manager
        self.workflow_manager = workflow_manager
    
    async def add_job(self, job_state: JobState) -> Dict[str, Any]:
        """Add a new job and start workflow execution"""
        # Store job state
        self.job_states[job_state.id] = job_state
        
        # Create workflow executor with input and options
        workflow = self.workflow_manager.create_workflow_executor(
            job_state.model,
            {
                "input": job_state.input,
                "options": job_state.options
            }
        )
        
        if not workflow:
            await self.update_job_state(job_state.id, {
                "status": "failed",
                "error": f"Workflow not found: {job_state.model}"
            })
            raise ValueError(f"Workflow not found: {job_state.model}")
        
        # Start workflow execution
        task = asyncio.create_task(self._execute_workflow(job_state.id, workflow, {"input": job_state.input, "options": job_state.options}))
        self.active_tasks[job_state.id] = task
        
        # Calculate queue stats
        '''
        current_queue_size = len([job for job in self.job_states.values() 
                                if job.status in ['pending', 'processing']])
        estimated_wait_time = calculate_wait_time(self.job_states)
        '''

        current_queue_size = 0
        estimated_wait_time = 0
        return {
            "id": job_state.id,
            "pod_id": pod_id,
            "queue_position": current_queue_size,
            "estimated_wait_time": estimated_wait_time,
            "pod_url": get_service_url()
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
        """Cancel a job in any state"""
        if job_id not in self.job_states:
            raise ValueError("Job not found")
            
        job_state = self.job_states[job_id]
        if job_state.status in ['completed', 'failed', 'cancelled']:
            raise ValueError(f"Cannot cancel job in {job_state.status} state")
        
        # Cancel active task
        if job_id in self.active_tasks:
            task = self.active_tasks[job_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_tasks[job_id]
        
        # Update state with cancellation time
        updates = {
            "status": "cancelled",
            "error": "Job cancelled by user",
            "completed_at": datetime.now(timezone.utc)
        }
        await self.update_job_state(job_id, updates)
        
        # Send cancellation webhook
        await self._send_webhook(job_id)
        
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
            createdAt=job_state.created_at.isoformat(),
            status=job_state.status,
            model=job_state.model,
            input=job_state.input,
            webhookUrl=job_state.webhook_url,
            options=job_state.options,
            stream=False,
            outputUrl=job_state.output_url,
            localUrl=job_state.local_url,
            outputWasabiUrl=job_state.output_wasabi_url,
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
    
    async def _execute_workflow(self, job_id: str, workflow_executor: WorkflowExecutor, input_data: Dict[str, Any]) -> None:
        """Execute workflow for a job"""
        try:
            # Get job state to access options
            job_state = self.job_states[job_id]
            
            # Update job status to processing
            await self.update_job_state(job_id, {"status": "processing"})
            
            # Execute workflow with both input and options
            async with self.processing_semaphore:
                try:
                    # Execute the workflow graph
                    results = await workflow_executor.execute()
                    
                    # Get final output from the last node
                    final_node = list(workflow_executor.graph.nodes.values())[-1]
                    final_result = workflow_executor.get_node_result(final_node.node_id)
                    
                    # Update job state with results and trigger webhook
                    updates = {
                        "status": "completed",
                        "output_url": final_result.get("output_url"),
                        "completed_at": datetime.now(timezone.utc)
                    }
                    await self.update_job_state(job_id, updates)
                    await self._send_webhook(job_id)  # 成功时发送回调
                    
                except asyncio.CancelledError:
                    logger.info(f"Workflow execution cancelled for job {job_id}", 
                              extra={"job_id": job_id})
                    # 取消时的状态更新和回调在 cancel_job 中处理
                    raise
                    
                except Exception as e:
                    error_msg = f"Workflow execution failed: {str(e)}"
                    logger.error(error_msg, extra={"job_id": job_id})
                    # 更新失败状态并发送回调
                    updates = {
                        "status": "failed",
                        "error": error_msg,
                        "completed_at": datetime.now(timezone.utc)
                    }
                    await self.update_job_state(job_id, updates)
                    await self._send_webhook(job_id)  # 失败时发送回调
                    raise
                
        except asyncio.CancelledError:
            # Job was cancelled, state and webhook already handled in cancel_job
            pass
        except Exception as e:
            # Error already logged and webhook sent
            pass
        finally:
            # Clean up task tracking
            if job_id in self.active_tasks:
                del self.active_tasks[job_id]

# Create global job manager instance
job_manager = JobManager()
