import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timezone
from app.utils.logger import logger

class CallbackManager:
    """Manages service callbacks and their routing"""
    
    def __init__(self):
        # Store callback handlers by job_id
        self.handlers: Dict[str, Callable] = {}
        # Store pending callbacks
        self.pending_callbacks: Dict[str, asyncio.Future] = {}
    
    def register_handler(self, job_id: str, 
                        handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Register a callback handler for a specific service and job"""
        # Store handler directly by job_id
        self.handlers[job_id] = handler
        
        # Create a future for this callback
        self.pending_callbacks[job_id] = asyncio.Future()
    
    def unregister_handler(self, job_id: str) -> None:
        """Unregister a callback handler"""
        # Remove handler if exists
        if job_id in self.handlers:
            del self.handlers[job_id]
        
        # Remove pending callback if exists
        if job_id in self.pending_callbacks:
            if not self.pending_callbacks[job_id].done():
                self.pending_callbacks[job_id].cancel()
            del self.pending_callbacks[job_id]
    
    async def handle_callback(self, data: Dict[str, Any]) -> None:
        """Handle incoming callback from a service"""
        job_id = data.get("id")
        if not job_id:
            logger.error(f"Received callback without job_id", 
                        extra={"job_id": "system"})
            return
        
        try:
            # Get handler for this job
            handler = self.handlers.get(job_id)
            if handler:
                await handler(data)
                
                # Set the future result
                if job_id in self.pending_callbacks:
                    future = self.pending_callbacks[job_id]
                    if not future.done():
                        future.set_result(data)
                
                # Clean up handler
                self.unregister_handler(job_id)
            else:
                logger.warning(f"No handler found for job {job_id}", 
                             extra={"job_id": job_id})
        
        except Exception as e:
            logger.error(f"Error handling callback for job {job_id}: {str(e)}", 
                        extra={"job_id": job_id})
            # Set exception in future
            if job_id in self.pending_callbacks:
                future = self.pending_callbacks[job_id]
                if not future.done():
                    future.set_exception(e)
    
    async def wait_for_callback(self, job_id: str, 
                              timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for a callback to complete"""
        if job_id not in self.pending_callbacks:
            raise ValueError(f"No pending callback found for job {job_id}")
        
        try:
            return await asyncio.wait_for(self.pending_callbacks[job_id], timeout)
        except asyncio.TimeoutError:
            self.unregister_handler(job_id)
            raise TimeoutError(f"Callback timeout for job {job_id}")
        except Exception as e:
            self.unregister_handler(job_id)
            raise

# Create global callback manager instance
callback_manager = CallbackManager()
