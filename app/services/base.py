from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
import aiohttp
from ..core.logger import logger
from ..core.callback_manager import callback_manager
from ..core.concurrency import concurrency_manager

class AsyncServiceNode(ABC):
    """Base class for async service nodes"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.service_name = self._get_service_name()
    
    @abstractmethod
    def _get_service_name(self) -> str:
        """Return the service name"""
        pass
    
    @abstractmethod
    def _prepare_request(self, input_data: Dict[str, Any], 
                        callback_url: Optional[str] = None) -> Dict[str, Any]:
        """Prepare request data for the service"""
        pass
    
    @abstractmethod
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service callback data"""
        pass
    
    async def _make_request(self, data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Make HTTP request to service"""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        async def _request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/generate",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Service call failed with status {response.status}: {error_text}"
                        )
                    return await response.json()
        
        return await concurrency_manager.execute_with_limits(
            self.service_name,
            _request,
            job_id=job_id
        )
    
    async def generate(self, input_data: Dict[str, Any], job_id: str, 
                      callback_url: Optional[str] = None,
                      timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate output using the service
        
        Args:
            input_data: Input data for the service
            job_id: Job ID
            callback_url: Optional callback URL
            timeout: Optional timeout for waiting for callback
            
        Returns:
            Dict containing service response
        """
        try:
            # Register callback handler
            if callback_url:
                callback_manager.register_handler(
                    self.service_name,
                    job_id,
                    self._handle_callback
                )
            
            # Prepare and send request
            request_data = self._prepare_request(input_data, callback_url)
            response = await self._make_request(request_data, job_id)
            
            # If no callback URL, return response directly
            if not callback_url:
                return response
            
            # Wait for callback
            try:
                callback_data = await callback_manager.wait_for_callback(job_id, timeout)
                return await self._handle_callback(callback_data)
            except Exception as e:
                callback_manager.unregister_handler(job_id)
                raise Exception(f"Callback failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}", extra={"job_id": job_id})
            raise
    
    async def cancel(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job"""
        try:
            headers = {"X-API-Key": self.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.api_url}/cancel/{job_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Cancel failed with status {response.status}: {error_text}"
                        )
                    return await response.json()
        except Exception as e:
            logger.error(f"Cancel failed: {str(e)}", extra={"job_id": job_id})
            raise
