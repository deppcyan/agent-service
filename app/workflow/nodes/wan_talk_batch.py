from typing import Dict, Any, List
import asyncio
import json
from app.workflow.base import WorkflowNode
from app.workflow.nodes.wan_talk import WanTalkNode
from app.utils.logger import logger

class WanTalkBatchNode(WorkflowNode):
    """Node for batch processing with WanTalk (Talking Head) service"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("api_url", "string", True)  # API endpoint URL
        self.add_input_port("timeout", "number", False, 300)  # Timeout in seconds
        self.add_input_port("image_urls", "array", True)  # List of image URLs
        self.add_input_port("audio_urls", "array", True)  # List of audio URLs
        self.add_input_port("prompts", "array", False, [])  # List of prompts
        self.add_input_port("audio_prompts", "array", False, [])  # List of audio prompts
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
        audio_urls = self.input_values["audio_urls"]
        prompts = self.input_values.get("prompts", [""] * len(image_urls))
        audio_prompts = self.input_values.get("audio_prompts", [""] * len(image_urls))
        width = self.input_values.get("width", 768)
        height = self.input_values.get("height", 768)
        batch_size = self.input_values.get("batch_size", 1)
        output_format = self.input_values.get("output_format", "mp4")
        duration = self.input_values.get("duration", 5)
        seed = self.input_values.get("seed", None)
        
        # Ensure prompts, audio_prompts and audio_urls lists match the length of image_urls
        if len(prompts) < len(image_urls):
            prompts.extend([""] * (len(image_urls) - len(prompts)))
            logger.info(f"Extended prompts list to match {len(image_urls)} images")
        
        if len(audio_prompts) < len(image_urls):
            audio_prompts.extend([""] * (len(image_urls) - len(audio_prompts)))
            logger.info(f"Extended audio_prompts list to match {len(image_urls)} images")
            
        if len(audio_urls) < len(image_urls):
            # Get the last non-empty audio URL
            last_valid_audio = next((url for url in reversed(audio_urls) if url), audio_urls[0])
            # Extend the list with copies of the last valid audio URL
            audio_urls.extend([last_valid_audio] * (len(image_urls) - len(audio_urls)))
            logger.info(f"Extended audio_urls list to match {len(image_urls)} images by repeating last valid audio: {last_valid_audio}")
        
        # Prepare tasks for parallel processing
        tasks = []
        for image_url, audio_url, prompt, audio_prompt in zip(image_urls, audio_urls, prompts, audio_prompts):
            # Create a new WanTalkNode instance for each task to avoid state conflicts
            talk_node = WanTalkNode()
            talk_node.input_values = {
                "api_url": self.input_values["api_url"],
                "timeout": self.input_values.get("timeout", 300),
                "image_url": image_url,
                "audio_url": audio_url,
                "prompt": prompt,
                "audio_prompt": audio_prompt,
                "width": width,
                "height": height,
                "batch_size": batch_size,
                "output_format": output_format,
                "duration": duration,
                "seed": seed,
                "callback_url": self.input_values.get("callback_url")
            }
            tasks.append(talk_node.process())
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any errors
        output_urls = []
        options_list = []
        status_list = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle error case
                error_msg = str(result)
                logger.error(f"Task {i} failed: {error_msg}")
                output_urls.append(None)
                options_list.append({"error": error_msg})
                status_list.append("failed")
            else:
                output_urls.append(result["output_url"])
                options_list.append(result["options"])
                status_list.append(result["status"])
        
        logger.info(f"Batch processing completed. {len([url for url in output_urls if url])} successful, "
                   f"{len([url for url in output_urls if not url])} failed")
        
        self.output_values = {
            "output_urls": output_urls,
            "options_list": options_list,
            "status_list": status_list
        }
        return self.output_values
