import os
import json
from typing import Dict, Any, List, Optional

from app.utils.logger import logger

# 全局变量
MODEL_CONFIGS: Dict[str, 'ModelConfig'] = {}
DEFAULT_MODEL_NAME = None  # 添加默认模型名称变量

class ModelConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.workflow_path = config_data["workflow_path"]
        self.parameter_mapping = config_data["parameter_mapping"]
        self.input_mapping = config_data["input_mapping"]
        self.output_mapping = config_data["output_mapping"]
        self.required_inputs = config_data.get("required_inputs", [])
        self.timeout_minutes = config_data.get("timeout_minutes", 20)  # 默认20分钟超时
        self.default_params = config_data.get("default_params", {})  # 默认参数配置

    def validate_inputs(self, inputs: List[Dict[str, str]]) -> bool:
        """验证输入是否满足模型要求"""
        input_types = set(input_item["type"] for input_item in inputs)
        return all(req_input in input_types for req_input in self.required_inputs)

    def get_workflow(self) -> Dict[str, Any]:
        """Load and return the workflow for this model"""
        with open(self.workflow_path, "r") as f:
            return json.load(f)

    def map_parameter(self, param_name: str, value: Any) -> List[Dict[str, Any]]:
        """Map a parameter to its node configurations
        
        Returns:
            List[Dict[str, Any]]: List of mappings, each containing:
                - node_id: The target node ID
                - input_key: The input key in the node
                - value: The value to set
        """
        if param_name in self.parameter_mapping:
            mapping = self.parameter_mapping[param_name]
            # If mapping is a list, it means one parameter maps to multiple targets
            if isinstance(mapping, list):
                return [
                    {
                        "node_id": m["node_id"],
                        "input_key": m["input_key"],
                        "value": value
                    }
                    for m in mapping
                ]
            # If mapping is a dict, convert to single-item list for consistency
            else:
                return [{
                    "node_id": mapping["node_id"],
                    "input_key": mapping["input_key"],
                    "value": value
                }]
        return []

    def map_input_file(self, input_type: str, job_id: str) -> List[Dict[str, Any]]:
        """Map an input file to its node configurations
        
        Returns:
            List[Dict[str, Any]]: List of mappings, each containing:
                - node_id: The target node ID
                - input_key: The input key in the node
        """
        if input_type in self.input_mapping:
            mapping = self.input_mapping[input_type]
            # If mapping is a list, it means one input maps to multiple targets
            if isinstance(mapping, list):
                return [
                    {
                        "node_id": m["node_id"],
                        "input_key": m["input_key"]
                    }
                    for m in mapping
                ]
            # If mapping is a dict, convert to single-item list for consistency
            else:
                return [{
                    "node_id": mapping["node_id"],
                    "input_key": mapping["input_key"]
                }]
        return []

    def get_output_config(self, output_type: str) -> Optional[Dict[str, Any]]:
        """Get output configuration for a given type"""
        return self.output_mapping.get(output_type)

    def get_default_param(self, param_name: str) -> Optional[Any]:
        """获取参数的默认值"""
        return self.default_params.get(param_name)

def load_model_configs(model_config_path: str):
    """Load all model configurations"""
    try:
        if not os.path.exists(model_config_path):
            logger.error(f"Configuration file not found: {model_config_path}")
            raise FileNotFoundError(f"Configuration file not found: {model_config_path}")
            
        with open(model_config_path, "r") as f:
            config_data = json.load(f)
            
            # 读取默认模型名称
            global DEFAULT_MODEL_NAME
            # 优先使用环境变量中的默认模型设置，如果没有则使用配置文件中的设置
            env_default_model = os.getenv('DEFAULT_MODEL')
            config_default_model = config_data.get("default_model")
            DEFAULT_MODEL_NAME = env_default_model or config_default_model
            
            # 记录默认模型的来源
            if env_default_model:
                logger.info(f"Using default model from environment variable: {DEFAULT_MODEL_NAME}")
            else:
                logger.info(f"Using default model from config file: {DEFAULT_MODEL_NAME}")
            
            # 加载模型配置
            models_config = config_data.get("models", {})
            for model_name, model_config in models_config.items():
                MODEL_CONFIGS[model_name] = ModelConfig(model_config)
        
        if DEFAULT_MODEL_NAME not in MODEL_CONFIGS:
            logger.error(f"Default model '{DEFAULT_MODEL_NAME}' not found in configurations")
            raise ValueError(f"Default model '{DEFAULT_MODEL_NAME}' not found in configurations")
            
        logger.info(f"Successfully loaded model configurations from {model_config_path}")
        logger.info(f"Available models: {list(MODEL_CONFIGS.keys())}")
        logger.info(f"Default model: {DEFAULT_MODEL_NAME}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse configuration file {model_config_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading model configurations: {str(e)}")
        raise

def get_model_config(model_name: str) -> ModelConfig:
    """
    获取模型配置，如果指定的模型不存在或参数不匹配，返回默认模型配置
    """
    if model_name in MODEL_CONFIGS:
        return MODEL_CONFIGS[model_name]
    
    if DEFAULT_MODEL_NAME is None:
        raise Exception("Default model not initialized. Please check configuration.")
    
    logger.warning(f"Model '{model_name}' not found, using default model '{DEFAULT_MODEL_NAME}'")
    return MODEL_CONFIGS[DEFAULT_MODEL_NAME]

def get_default_model_name() -> str:
    """
    安全地获取默认模型名称
    """
    if DEFAULT_MODEL_NAME is None:
        raise Exception("Default model not initialized. Please check configuration.")
    return DEFAULT_MODEL_NAME 