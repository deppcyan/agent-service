from typing import Dict, Any, List, Union, Optional
from enum import Enum
from app.workflow.base import WorkflowNode
from app.utils.logger import logger

class InputType(str, Enum):
    """支持的输入类型"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class ModelRequestInputNode(WorkflowNode):
    """模型请求输入节点
    
    用于构建和验证单一类型的输入数据。支持单个或批量输入：
    1. 单个输入：提供单个URL (url)
    2. 批量输入：提供URL列表 (urls)
    
    type参数指定输入类型，url和urls只能提供一个。
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("url", "string", False)  # 单个URL
        self.add_input_port("urls", "array", False)  # URL列表
        self.add_input_port("type", "string", True)  # 输入类型
        
        # 输出端口
        self.add_output_port("input_list", "array")  # 处理后的输入列表
        
    def _validate_input_type(self, input_type: str) -> bool:
        """验证输入类型是否支持"""
        try:
            InputType(input_type)
            return True
        except ValueError:
            return False
    
    def _validate_url(self, url: str) -> None:
        """验证URL格式"""
        if not isinstance(url, str):
            raise ValueError("URL必须是字符串类型")
        if not url:
            raise ValueError("URL不能为空")
    
    async def process(self) -> Dict[str, Any]:
        """处理输入并生成标准格式的输入列表"""
        # 验证输入类型
        input_type = self.input_values["type"]
        if not self._validate_input_type(input_type):
            raise ValueError(f"输入类型必须是以下之一: {[t.value for t in InputType]}")
        
        # 检查输入方式
        url = self.input_values.get("url")
        urls = self.input_values.get("urls")
        
        # 确保只使用一种输入方式
        if url and urls:
            raise ValueError("url和urls不能同时提供")
        if not url and not urls:
            raise ValueError("必须提供url或urls之一")
        
        # 处理输入
        if url:
            # 单个输入
            self._validate_url(url)
            input_list = [{"type": input_type, "url": url}]
        else:
            # 批量输入
            if not isinstance(urls, list):
                raise ValueError("urls必须是列表类型")
            if not urls:
                raise ValueError("urls不能为空列表")
            
            # 验证所有URL
            for url in urls:
                self._validate_url(url)
            
            input_list = [{"type": input_type, "url": url} for url in urls]
        
        return {"input_list": input_list}

class ConcatModelRequestInputNode(WorkflowNode):
    """模型请求输入合并节点
    
    用于合并多个ModelRequestInputNode的输出。
    支持动态添加输入端口，每个输入端口接收一个input_list。
    """
    
    category = "model-request"
    
    def __init__(self, num_inputs: int = 2, node_id: str = None):
        """
        Args:
            num_inputs: 输入端口数量，默认为2
            node_id: 节点ID
        """
        super().__init__(node_id)
        
        # 创建指定数量的输入端口
        for i in range(num_inputs):
            self.add_input_port(f"input_{i}", "array", True)
        
        # 输出端口
        self.add_output_port("input_list", "array")
    
    async def process(self) -> Dict[str, Any]:
        """合并所有输入列表"""
        # 收集所有输入列表
        combined_list = []
        for key, value in self.input_values.items():
            if key.startswith("input_") and isinstance(value, list):
                combined_list.extend(value)
        
        if not combined_list:
            raise ValueError("没有有效的输入列表")
        
        return {"input_list": combined_list}

class ModelRequestOptionNode(WorkflowNode):
    """模型请求选项节点
    
    用于配置模型运行的各种参数选项，包括：
    1. 基础选项：提示词、图像尺寸等
    2. 高级选项：批处理大小、随机种子等
    3. 扩展选项：模型特定的额外参数
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 基础选项
        self.add_input_port("prompt", "string", False, "")
        self.add_input_port("audio_prompt", "string", False, "")
        self.add_input_port("negative_prompt", "string", False, "")
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        
        # 高级选项
        self.add_input_port("batch_size", "number", False, 1)
        self.add_input_port("seed", "number", False, None)
        self.add_input_port("output_format", "string", False, None)
        
        # 扩展选项
        self.add_input_port("extra_options", "object", False, {})
        
        # 输出
        self.add_output_port("options", "object")
    
    async def process(self) -> Dict[str, Any]:
        """处理并合并所有选项"""
        # 收集基础选项
        options = {
            "prompt": self.input_values.get("prompt", ""),
            "audio_prompt": self.input_values.get("audio_prompt", ""),
            "negative_prompt": self.input_values.get("negative_prompt", ""),
            "width": self.input_values.get("width", 768),
            "height": self.input_values.get("height", 768),
            "batch_size": self.input_values.get("batch_size", 1)
        }
        
        # 添加可选参数
        if self.input_values.get("seed") is not None:
            options["seed"] = self.input_values["seed"]
            
        if self.input_values.get("output_format"):
            options["output_format"] = self.input_values["output_format"]
        
        # 合并扩展选项
        extra_options = self.input_values.get("extra_options", {})
        options.update(extra_options)
        
        return {"options": options}

class ModelRequestNode(WorkflowNode):
    """模型请求节点
    
    整合输入数据和选项配置，生成完整的模型请求配置。
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 必需输入
        self.add_input_port("input_list", "array", True)  # 来自 ModelRequestInputNode 或 ConcatModelRequestInputNode
        self.add_input_port("options", "object", True)  # 来自 ModelRequestOptionNode
        
        # 输出
        self.add_output_port("request", "object")  # 完整的请求数据
    
    async def process(self) -> Dict[str, Any]:
        """整合输入和选项生成请求数据"""
        request = {
            "input": self.input_values["input_list"],
            "options": self.input_values["options"]
        }
        
        return {"request": request}