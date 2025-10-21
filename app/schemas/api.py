from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class InputItem(BaseModel):
    type: str = Field(..., description="Input type: 'image' or 'video'")
    url: str = Field(..., description="S3 URL for images or videos")

class Options(BaseModel):
    prompt: Optional[str] = Field(None, description="Generation prompt")
    seed: Optional[int] = Field(None, description="Random seed for generation")
    duration: Optional[int] = Field(None, description="Video duration in seconds (4-10)")
    upload_url: Optional[str] = Field(None, description="Custom AWS S3 upload URL")
    upload_wasabi_url: Optional[str] = Field(None, description="Custom Wasabi upload URL")
    resolution: Optional[str] = Field(None, description="Output resolution (e.g., '512x512')")
    crf: Optional[int] = Field(None, description="Video CRF value")
    width: Optional[int] = Field(768, description="Output width in pixels")
    height: Optional[int] = Field(768, description="Output height in pixels")

class GenerateRequest(BaseModel):
    model: str = Field(..., description="Model name to use")
    input: List[InputItem] = Field(..., description="List of input items")
    options: Options = Field(..., description="Generation options")
    webhookUrl: str = Field(..., description="Webhook URL for completion notification")

class JobResponse(BaseModel):
    id: str = Field(..., description="Job ID")
    pod_id: str = Field(..., description="Pod ID")
    queue_position: int = Field(..., description="Position in queue")
    estimated_wait_time: float = Field(..., description="Estimated wait time in seconds")
    pod_url: str = Field(..., description="Service URL")

class JobState(BaseModel):
    id: str = Field(..., description="Job ID")
    created_at: datetime = Field(..., description="Job creation time")
    completed_at: datetime = Field(None, description="Job completed time")
    status: str = Field(..., description="Job status")
    model: str = Field(..., description="Model name")
    input: List[Dict[str, Any]] = Field(..., description="Input data")
    webhook_url: str = Field(..., description="Webhook URL")
    options: Dict[str, Any] = Field(..., description="Job options")
    output_url: Optional[str] = Field(None, description="Output S3 URL")
    local_url: Optional[str] = Field(None, description="Local file URL")
    output_wasabi_url: Optional[str] = Field(None, description="Output Wasabi URL")
    error: Optional[str] = Field(None, description="Error message if failed")
    workflow_task_id: Optional[str] = Field(None, description="Workflow task ID")
    

class WebhookResponse(BaseModel):
    id: str = Field(..., description="Job ID")
    createdAt: str = Field(..., description="Job creation time")
    status: str = Field(..., description="Job status")
    model: str = Field(..., description="Model name")
    input: List[InputItem] = Field(..., description="Input data")
    webhookUrl: str = Field(..., description="Webhook URL")
    options: Dict[str, Any] = Field(default={}, description="Job options")
    stream: bool = Field(default=True, description="Stream mode")
    outputUrl: Optional[str] = Field(None, description="Output S3 URL")
    localUrl: Optional[str] = Field(None, description="Local file URL")
    outputWasabiUrl: Optional[str] = Field(None, description="Output Wasabi URL")
    error: Optional[str] = Field(None, description="Error message if failed")

class FileInfo(BaseModel):
    file_id: str = Field(..., description="File ID")
    created_at: datetime = Field(..., description="File creation time")
    job_id: str = Field(..., description="Associated job ID")
    filename: str = Field(..., description="Original filename")
    expires_at: datetime = Field(..., description="File expiration time")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    jobs: Dict[str, int] = Field(..., description="Job statistics")

class CancelResponse(BaseModel):
    status: str = Field(..., description="Cancellation status")
    job_id: str = Field(..., description="Cancelled job ID")

class PurgeResponse(BaseModel):
    removed: int = Field(..., description="Number of removed jobs")
    status: str = Field(..., description="Operation status")

class WorkflowRequest(BaseModel):
    workflow: Dict[str, Any] = Field(..., description="Workflow configuration")
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
    webhook_url: str = Field(..., description="Webhook URL for workflow completion notification")
