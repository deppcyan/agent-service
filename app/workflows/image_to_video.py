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
        # 获取步骤配置
        self.steps_config = {step["name"]: step.get("config", {}) for step in self.workflow_config.steps}
        # 工作流实例在执行时创建
        self.workflow = None
        
        # 获取base callback URL从服务配置
        self.base_callback_url = get_service_url()
    
    def _get_callback_url(self, service_name: str) -> str:
        """Get callback URL for a service"""
        return f"{self.base_callback_url}/webhook/{service_name}"
    
    def _create_scene_extraction_step(self) -> ServiceStep:
        """创建分镜提取步骤"""
        step = ServiceStep(
            "scene_extraction",
            None,  # 这是一个内部处理步骤，不需要外部服务
            input_mapping={
                "text": "raw_scenes"
            },
            output_mapping={
                "scenes": "scenes"
            }
        )
        
        # 添加处理逻辑
        async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
            text = context.get("text", "")
            max_scenes = self.steps_config["image_editing"].get("max_scenes", 3)
            scenes = []
            result = {"scenes": []}
            
            for line in text.split("\n"):
                if line.startswith("Next Scene:"):
                    scene = line.replace("Next Scene:", "").strip()
                    scenes.append(scene)
                    if len(scenes) >= max_scenes:
                        break
            
            # 将场景列表添加到结果中
            result["scenes"] = scenes
            
            # 为每个场景创建单独的上下文变量
            for i, scene in enumerate(scenes):
                result[f"scenes[{i}]"] = scene
                
            return result
            
        step.execute = execute
        return step

    def _create_scene_generation_step(self) -> ServiceStep:
        """创建场景生成步骤"""
        config = self.steps_config["scene_generation"]
        step = ServiceStep(
            "scene_generation",
            self.services["qwen_vl"],
            input_mapping={
                "image_url": "input_image_url",
                "prompt": "prompt",
                "system_prompt": "system_prompt"
            },
            output_mapping={
                "raw_scenes": "enhanced_prompt"  # 改为raw_scenes，后续会处理
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
        
        # 添加分镜提取步骤
        builder.add_service(self._create_scene_extraction_step())
        
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
    
    async def execute(self, job_id: str, input_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        # 准备初始上下文
        # 从配置中获取默认值
        scene_gen_config = self.steps_config["scene_generation"]
        
        context = {
            "job_id": job_id,
            "input_image_url": input_data[0]["url"],
            "prompt": options.get("prompt", ""),
            "system_prompt": scene_gen_config.get("system_prompt", ""),
            "width": options.get("width", 768),
            "height": options.get("height", 768),
            "duration": options.get("duration", 5),
            "crf": options.get("crf", None),
            "seed": options.get("seed", None),
        }
        
        # 记录工作流开始和输入参数
        self._log_request(job_id, "workflow_start", {
            "input_data": input_data,
            "options": options,
            "context": context
        })
        
        # 根据配置文件确定场景数量
        scene_count = self.steps_config["image_editing"].get("max_scenes", 3)
        
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
                "scenes": result.get("scenes", []),
                "edited_images": [
                    result.get(f"edited_image_{i}") for i in range(scene_count)
                ],
                "videos": [
                    result.get(f"video_{i}") for i in range(scene_count)
                ]
            }
        }
