from typing import Dict, Any, List
from app.workflow.node_api import AsyncDigenAPINode
from app.utils.logger import logger

class ModelServiceNode(AsyncDigenAPINode):
    """模型服务节点
    
    处理与模型服务的API通信。期望从ModelRequestNode接收完整的配置。
    
    工作流程：
    1. ModelRequestInputNode: 处理和验证输入数据
    2. ModelRequestOptionNode: 配置模型运行选项
    3. ModelRequestNode: 整合输入和选项
    4. ModelServiceNode: 执行API调用并返回结果
    """
    
    def __init__(self, node_id: str = None):
        super().__init__("model-service", node_id)
        
        # 输入端口
        self.add_input_port("model", "string", True)  # 模型名称/标识符
        self.add_input_port("request", "object", True)  # 请求数据
        
        # Output ports
        self.add_output_port("local_urls", "array")  # List of local output URLs
        self.add_output_port("wasabi_urls", "array")  # List of Wasabi output URLs
        self.add_output_port("aws_urls", "array")  # List of AWS output URLs
        self.add_output_port("options", "object")  # Options used for generation
        self.add_output_port("status", "string")  # Status of the request
        self.add_output_port("metadata", "object")  # Additional metadata from the model
    
    def _prepare_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备模型服务请求数据"""
        model = input_data["model"]
        request_data = input_data["request"]
        
        # 构建完整请求
        request = {
            "model": model,
            "input": request_data["input"],
            "options": request_data["options"],
            "webhookUrl": self.get_callback_url()
        }
        
        logger.debug(f"准备发送请求到模型 {model}: {request}")
        return request
    
    async def _handle_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle model service callback"""
        status = callback_data.get("status")
        
        if status == "completed":
            # Get all output URLs
            return {
                "status": "completed",
                "local_urls": callback_data.get("local_outputs", []),
                "wasabi_urls": callback_data.get("wasabi_outputs", []),
                "aws_urls": callback_data.get("outputs", []),
                "options": callback_data.get("options", {}),
                "metadata": callback_data.get("metadata", {})
            }
        elif status == "failed":
            error_msg = callback_data.get("error", "Unknown error")
            logger.error(f"Model service failed: {error_msg}")
            raise Exception(error_msg)
        else:
            raise Exception(f"Unexpected status: {status}")
