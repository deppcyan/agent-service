from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
import aiohttp
from app.core.logger import logger
from app.core.callback_manager import callback_manager

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
            logger.debug("Creating HTTP session", 
                       extra={"job_id": job_id, "service": self.service_name})
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/v1/generate"
                import json
                
                # Log request details
                logger.info(
                    f"Making POST request to {url}",
                    extra={
                        "job_id": job_id,
                        "url": url,
                        "service": self.service_name
                    }
                )
                # Log request JSON data
                logger.info(
                    "Request JSON data:\n" + json.dumps(data, indent=2, ensure_ascii=False),
                    extra={
                        "job_id": job_id,
                        "service": self.service_name
                    }
                )
                
                async with session.post(
                    url,
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Service request failed with status {response.status}\nError: {error_text}",
                            extra={
                                "job_id": job_id,
                                "service": self.service_name,
                                "status": response.status
                            }
                        )
                        raise Exception(
                            f"Service call failed with status {response.status}: {error_text}"
                        )
                    
                    response_data = await response.json()
                    logger.info(
                        f"Successfully received response (status: {response.status})",
                        extra={
                            "job_id": job_id,
                            "service": self.service_name
                        }
                    )
                    # Log response JSON data
                    logger.info(
                        "Response JSON data:\n" + json.dumps(response_data, indent=2, ensure_ascii=False),
                        extra={
                            "job_id": job_id,
                            "service": self.service_name
                        }
                    )
                    return response_data
        
        return await _request()
    
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
            logger.info(f"Starting generation for service {self.service_name}", 
                       extra={"job_id": job_id, "service": self.service_name})
            
            # Register callback handler
            if callback_url:
                logger.debug(f"Registering callback handler for URL: {callback_url}", 
                           extra={"job_id": job_id, "callback_url": callback_url})
                callback_manager.register_handler(
                    self.service_name,
                    job_id,
                    self._handle_callback
                )
            
            # Prepare and send request
            logger.debug("Preparing request data", extra={"job_id": job_id})
            request_data = self._prepare_request(input_data, callback_url)
            
            logger.info("Sending request to service", 
                       extra={"job_id": job_id, "service": self.service_name})
            response = await self._make_request(request_data, job_id)
            logger.debug("Received response from service", 
                        extra={"job_id": job_id, "service": self.service_name})
            
            # If no callback URL, return response directly
            if not callback_url:
                logger.info("Generation completed successfully (no callback)", 
                          extra={"job_id": job_id, "service": self.service_name})
                return response
            
            # Wait for callback
            try:
                logger.info("Waiting for callback", 
                          extra={"job_id": job_id, "service": self.service_name})
                callback_data = await callback_manager.wait_for_callback(job_id, timeout)
                logger.debug("Received callback data", 
                           extra={"job_id": job_id, "service": self.service_name})
                result = await self._handle_callback(callback_data)
                logger.info("Generation completed successfully (with callback)", 
                          extra={"job_id": job_id, "service": self.service_name})
                return result
            except Exception as e:
                logger.error(f"Callback handling failed: {str(e)}", 
                           extra={"job_id": job_id, "service": self.service_name})
                callback_manager.unregister_handler(job_id)
                raise Exception(f"Callback failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}", extra={"job_id": job_id})
            raise
    
    async def cancel(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running job"""
        try:
            logger.info(f"Attempting to cancel job for service {self.service_name}", 
                       extra={"job_id": job_id, "service": self.service_name})
            
            headers = {"X-API-Key": self.api_key}
            logger.debug("Creating HTTP session for cancel request", 
                       extra={"job_id": job_id, "service": self.service_name})
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/cancel/{job_id}"
                import json
                
                # Log request details
                logger.info(
                    f"Making DELETE request to {url}",
                    extra={
                        "job_id": job_id,
                        "url": url,
                        "service": self.service_name
                    }
                )
                
                async with session.delete(
                    url,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Cancel request failed with status {response.status}\nError: {error_text}",
                            extra={
                                "job_id": job_id,
                                "service": self.service_name,
                                "status": response.status
                            }
                        )
                        raise Exception(
                            f"Cancel failed with status {response.status}: {error_text}"
                        )
                    
                    response_data = await response.json()
                    logger.info(
                        f"Job cancelled successfully (status: {response.status})",
                        extra={
                            "job_id": job_id,
                            "service": self.service_name
                        }
                    )
                    # Log response JSON data
                    logger.info(
                        "Response JSON data:\n" + json.dumps(response_data, indent=2, ensure_ascii=False),
                        extra={
                            "job_id": job_id,
                            "service": self.service_name
                        }
                    )
                    return response_data
                    
        except Exception as e:
            logger.error(f"Cancel failed: {str(e)}", 
                        extra={"job_id": job_id, "service": self.service_name})
            raise
