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
        self.add_input_port("text", "string", True)  # QwenVL response text (JSON format)
        self.add_input_port("image_url", "string", False)  # Base image URL to be edited
        self.add_input_port("max_segments", "number", False, 3)  # Maximum number of segments/shots to process
        
        # Output ports
        self.add_output_port("prompts", "array")  # List of image prompts for each shot
        self.add_output_port("video_prompts", "array")  # List of video prompts for each shot
        self.add_output_port("dialogues", "array")  # List of dialogues for each shot
        self.add_output_port("image_urls", "array")  # List of image URLs (duplicated for each shot)
        self.add_output_port("metadata", "object")  # Additional metadata like scene numbers, descriptions
    
    def _parse_shots(self, text: str) -> List[Dict[str, Any]]:
        """Parse the JSON formatted text into individual shots with their details"""
        try:
            # Remove markdown code block markers if present
            text = text.strip()
            if text.startswith("```"):
                # Find the first newline to skip the ```json line
                first_newline = text.find("\n")
                if first_newline != -1:
                    # Find the last ``` and remove it
                    text = text[first_newline:].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
            
            data = json.loads(text)
            segments = data.get("expanded_story", {}).get("segments", [])
            
            # Limit the number of segments based on max_segments input
            max_segments = self.input_values.get("max_segments", 3)
            if len(segments) > max_segments:
                logger.warning(f"Number of segments ({len(segments)}) exceeds max_segments ({max_segments}). Truncating to first {max_segments} segments.")
                segments = segments[:max_segments]
            shots = []
            
            for segment in segments:
                shot = {
                    "shot_number": segment.get("segment_number", 0),
                    "description": segment.get("narrative_summary", ""),
                    "prompt": segment.get("image_prompt", ""),
                    "video_prompt": segment.get("video_prompt", ""),
                    "dialogue": segment.get("dialogue", "")
                }
                shots.append(shot)
            
            return shots
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON input: {e}")
            raise ValueError(f"Invalid JSON input: {e}")
    
    async def process(self) -> Dict[str, Any]:
        if not self.validate_inputs():
            raise ValueError("Required inputs are missing")
        
        text = self.input_values["text"]
        image_url = self.input_values["image_url"]
        
        logger.info(f"StoryboardParser processing text input: {text[:200]}...")
        logger.info(f"Using base image URL: {image_url}")
        
        shots = self._parse_shots(text)
        logger.info(f"Parsed {len(shots)} shots from input text")
        
        # Extract all required fields from shots
        prompts = [shot["prompt"] for shot in shots]
        video_prompts = [shot["video_prompt"] for shot in shots]
        # Combine all dialogues in each shot into a single string
        dialogues = [shot["dialogue"] for shot in shots]
        # Duplicate the image_url for each shot
        image_urls = [image_url] * len(shots)
        
        metadata = {
            "total_shots": len(shots)
        }
        
        logger.info(f"Generated prompts: {json.dumps(prompts, ensure_ascii=False, indent=2)}")
        logger.info(f"Generated video prompts: {json.dumps(video_prompts, ensure_ascii=False, indent=2)}")
        logger.info(f"Generated dialogues: {json.dumps(dialogues, ensure_ascii=False, indent=2)}")
        logger.debug(f"Full metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
        
        self.output_values = {
            "prompts": prompts,
            "video_prompts": video_prompts,
            "dialogues": dialogues,
            "image_urls": image_urls,
            "metadata": metadata
        }
        return self.output_values