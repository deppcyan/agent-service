from typing import Dict, Any, List
from ..core.orchestrator import WorkflowBuilder, ServiceStep
from ..services.nodes.qwen_vl import QwenVLNode
from ..services.nodes.qwen_edit import QwenEditNode
from ..services.nodes.wan_i2v import WanI2VNode
from ..services.nodes.video_concat import VideoConcatNode
from ..core.utils import get_service_url

class ImageToVideoWorkflow:
    """Image to video workflow using orchestrator"""
    
    def __init__(self, services: Dict[str, Any]):
        self.qwen_vl = QwenVLNode(services["qwen_vl_url"], services["api_key"])
        self.qwen_edit = QwenEditNode(services["qwen_edit_url"], services["api_key"])
        self.wan_i2v = WanI2VNode(services["wan_i2v_url"], services["api_key"])
        self.video_concat = VideoConcatNode(services["video_concat_url"], services["api_key"])
        
        # Store base callback URL
        self.base_callback_url = services["base_callback_url"]
        
        # Build the workflow
        self.workflow = self._build_workflow()
    
    def _get_callback_url(self, service_name: str) -> str:
        """Get callback URL for a service"""
        return f"{self.base_callback_url}/{service_name}"
    
    def _build_workflow(self):
        """Build the workflow using WorkflowBuilder"""
        builder = WorkflowBuilder("image_to_video")
        
        # Add QwenVL step for scene generation
        # QwenVL 是同步服务，不需要回调
        builder.add_service(
            "scene_generation",
            self.qwen_vl,
            input_mapping={
                "image_url": "input_image_url",
                "prompt": "prompt",
                "system_prompt": "system_prompt"
            },
            output_mapping={
                "scenes": "enhanced_prompt"
            }
        )
        
        # Add parallel step for image editing
        edit_steps = []
        for i in range(3):  # Maximum 3 scenes
            step = ServiceStep(
                f"image_edit_{i}",
                self.qwen_edit,
                input_mapping={
                    "image_url": "input_image_url",
                    "prompt": f"scenes[{i}]",
                    "width": "width",
                    "height": "height"
                },
                output_mapping={
                    f"edited_image_{i}": "output_url"
                },
                callback_url=self._get_callback_url("qwen-edit")  # 添加回调 URL
            )
            edit_steps.append(step)
        
        builder.add_parallel("image_editing", edit_steps)
        
        # Add parallel step for video generation
        video_steps = []
        for i in range(3):
            step = ServiceStep(
                f"video_generation_{i}",
                self.wan_i2v,
                input_mapping={
                    "image_url": f"edited_image_{i}",
                    "prompt": f"scenes[{i}]",
                    "width": "width",
                    "height": "height",
                    "duration": "duration"
                },
                output_mapping={
                    f"video_{i}": "output_url"
                },
                callback_url=self._get_callback_url("wan-i2v")  # 添加回调 URL
            )
            video_steps.append(step)
        
        builder.add_parallel("video_generation", video_steps)
        
        # Add video concatenation step
        builder.add_service(
            "video_concatenation",
            self.video_concat,
            input_mapping={
                "video_urls": ["video_0", "video_1", "video_2"],
                "crf": "crf"
            },
            output_mapping={
                "final_video": "output_url"
            },
            callback_url=self._get_callback_url("concat-upscale")  # 添加回调 URL
        )
        
        return builder.build()
    
    def _extract_scenes(self, text: str, max_scenes: int = 3) -> List[str]:
        """Extract scene descriptions from QwenVL output"""
        scenes = []
        for line in text.split("\n"):
            if line.startswith("Next Scene:"):
                scenes.append(line.replace("Next Scene:", "").strip())
                if len(scenes) >= max_scenes:
                    break
        return scenes
    
    async def execute(self, job_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        # Prepare initial context
        context = {
            "job_id": job_id,
            "input_image_url": input_data["input"][0]["url"],
            "prompt": input_data["options"].get("prompt", ""),
            "system_prompt": input_data["options"].get("system_prompt", ""),
            "width": input_data["options"].get("width", 768),
            "height": input_data["options"].get("height", 768),
            "duration": input_data["options"].get("duration", 5),
            "crf": input_data["options"].get("crf", None)
        }
        
        # Execute workflow
        result = await self.workflow.execute(context)
        
        # Return results
        return {
            "status": "completed",
            "output_url": result.get("final_video"),
            "intermediate_results": {
                "scenes": self._extract_scenes(result["scenes"]),
                "edited_images": [
                    result.get(f"edited_image_{i}") for i in range(3)
                ],
                "videos": [
                    result.get(f"video_{i}") for i in range(3)
                ]
            }
        }

# Create workflow instance
def create_workflow(services: Dict[str, Any]) -> ImageToVideoWorkflow:
    return ImageToVideoWorkflow(services)