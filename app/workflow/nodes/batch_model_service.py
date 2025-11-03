from typing import Dict, Any, Optional
from app.workflow.node_control import IterativeNode
from app.workflow.nodes.model_service import ModelServiceNode
from app.workflow.nodes.model_request import ModelRequestNode
from app.utils.logger import logger
from app.core.api_url_config import api_url_config

class BatchModelServiceNode(IterativeNode):
    """批量处理模型服务请求的节点
    
    这个节点可以批量处理多个请求，并调用模型服务。
    支持并行处理和错误恢复。
    
    工作流程：
    1. 接收模型名称和一系列请求数据
    2. 对每个请求创建一个 ModelServiceNode 实例
    3. 并行处理所有请求
    4. 合并所有结果
    """
    
    category = "digen_services"
    
    def __init__(self, node_id: Optional[str] = None):
        super().__init__(node_id)
        
        # 基本配置 - 只显示comfy分组的模型选项
        model_options = api_url_config.get_group_model_names("comfy")
        self.add_input_port("model", "string", True, options=model_options)  # 模型名称
        self.add_input_port("timeout", "number", False)  # 超时时间（秒）
        
        # 输出端口
        self.add_output_port("local_urls", "array")  # 本地URL列表
        self.add_output_port("wasabi_urls", "array")  # Wasabi URL列表
        self.add_output_port("aws_urls", "array")  # AWS URL列表
        self.add_output_port("metadata", "array")  # 每个结果的元数据
    
    async def process_item(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个请求
        
        Args:
            request_data: 包含输入和选项的请求数据
            
        Returns:
            包含处理结果的字典
        """
        logger.info(f"Processing request with options: {request_data.get('options', {})}")
        
        # 创建模型服务节点
        model_node = ModelServiceNode()
        
        # 设置输入值
        model_node.input_values = {
            "model": self.input_values["model"],
            "request": request_data,  # 直接使用请求数据
            "timeout": self.input_values.get("timeout")  # 超时时间（可选）
        }
        
        # 处理并返回结果
        try:
            result = await model_node.process()
            return {
                "request": request_data,  # 保存原始请求以便追踪
                "local_urls": result.get("local_urls", []),
                "wasabi_urls": result.get("wasabi_urls", []),
                "aws_urls": result.get("aws_urls", []),
                "metadata": result.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise
    
    async def process(self) -> Dict[str, Any]:
        """处理所有输入并整理结果
        
        Returns:
            包含所有处理结果的字典
        """
        # 调用父类的处理方法
        result = await super().process()
        
        # 整理输出格式
        successful_results = result["results"]
        
        # 收集所有URL和元数据
        all_local_urls = []
        all_wasabi_urls = []
        all_aws_urls = []
        all_metadata = []
        
        for r in successful_results:
            all_local_urls.extend(r.get("local_urls", []))
            all_wasabi_urls.extend(r.get("wasabi_urls", []))
            all_aws_urls.extend(r.get("aws_urls", []))
            all_metadata.append({
                "metadata": r.get("metadata", {})
            })
        
        return {
            "results": successful_results,
            "success_count": result["success_count"],
            "error_count": result["error_count"],
            "errors": result["errors"],
            "local_urls": all_local_urls,
            "wasabi_urls": all_wasabi_urls,
            "aws_urls": all_aws_urls,
            "metadata": all_metadata
        }