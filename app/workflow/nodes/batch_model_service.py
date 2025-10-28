from typing import Dict, Any, Optional
from app.workflow.nodes.iterative import IterativeNode
from app.workflow.nodes.model_service import ModelServiceNode
from app.utils.logger import logger

class BatchModelServiceNode(IterativeNode):
    """批量处理模型服务请求的节点
    
    这个节点可以批量处理多个输入，并调用模型服务。
    支持并行处理和错误恢复。
    """
    
    def __init__(self, node_id: Optional[str] = None):
        super().__init__(node_id)
        
        # 添加模型服务相关的输入端口
        self.add_input_port("model", "string", True)  # 模型名称
        self.add_input_port("api_url", "string", True)  # API 端点
        self.add_input_port("callback_url", "string", True)  # 回调 URL
        
        # 可选的模型参数
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        self.add_input_port("negative_prompt", "string", False, "")
        self.add_input_port("extra_options", "object", False, {})
        
        # 修改输出端口以包含更多信息
        self.add_output_port("local_urls", "array")  # 本地URL列表
        self.add_output_port("wasabi_urls", "array")  # Wasabi URL列表
        self.add_output_port("aws_urls", "array")  # AWS URL列表
        self.add_output_port("metadata", "array")  # 每个结果的元数据
    
    async def process_item(self, prompt: str) -> Dict[str, Any]:
        """处理单个 prompt
        
        Args:
            prompt: 输入的 prompt 字符串
            
        Returns:
            包含处理结果的字典
        """
        logger.info(f"Processing prompt: {prompt}")
        
        # 创建模型服务节点
        model_node = ModelServiceNode()
        
        # 设置输入值
        model_node.input_values = {
            "model": self.input_values["model"],
            "input": [],  # 空列表，因为我们使用 prompt
            "prompt": prompt,
            "api_url": self.input_values["api_url"],
            "callback_url": self.input_values["callback_url"],
            "width": self.input_values.get("width", 768),
            "height": self.input_values.get("height", 768),
            "negative_prompt": self.input_values.get("negative_prompt", ""),
            "extra_options": self.input_values.get("extra_options", {})
        }
        
        # 处理并返回结果
        try:
            result = await model_node.process()
            return {
                "prompt": prompt,
                "local_urls": result.get("local_urls", []),
                "wasabi_urls": result.get("wasabi_urls", []),
                "aws_urls": result.get("aws_urls", []),
                "metadata": result.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Error processing prompt '{prompt}': {str(e)}")
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
                "prompt": r.get("prompt"),
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