import os
import yaml
from typing import Dict, Any, Optional
from pydantic import BaseModel
from functools import lru_cache

class ServiceConfig(BaseModel):
    url: str
    api_key: str
    rate_limit: Dict[str, float]
    max_concurrent: int

class Config:
    """Configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.services: Dict[str, ServiceConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load all configuration files"""
        self._load_services_config()
    
    def _load_services_config(self):
        """Load services configuration"""
        services_file = os.path.join(self.config_dir, "services.yaml")
        with open(services_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Process services
        for service_name, service_config in config['services'].items():
            # Replace environment variables in URL and API key
            url = service_config['url']
            api_key = service_config['api_key']
            
            # Process URL
            if url.startswith('${') and url.endswith('}'):
                env_var = url[2:-1]
                url = os.getenv(env_var)
                if not url:
                    raise ValueError(f"Environment variable {env_var} not set")
            
            # Process API key
            if api_key.startswith('${') and api_key.endswith('}'):
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var)
                if not api_key:
                    raise ValueError(f"Environment variable {env_var} not set")
            
            # Create service config
            self.services[service_name] = ServiceConfig(
                url=url,
                api_key=api_key,
                rate_limit=service_config['rate_limit'],
                max_concurrent=service_config['max_concurrent']
            )
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL"""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        return self.services[service_name].url
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get full service configuration"""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        return self.services[service_name]
    
    def get_all_service_urls(self) -> Dict[str, str]:
        """Get all service URLs"""
        return {
            name: config.url
            for name, config in self.services.items()
        }

@lru_cache()
def get_config() -> Config:
    """Get configuration singleton"""
    return Config()

# Create global config instance
config = get_config()