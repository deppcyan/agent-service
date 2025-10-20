from typing import Dict, Any, List
import asyncio
import json
from app.workflow.base import WorkflowNode
from app.workflow.nodes.qwen_edit import QwenEditNode
from app.utils.logger import logger
from app.workflow.nodes.async_api_service import AsyncAPIServiceNode

class QwenEditBatchNode(WorkflowNode):
    """Node for batch processing with QwenEdit service"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("api_url", "string", True)  # API endpoint URL
        self.add_input_port("timeout", "number", False, 300)  # Timeout in seconds
        self.add_input_port("image_urls", "array", True)  # List of image URLs
        self.add_input_port("prompts", "array", False, [])  # List of prompts
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        self.add_input_port("callback_url", "string", False)  # Optional callback URL for async processing
        
        # Output ports
        self.add_output_port("output_urls", "array")  # List of output URLs
        self.add_output_port("options_list", "array")  # List of options
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs are missing")
            
        image_urls = self.input_values["image_urls"]
        prompts = self.input_values.get("prompts", [""] * len(image_urls))
        width = self.input_values.get("width", 768)
        height = self.input_values.get("height", 768)
        
        logger.info(f"QwenEditBatch starting with {len(image_urls)} images")
        logger.info(f"API URL: {self.input_values['api_url']}")
        logger.debug(f"Image URLs: {json.dumps(image_urls, ensure_ascii=False)}")
        logger.debug(f"Prompts: {json.dumps(prompts, ensure_ascii=False, indent=2)}")
        
        # Ensure prompts list matches the length of image_urls
        if len(prompts) < len(image_urls):
            prompts.extend([""] * (len(image_urls) - len(prompts)))
            logger.info(f"Extended prompts list to match {len(image_urls)} images")
        
        # Prepare tasks for parallel processing
        tasks = []
        for image_url, prompt in zip(image_urls, prompts):
            # Create a new QwenEditNode instance for each task to avoid state conflicts
            edit_node = QwenEditNode()
            edit_node.input_values = {
                "api_url": self.input_values["api_url"],
                "timeout": self.input_values.get("timeout", 300),
                "image_url": image_url,
                "prompt": prompt,
                "width": width,
                "height": height,
                "callback_url": self.input_values.get("callback_url")
            }
            tasks.append(edit_node.process())
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any errors
        output_urls = []
        options_list = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle error case
                error_msg = str(result)
                logger.error(f"Task {i} failed: {error_msg}")
                output_urls.append(None)
                options_list.append({"error": error_msg})
            else:
                logger.info(f"Task {i} completed successfully")
                logger.debug(f"Task {i} result: {json.dumps(result, ensure_ascii=False)}")
                output_urls.append(result["output_url"])
                options_list.append(result["options"])
        
        logger.info(f"Batch processing completed. {len([url for url in output_urls if url])} successful, "
                   f"{len([url for url in output_urls if not url])} failed")
        
        self.output_values = {
            "output_urls": output_urls
        }
        return self.output_values