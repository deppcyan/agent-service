from typing import Dict, Any, List
import asyncio
import json
from app.workflow.base import WorkflowNode
from app.workflow.nodes.wan_i2v import WanI2VNode
from app.utils.logger import logger

class WanI2VBatchNode(WorkflowNode):
    """Node for batch processing with WanI2V (Image to Video) service"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("api_url", "string", True)  # API endpoint URL
        self.add_input_port("timeout", "number", False, 300)  # Timeout in seconds
        self.add_input_port("image_urls", "array", True)  # List of image URLs
        self.add_input_port("prompts", "array", False, [])  # List of prompts
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        self.add_input_port("batch_size", "number", False, 1)
        self.add_input_port("output_format", "string", False, "mp4")
        self.add_input_port("duration", "number", False, 5)
        self.add_input_port("seed", "number", False, None)
        self.add_input_port("callback_url", "string", False)  # Optional callback URL for async processing
        
        # Output ports
        self.add_output_port("output_urls", "array")  # List of output URLs
        self.add_output_port("options_list", "array")  # List of options
        self.add_output_port("status_list", "array")  # List of statuses
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs are missing")
            
        image_urls = self.input_values["image_urls"]
        prompts = self.input_values.get("prompts", [""] * len(image_urls))
        width = self.input_values.get("width", 768)
        height = self.input_values.get("height", 768)
        batch_size = self.input_values.get("batch_size", 1)
        output_format = self.input_values.get("output_format", "mp4")
        duration = self.input_values.get("duration", 5)
        seed = self.input_values.get("seed", None)
        
        # Ensure prompts list matches the length of image_urls
        if len(prompts) < len(image_urls):
            prompts.extend([""] * (len(image_urls) - len(prompts)))
            logger.info(f"Extended prompts list to match {len(image_urls)} images")
        
        # Prepare tasks for parallel processing
        tasks = []
        for image_url, prompt in zip(image_urls, prompts):
            # Create a new WanI2VNode instance for each task to avoid state conflicts
            i2v_node = WanI2VNode()
            i2v_node.input_values = {
                "api_url": self.input_values["api_url"],
                "timeout": self.input_values.get("timeout", 300),
                "image_url": image_url,
                "prompt": prompt,
                "width": width,
                "height": height,
                "batch_size": batch_size,
                "output_format": output_format,
                "duration": duration,
                "seed": seed,
                "callback_url": self.input_values.get("callback_url")
            }
            tasks.append(i2v_node.process())
        
        # Execute all tasks in parallel while maintaining order
        task_list = [asyncio.create_task(task) for task in tasks]
        
        # Pre-allocate result lists to maintain order
        output_urls = [None] * len(tasks)
        options_list = [None] * len(tasks)
        status_list = [None] * len(tasks)
        
        # Process each task in order of completion
        for i, task in enumerate(task_list):
            try:
                result = await task
                output_urls[i] = result["output_url"]
                options_list[i] = result["options"]
                status_list[i] = result["status"]
                logger.info(f"Task {i} completed successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Task {i} failed: {error_msg}")
                output_urls[i] = None
                options_list[i] = {"error": error_msg}
                status_list[i] = "failed"
        
        logger.info(f"Batch processing completed. {len([url for url in output_urls if url])} successful, "
                   f"{len([url for url in output_urls if not url])} failed")
        
        self.output_values = {
            "output_urls": output_urls,
            "options_list": options_list,
            "status_list": status_list
        }
        return self.output_values
