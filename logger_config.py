import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Get RUNPOD_POD_ID from environment variables
runpod_id = os.getenv('RUNPOD_POD_ID')
if runpod_id:
    pod_id = runpod_id
    gpu_vendor = 'runpod'
    novita_region = os.getenv('NOVITA_REGION')
elif os.getenv('NOVITA_REGION'):
    pod_id = os.getenv('HOSTNAME', 'no_pod')
    gpu_vendor = 'novita'
    novita_region = os.getenv('NOVITA_REGION')
else:
    pod_id = 'no_pod'
    gpu_vendor = 'local'
    novita_region = os.getenv('NOVITA_REGION')

# 获取服务名称，默认为 wan2video
service_name = os.getenv('DIGEN_SERVICE_NAME', 'agent')

# Ensure the log directory exists
os.makedirs('log', exist_ok=True)

# Global flag to track if logger is already configured
_logger_configured = False

class JobIdFilter(logging.Filter):
    """自定义日志过滤器,添加job_id和pod_id字段"""
    def filter(self, record):
        if not hasattr(record, 'job_id'):
            record.job_id = 'no_job'
        if not hasattr(record, 'pod_id'):
            record.pod_id = pod_id
        return True

def setup_logger(name: str = "agent") -> logging.Logger:
    """
    设置日志配置
    
    Args:
        name: 日志器名称，默认为"wan2video"
    
    Returns:
        logging.Logger: 配置好的日志器
    """
    global _logger_configured
    
    # Get the logger
    logger = logging.getLogger(name)
    
    # If logger is already configured, return it
    if _logger_configured:
        return logger
    
    # Configure logging with custom formatter that includes job_id
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Prevent propagation to root logger to avoid duplicate output
    logger.propagate = False
    
    logger.addFilter(JobIdFilter())

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler with rotation, using the 'log' directory
    file_handler = RotatingFileHandler("log/app.log", maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(pod_id)s][%(job_id)s] - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Mark as configured
    _logger_configured = True
    
    return logger

# 创建默认日志器实例
logger = setup_logger(service_name) 