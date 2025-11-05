import random
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.core.model_config import ModelConfig
from app.utils.logger import logger

class BasePreprocessor(ABC):
    """统一的参数预处理基类"""
    
    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config
    
    async def preprocess_options(self, options: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """统一的选项参数预处理"""
        processed_options = options.copy()
        
        # 应用所有默认参数
        for param_name, default_value in self.model_config.default_params.items():
            if param_name not in processed_options or processed_options[param_name] is None:
                processed_options[param_name] = default_value
        
        # 处理seed参数
        if processed_options.get('seed') is None:
            processed_options['seed'] = random.randint(0, 2**32 - 1)
        logger.info(f"Using seed: {processed_options['seed']}", extra={"job_id": job_id})
        
        return processed_options
    
    async def preprocess_inputs(self, options: Dict[str, Any], job_id: str, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """统一的输入预处理
        
        将输入列表转换为映射，处理重复的type:
        - 如果某个type只出现一次，保持原样 (如 "mask": "url1")
        - 如果某个type出现多次，添加编号 (如 "image1": "url1", "image2": "url2")
        """
        processed_data = {}
        type_counts = {}  # 用于跟踪每个type出现的次数
        
        # 第一遍遍历，统计每个type的出现次数
        for input_item in inputs:
            input_type = input_item.get('type')
            if input_type:
                type_counts[input_type] = type_counts.get(input_type, 0) + 1
        
        # 第二遍遍历，根据出现次数处理key
        type_indices = {}  # 用于跟踪每个type当前处理到第几个
        for input_item in inputs:
            input_type = input_item.get('type')
            url = input_item.get('url')
            if input_type and url:
                if type_counts[input_type] > 1:
                    # 如果有多个相同type，添加编号
                    type_indices[input_type] = type_indices.get(input_type, 0) + 1
                    key = f"{input_type}{type_indices[input_type]}"
                else:
                    # 如果只有一个，保持原样
                    key = input_type
                processed_data[key] = url
        
        return processed_data
    
    async def preprocess_workflow(self, workflow: Dict[str, Any], options: Dict[str, Any], inputs: Dict[str, str], job_id: str) -> Dict[str, Any]:
        """统一的工作流预处理"""
        processed_workflow = workflow.copy()
        
        # 确保workflow有nodes结构
        if "nodes" not in processed_workflow:
            processed_workflow["nodes"] = {}
            
        # 处理所有输入URL
        for input_type, url in inputs.items():
            # 获取映射列表
            mappings = self.model_config.map_input_file(input_type, job_id)
            if not isinstance(mappings, list):
                mappings = [mappings] if mappings else []
                
            # 应用每个映射
            for mapping in mappings:
                if mapping:
                    node_id = mapping["node_id"]
                    if node_id not in processed_workflow["nodes"]:
                        processed_workflow["nodes"][node_id] = {"inputs": {}}
                    elif "inputs" not in processed_workflow["nodes"][node_id]:
                        processed_workflow["nodes"][node_id]["inputs"] = {}
                    processed_workflow["nodes"][node_id]["inputs"][mapping["input_key"]] = url
        
        # 设置所有参数
        for param_name, value in options.items():
            if value is not None:
                param_mappings = self.model_config.map_parameter(param_name, value)
                for mapping in param_mappings:
                    node_id = mapping["node_id"]
                    if node_id not in processed_workflow["nodes"]:
                        processed_workflow["nodes"][node_id] = {"inputs": {}}
                    elif "inputs" not in processed_workflow["nodes"][node_id]:
                        processed_workflow["nodes"][node_id]["inputs"] = {}
                    processed_workflow["nodes"][node_id]["inputs"][mapping["input_key"]] = mapping["value"]
        
        return processed_workflow

# 模型名称到预处理器的映射
MODEL_PREPROCESSOR_MAP = {
    
}

def get_preprocessor(model_name: str, model_config: ModelConfig) -> BasePreprocessor:
    """
    根据模型名称获取对应的预处理器
    
    Args:
        model_name: 模型名称
        model_config: 模型配置
    
    Returns:
        BasePreprocessor: 对应的预处理器实例
    """
    preprocessor_class = MODEL_PREPROCESSOR_MAP.get(model_name, BasePreprocessor)
    return preprocessor_class(model_config)

async def preprocess_job(job: Dict[str, Any], model_config: ModelConfig, job_id: str) -> Dict[str, Any]:
    """
    预处理任务参数
    
    Args:
        job: 任务信息
        model_config: 模型配置
        job_id: 任务ID
    
    Returns:
        Dict[str, Any]: 预处理后的工作流
    """
    # 获取模型名称
    model_name = job.get('model', 'image-to-video')
    
    # 获取对应的预处理器
    preprocessor = get_preprocessor(model_name, model_config)
    
    # 预处理选项参数
    options = job.get('options', {}).copy()
    processed_options = await preprocessor.preprocess_options(options, job_id)
    
    # 获取输入
    inputs = job.get('input', {})
    
    # 预处理输入，将输入列表转换为映射
    processed_inputs = await preprocessor.preprocess_inputs(processed_options, job_id, inputs)
    
    # 更新options
    #processed_options.update(processed_inputs)
    
    # 获取工作流
    workflow = model_config.get_workflow()
    
    # 预处理工作流，使用处理后的inputs映射
    processed_workflow = await preprocessor.preprocess_workflow(workflow, processed_options, processed_inputs, job_id)
    
    return {
        'workflow': processed_workflow,
        'options': processed_options
    } 