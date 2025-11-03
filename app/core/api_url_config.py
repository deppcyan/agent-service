import os
import json
from typing import Dict, Optional
from app.utils.logger import logger

class APIURLConfig:
    """API URL配置管理类
    
    从api_url.json配置文件中读取不同环境的API URL映射，
    根据环境变量ENVIRONMENT确定当前环境。
    """
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(APIURLConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if self._config_data is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config", "api_url.json"
            )
            
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            
            logger.info(f"API URL配置已加载: {config_path}")
            
        except FileNotFoundError:
            logger.error(f"API URL配置文件未找到: {config_path}")
            self._config_data = {}
        except json.JSONDecodeError as e:
            logger.error(f"API URL配置文件格式错误: {e}")
            self._config_data = {}
        except Exception as e:
            logger.error(f"加载API URL配置时发生错误: {e}")
            self._config_data = {}
    
    def get_environment(self) -> str:
        """获取当前环境
        
        Returns:
            环境名称，默认为'prod'
        """
        env = os.getenv("DIGEN_SERVICE_ENV", "prod").lower()
        logger.debug(f"当前环境: {env}")
        return env
    
    def get_api_url(self, service_name: str) -> Optional[str]:
        """获取指定服务的API URL
        
        Args:
            service_name: 服务名称/模型名称
            
        Returns:
            API URL，如果未找到则返回None
        """
        env = self.get_environment()
        
        # 检查环境是否存在
        if env not in self._config_data:
            logger.warning(f"环境 '{env}' 在配置中不存在，可用环境: {list(self._config_data.keys())}")
            return None
        
        env_config = self._config_data[env]
        
        # 在所有分组中查找服务
        for group_name, group_services in env_config.items():
            if service_name in group_services:
                api_url = group_services[service_name]
                logger.debug(f"获取API URL: {service_name} -> {api_url} (环境: {env}, 分组: {group_name})")
                return api_url
        
        # 收集所有可用服务用于错误提示
        all_services = []
        for group_services in env_config.values():
            all_services.extend(group_services.keys())
        
        logger.warning(f"服务 '{service_name}' 在环境 '{env}' 中不存在，可用服务: {all_services}")
        return None
    
    def get_all_services(self, environment: Optional[str] = None) -> Dict[str, str]:
        """获取指定环境的所有服务配置
        
        Args:
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            服务名称到API URL的映射字典
        """
        env = environment or self.get_environment()
        
        if env not in self._config_data:
            logger.warning(f"环境 '{env}' 在配置中不存在")
            return {}
        
        # 合并所有分组的服务
        all_services = {}
        for group_services in self._config_data[env].values():
            all_services.update(group_services)
        
        return all_services
    
    def get_available_environments(self) -> list:
        """获取所有可用环境
        
        Returns:
            环境名称列表
        """
        return list(self._config_data.keys())
    
    def get_available_services(self, environment: Optional[str] = None) -> list:
        """获取指定环境的所有可用服务
        
        Args:
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            服务名称列表
        """
        env = environment or self.get_environment()
        
        if env not in self._config_data:
            return []
        
        # 收集所有分组的服务名称
        all_services = []
        for group_services in self._config_data[env].values():
            all_services.extend(group_services.keys())
        
        return sorted(all_services)
    
    def get_all_model_names(self) -> list:
        """获取所有环境中的模型名称（去重）
        
        Returns:
            所有可用模型名称的列表
        """
        all_models = set()
        for env_config in self._config_data.values():
            for group_services in env_config.values():
                all_models.update(group_services.keys())
        return sorted(list(all_models))
    
    def get_group_model_names(self, group_name: str, environment: Optional[str] = None) -> list:
        """获取指定分组的模型名称
        
        Args:
            group_name: 分组名称（如 'comfy' 或 'vllm'）
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            指定分组的模型名称列表
        """
        env = environment or self.get_environment()
        
        if env not in self._config_data:
            logger.warning(f"环境 '{env}' 在配置中不存在")
            return []
        
        env_config = self._config_data[env]
        if group_name not in env_config:
            logger.warning(f"分组 '{group_name}' 在环境 '{env}' 中不存在，可用分组: {list(env_config.keys())}")
            return []
        
        return sorted(list(env_config[group_name].keys()))
    
    def get_available_groups(self, environment: Optional[str] = None) -> list:
        """获取指定环境的所有可用分组
        
        Args:
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            分组名称列表
        """
        env = environment or self.get_environment()
        
        if env not in self._config_data:
            return []
        
        return list(self._config_data[env].keys())
    
    def reload_config(self):
        """重新加载配置文件"""
        logger.info("重新加载API URL配置")
        self._config_data = None
        self._load_config()

# 创建全局实例
api_url_config = APIURLConfig()
