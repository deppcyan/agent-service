import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from .logger import logger

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls: int, period: float):
        self.calls = calls  # Number of calls allowed
        self.period = period  # Period in seconds
        self.timestamps = []
    
    async def acquire(self):
        """Acquire permission to make a call"""
        now = datetime.now()
        
        # Remove timestamps older than the period
        self.timestamps = [ts for ts in self.timestamps 
                         if now - ts < timedelta(seconds=self.period)]
        
        # If we've reached the limit, wait
        if len(self.timestamps) >= self.calls:
            wait_time = (self.timestamps[0] + 
                        timedelta(seconds=self.period) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.timestamps.pop(0)
        
        # Add current timestamp
        self.timestamps.append(now)

class RetryWithBackoff:
    """Retry mechanism with exponential backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        delay = self.initial_delay
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f}s",
                        extra={"job_id": kwargs.get("job_id", "system")}
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
        
        raise last_exception

class ConcurrencyManager:
    """Manages concurrency and rate limiting for different services"""
    
    def __init__(self):
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.retry_handler = RetryWithBackoff()
        self.service_semaphores: Dict[str, asyncio.Semaphore] = {}
    
    def configure_rate_limit(self, service: str, calls: int, period: float):
        """Configure rate limiting for a service"""
        self.rate_limiters[service] = RateLimiter(calls, period)
    
    def configure_concurrency(self, service: str, max_concurrent: int):
        """Configure maximum concurrent calls for a service"""
        self.service_semaphores[service] = asyncio.Semaphore(max_concurrent)
    
    async def execute_with_limits(
        self,
        service: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """Execute function with rate limiting and concurrency control"""
        # Get rate limiter and semaphore
        rate_limiter = self.rate_limiters.get(service)
        semaphore = self.service_semaphores.get(service)
        
        # Apply rate limiting if configured
        if rate_limiter:
            await rate_limiter.acquire()
        
        # Apply concurrency control if configured
        if semaphore:
            async with semaphore:
                return await self.retry_handler.execute(func, *args, **kwargs)
        else:
            return await self.retry_handler.execute(func, *args, **kwargs)

# Create global concurrency manager instance
concurrency_manager = ConcurrencyManager()

# Configure default limits
concurrency_manager.configure_rate_limit("qwen-vl", 10, 1.0)  # 10 calls per second
concurrency_manager.configure_rate_limit("wan-i2v", 5, 1.0)   # 5 calls per second
concurrency_manager.configure_rate_limit("qwen-edit", 10, 1.0) # 10 calls per second

concurrency_manager.configure_concurrency("qwen-vl", 20)    # 20 concurrent calls
concurrency_manager.configure_concurrency("wan-i2v", 10)    # 10 concurrent calls
concurrency_manager.configure_concurrency("qwen-edit", 20)  # 20 concurrent calls
