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
    
    用于构建和验证单一类型的输入数据。支持单个或批量输入:
    1. 单个输入: 提供单个URL (url)
    2. 批量输入: 提供URL列表 (urls)
    
    type参数指定输入类型: url和urls只能提供一个。
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
    
    用于合并两个ModelRequestInputNode的输出。
    每个输入端口接收一个input_list。
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        """
        Args:
            node_id: 节点ID
        """
        super().__init__(node_id)
        
        # 固定两个输入端口
        self.add_input_port("input_1", "array", True)
        self.add_input_port("input_2", "array", True)
        
        # 输出端口
        self.add_output_port("input_list", "array")
    
    async def process(self) -> Dict[str, Any]:
        """合并两个输入列表"""
        # 获取输入列表
        input_1 = self.input_values.get("input_1", [])
        input_2 = self.input_values.get("input_2", [])
        
        # 验证输入
        if not isinstance(input_1, list) or not isinstance(input_2, list):
            raise ValueError("输入必须是列表类型")
        
        # 合并列表
        combined_list = []
        combined_list.extend(input_1)
        combined_list.extend(input_2)
        
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

class BatchModelRequestInputNode(WorkflowNode):
    """批量模型请求输入节点
    
    将输入的URL列表转换为标准格式的input_list。
    每个URL会生成一个input_list中的一项。
    
    输入:
    - urls: URL列表
    - type: 输入类型 (image/audio/video)
    
    输出:
    - input_list: 包含所有输入项的列表
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("urls", "array", True)  # URL列表
        self.add_input_port("type", "string", True)  # 输入类型
        
        # 输出端口
        self.add_output_port("input_list", "array")
    
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
        """处理输入并生成input_list"""
        # 验证输入类型
        input_type = self.input_values["type"]
        if not self._validate_input_type(input_type):
            raise ValueError(f"输入类型必须是以下之一: {[t.value for t in InputType]}")
        
        # 获取URLs
        urls = self.input_values["urls"]
        
        # 验证URLs
        if not isinstance(urls, list):
            raise ValueError("urls必须是列表类型")
        if not urls:
            raise ValueError("urls不能为空列表")
        
        # 验证所有URL
        for url in urls:
            self._validate_url(url)
        
        # 生成input_list，每个URL生成一个独立的子列表
        input_list = [[{"type": input_type, "url": url}] for url in urls]
        
        return {"input_list": input_list}

class ConcatBatchModelRequestInputNode(WorkflowNode):
    """批量模型请求输入合并节点
    
    用于合并两个BatchModelRequestInputNode的输出。
    要求两个输入列表的长度必须相同。
    
    输入:
    - input_list_1: 第一个输入列表 (来自BatchModelRequestInputNode)
    - input_list_2: 第二个输入列表 (来自BatchModelRequestInputNode)
    
    输出:
    - input_list: 合并后的列表，每个子列表包含两个输入的对应项
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("input_list_1", "array", True)  # 第一个输入列表
        self.add_input_port("input_list_2", "array", True)  # 第二个输入列表
        
        # 输出端口
        self.add_output_port("input_list", "array")
    
    async def process(self) -> Dict[str, Any]:
        """合并两个输入列表"""
        # 获取输入列表
        input_list_1 = self.input_values["input_list_1"]
        input_list_2 = self.input_values["input_list_2"]
        
        # 验证输入类型
        if not isinstance(input_list_1, list) or not isinstance(input_list_2, list):
            raise ValueError("输入必须是列表类型")
        
        # 验证列表长度
        if len(input_list_1) != len(input_list_2):
            raise ValueError("两个输入列表的长度必须相同")
        
        if not input_list_1 or not input_list_2:
            raise ValueError("输入列表不能为空")
        
        # 验证每个元素都是列表
        for items_1, items_2 in zip(input_list_1, input_list_2):
            if not isinstance(items_1, list) or not isinstance(items_2, list):
                raise ValueError("输入列表的每个元素必须是列表")
        
        # 合并列表
        merged_list = []
        for items_1, items_2 in zip(input_list_1, input_list_2):
            merged_items = items_1 + items_2
            merged_list.append(merged_items)
        
        return {"input_list": merged_list}

class BatchModelRequestOptionNode(WorkflowNode):
    """批量模型请求选项节点
    
    用于处理批量的提示词输入，生成多个选项配置。
    prompts、audio_prompts、negative_prompts可以是列表或空，但如果提供了多个，它们的长度必须相同。
    其他参数保持单一值。
    
    输入:
    - prompts: 提示词列表 (可选)
    - audio_prompts: 音频提示词列表 (可选)
    - negative_prompts: 负面提示词列表 (可选)
    - width: 图像宽度
    - height: 图像高度
    - batch_size: 批处理大小
    - seed: 随机种子 (可选)
    - output_format: 输出格式 (可选)
    - extra_options: 扩展选项 (可选)
    
    输出:
    - options: 选项配置列表
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 批量提示词输入
        self.add_input_port("prompts", "array", False, [])  # 提示词列表
        self.add_input_port("audio_prompts", "array", False, [])  # 音频提示词列表
        self.add_input_port("negative_prompts", "array", False, [])  # 负面提示词列表
        
        # 基础选项
        self.add_input_port("width", "number", False, 768)
        self.add_input_port("height", "number", False, 768)
        
        # 高级选项
        self.add_input_port("batch_size", "number", False, 1)
        self.add_input_port("seed", "number", False, None)
        self.add_input_port("output_format", "string", False, None)
        
        # 扩展选项
        self.add_input_port("extra_options", "object", False, {})
        
        # 输出
        self.add_output_port("options", "array")
    
    def _validate_prompt_lists(self, prompts: List[str], audio_prompts: List[str], negative_prompts: List[str]) -> int:
        """验证提示词列表
        
        检查所有非空列表的长度是否一致，并返回列表长度。
        如果所有列表都为空，返回1（生成单个选项）。
        """
        lengths = []
        
        # 收集所有非空列表的长度
        if prompts:
            if not isinstance(prompts, list):
                raise ValueError("prompts必须是列表类型")
            lengths.append(len(prompts))
            
        if audio_prompts:
            if not isinstance(audio_prompts, list):
                raise ValueError("audio_prompts必须是列表类型")
            lengths.append(len(audio_prompts))
            
        if negative_prompts:
            if not isinstance(negative_prompts, list):
                raise ValueError("negative_prompts必须是列表类型")
            lengths.append(len(negative_prompts))
        
        # 如果没有任何列表，返回1
        if not lengths:
            return 1
        
        # 检查所有列表长度是否一致
        if len(set(lengths)) > 1:
            raise ValueError("所有提供的提示词列表长度必须相同")
        
        return lengths[0]
    
    async def process(self) -> Dict[str, Any]:
        """处理输入并生成选项列表"""
        # 获取提示词列表
        prompts = self.input_values.get("prompts", [])
        audio_prompts = self.input_values.get("audio_prompts", [])
        negative_prompts = self.input_values.get("negative_prompts", [])
        
        # 验证列表并获取长度
        num_options = self._validate_prompt_lists(prompts, audio_prompts, negative_prompts)
        
        # 获取其他选项
        base_options = {
            "width": self.input_values.get("width", 768),
            "height": self.input_values.get("height", 768),
            "batch_size": self.input_values.get("batch_size", 1)
        }
        
        # 添加可选参数
        if self.input_values.get("seed") is not None:
            base_options["seed"] = self.input_values["seed"]
            
        if self.input_values.get("output_format"):
            base_options["output_format"] = self.input_values["output_format"]
        
        # 获取扩展选项
        extra_options = self.input_values.get("extra_options", {})
        base_options.update(extra_options)
        
        # 生成选项列表
        options_list = []
        for i in range(num_options):
            options = base_options.copy()
            
            # 添加对应位置的提示词
            if prompts:
                options["prompt"] = prompts[i]
            else:
                options["prompt"] = ""
                
            if audio_prompts:
                options["audio_prompt"] = audio_prompts[i]
            else:
                options["audio_prompt"] = ""
                
            if negative_prompts:
                options["negative_prompt"] = negative_prompts[i]
            else:
                options["negative_prompt"] = ""
            
            options_list.append(options)
        
        return {"options": options_list}

class BatchModelRequestNode(WorkflowNode):
    """批量模型请求节点
    
    整合批量输入数据和选项配置，生成多个完整的模型请求配置。
    要求input_list和options的长度必须相同。
    
    输入:
    - input_list: 输入列表，每个元素是一个子列表 (来自BatchModelRequestInputNode或ConcatBatchModelRequestInputNode)
    - options: 选项列表 (来自BatchModelRequestOptionNode)
    
    输出:
    - requests: 请求配置列表，每个元素包含对应的输入和选项
    """
    
    category = "model-request"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("input_list", "array", True)  # 输入列表
        self.add_input_port("options", "array", True)  # 选项列表
        
        # 输出端口
        self.add_output_port("requests", "array")
    
    async def process(self) -> Dict[str, Any]:
        """整合输入和选项生成请求列表"""
        # 获取输入
        input_list = self.input_values["input_list"]
        options = self.input_values["options"]
        
        # 验证输入类型
        if not isinstance(input_list, list) or not isinstance(options, list):
            raise ValueError("input_list和options必须是列表类型")
        
        # 验证列表长度
        if len(input_list) != len(options):
            raise ValueError("input_list和options的长度必须相同")
        
        if not input_list or not options:
            raise ValueError("input_list和options不能为空")
        
        # 生成请求列表
        requests = []
        for inputs, opts in zip(input_list, options):
            request = {
                "input": inputs,
                "options": opts
            }
            requests.append(request)
        
        return {"requests": requests}

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