from typing import Dict, Any, List
from app.core.orchestrator import WorkflowBuilder, ServiceStep, Workflow
from app.services.base import AsyncServiceNode
from app.config.workflows import workflow_registry
from app.core.utils import get_service_url
from app.workflows.base import AsyncWorkflow

class ImageToVideoWorkflow(AsyncWorkflow):
    """Image to video workflow using orchestrator"""
    
    def __init__(self, services: Dict[str, AsyncServiceNode]):
        super().__init__("image_to_video")
        self.services = services
        # 加载工作流配置
        self.workflow_config = workflow_registry.workflows["image-to-video"]
        # 工作流实例在执行时创建
        self.workflow = None
        
        # 获取base callback URL从服务配置
        self.base_callback_url = get_service_url()
    
    def _get_callback_url(self, service_name: str) -> str:
        """Get callback URL for a service"""
        return f"{self.base_callback_url}/webhook/{service_name}"
    
    def _create_scene_generation_step(self) -> ServiceStep:
        """创建场景生成步骤"""
        step = ServiceStep(
            "scene_generation",
            self.services["qwen_vl"],
            input_mapping={
                "image_url": "input_image_url",
                "prompt": "prompt",
                "system_prompt": "system_prompt"
            },
            output_mapping={
                "scenes": "enhanced_prompt"
            }
        )
        
        # 添加日志记录
        original_execute = step.execute
        async def execute_with_logging(context: Dict[str, Any]) -> Dict[str, Any]:
            self._log_request(context["job_id"], "scene_generation", {
                "input": {k: context.get(v) for k, v in step.input_mapping.items()}
            })
            result = await original_execute(context)
            self._log_response(context["job_id"], "scene_generation", result)
            return result
            
        step.execute = execute_with_logging
        return step
    
    def _create_image_editing_steps(self, scene_count: int) -> List[ServiceStep]:
        """根据场景数量创建图片编辑步骤"""
        steps = []
        for i in range(scene_count):
            step = ServiceStep(
                f"image_edit_{i}",
                self.services["qwen_edit"],
                input_mapping={
                    "image_url": "input_image_url",
                    "prompt": f"scenes[{i}]",
                    "width": "width",
                    "height": "height"
                },
                output_mapping={
                    f"edited_image_{i}": "output_url"
                },
                callback_url=self._get_callback_url("qwen-edit")
            )
            
            # 添加日志记录
            original_execute = step.execute
            step_name = f"image_edit_{i}"
            async def execute_with_logging(context: Dict[str, Any], name=step_name) -> Dict[str, Any]:
                self._log_request(context["job_id"], name, {
                    "input": {k: context.get(v) for k, v in step.input_mapping.items()}
                })
                result = await original_execute(context)
                self._log_response(context["job_id"], name, result)
                return result
                
            step.execute = execute_with_logging
            steps.append(step)
        return steps
    
    def _create_video_generation_steps(self, scene_count: int) -> List[ServiceStep]:
        """根据场景数量创建视频生成步骤"""
        steps = []
        for i in range(scene_count):
            step = ServiceStep(
                f"video_generation_{i}",
                self.services["wan_i2v"],
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
                callback_url=self._get_callback_url("wan-i2v")
            )
            
            # 添加日志记录
            original_execute = step.execute
            step_name = f"video_generation_{i}"
            async def execute_with_logging(context: Dict[str, Any], name=step_name) -> Dict[str, Any]:
                self._log_request(context["job_id"], name, {
                    "input": {k: context.get(v) for k, v in step.input_mapping.items()}
                })
                result = await original_execute(context)
                self._log_response(context["job_id"], name, result)
                return result
                
            step.execute = execute_with_logging
            steps.append(step)
        return steps
    
    def _build_workflow(self, scene_count: int) -> Workflow:
        """根据运行时参数构建工作流"""
        builder = WorkflowBuilder("image_to_video")
        
        # 添加场景生成步骤
        builder.add_service(self._create_scene_generation_step())
        
        # 添加并行的图片编辑步骤
        builder.add_parallel(
            "image_editing",
            self._create_image_editing_steps(scene_count)
        )
        
        # 添加并行的视频生成步骤
        builder.add_parallel(
            "video_generation",
            self._create_video_generation_steps(scene_count)
        )
        
        # 添加视频拼接步骤
        concat_step = ServiceStep(
            "video_concatenation",
            self.services["video_concat"],
            input_mapping={
                "video_urls": [f"video_{i}" for i in range(scene_count)],
                "crf": "crf"
            },
            output_mapping={
                "final_video": "output_url"
            },
            callback_url=self._get_callback_url("concat-upscale")
        )
        
        # 添加日志记录
        original_execute = concat_step.execute
        async def execute_with_logging(context: Dict[str, Any]) -> Dict[str, Any]:
            self._log_request(context["job_id"], "video_concatenation", {
                "input": {k: context.get(v) for k, v in concat_step.input_mapping.items()}
            })
            result = await original_execute(context)
            self._log_response(context["job_id"], "video_concatenation", result)
            return result
            
        concat_step.execute = execute_with_logging
        builder.add_service(concat_step)
        
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
    
    async def execute(self, job_id: str, input_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        # 准备初始上下文
        context = {
            "job_id": job_id,
            "input_image_url": input_data[0]["url"],
            "prompt": options.get("prompt", ""),
            "system_prompt": options.get("system_prompt", ""),
            "width": options.get("width", 768),
            "height": options.get("height", 768),
            "duration": options.get("duration", 5),
            "crf": options.get("crf", None)
        }
        
        # 记录工作流开始和输入参数
        self._log_request(job_id, "workflow_start", {
            "input_data": input_data,
            "options": options,
            "context": context
        })
        
        # 根据输入参数确定场景数量
        scene_count = options.get("scene_count", 3)
        
        # 在执行时构建工作流
        self.workflow = self._build_workflow(scene_count)
        
        # 执行工作流并保存任务引用以支持取消
        self._task = self.workflow.execute(context)
        result = await self._task
        self._task = None
        
        # 记录工作流结果
        self._log_response(job_id, "workflow_complete", result)
        
        # 返回结果
        return {
            "status": "completed",
            "output_url": result.get("final_video"),
            "intermediate_results": {
                "scenes": self._extract_scenes(result["scenes"]),
                "edited_images": [
                    result.get(f"edited_image_{i}") for i in range(scene_count)
                ],
                "videos": [
                    result.get(f"video_{i}") for i in range(scene_count)
                ]
            }
        }
