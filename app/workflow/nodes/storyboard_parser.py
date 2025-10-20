from typing import Dict, Any, List
import re
import json
from app.workflow.base import WorkflowNode
from app.utils.logger import logger

class StoryboardParserNode(WorkflowNode):
    """Node for parsing QwenVL output into storyboard prompts"""
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # Input ports
        self.add_input_port("text", "string", True)  # QwenVL response text
        self.add_input_port("image_url", "string", True)  # Base image URL to be edited
        
        # Output ports
        self.add_output_port("prompts", "array")  # List of prompts for each shot
        self.add_output_port("image_urls", "array")  # List of image URLs (duplicated for each shot)
        self.add_output_port("metadata", "object")  # Additional metadata like scene numbers, descriptions
    
    def _parse_shots(self, text: str) -> List[Dict[str, Any]]:
        """Parse the text into individual shots with their details"""
        shots = []
        
        # Split by "Next Scene:"
        scene_texts = text.split("Next Scene:")
        # Filter out empty scenes and strip whitespace
        scene_texts = [scene.strip() for scene in scene_texts if scene.strip()]
        
        for i, scene_text in enumerate(scene_texts, 1):
            # Use the scene description directly as the prompt
            shots.append({
                "shot_number": i,
                "description": scene_text,
                "prompt": scene_text + "，高清摄影，电影感，写实风格"
            })
        
        return shots
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs are missing")
        
        text = self.input_values["text"]
        image_url = self.input_values["image_url"]
        
        logger.info(f"StoryboardParser processing text input: {text[:200]}...")
        logger.info(f"Using base image URL: {image_url}")
        
        shots = self._parse_shots(text)
        logger.info(f"Parsed {len(shots)} shots from input text")
        
        # Extract prompts and create corresponding image_urls list
        prompts = [shot["prompt"] for shot in shots]
        # Duplicate the image_url for each shot
        image_urls = [image_url] * len(shots)
        
        metadata = {
            "total_shots": len(shots),
            "shots": shots
        }
        
        logger.info(f"Generated prompts: {json.dumps(prompts, ensure_ascii=False, indent=2)}")
        logger.debug(f"Full metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        
        self.output_values = {
            "prompts": prompts,
            "image_urls": image_urls,
            "metadata": metadata
        }
        return self.output_values