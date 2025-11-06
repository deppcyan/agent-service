import logging
import os
from logging.handlers import RotatingFileHandler

# Get environment variables for service identification
pod_id = os.getenv('DIGEN_SERVICE_IP', 'local')

# Get service name, default to 'agent'
service_name = os.getenv('DIGEN_SERVICE_NAME', 'agent')

# Ensure log directory exists
os.makedirs('log', exist_ok=True)

# Global flag to track if logger is already configured
_logger_configured = False

class JobIdFilter(logging.Filter):
    """Custom log filter to add job_id and pod_id fields"""
    def filter(self, record):
        if not hasattr(record, 'job_id'):
            record.job_id = 'main'
        if not hasattr(record, 'pod_id'):
            record.pod_id = pod_id
        return True

def setup_logger(name: str = "agent") -> logging.Logger:
    """
    Configure logging setup
    
    Args:
        name: Logger name, defaults to "agent"
    
    Returns:
        logging.Logger: Configured logger
    """
    global _logger_configured
    
    # Get the logger
    logger = logging.getLogger(name)
    
    # If logger is already configured, return it
    if _logger_configured:
        return logger
    
    # Configure logging
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.addFilter(JobIdFilter())

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # File handler with rotation
    file_handler = RotatingFileHandler("log/app.log", maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(pod_id)s][%(job_id)s] - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Mark as configured
    _logger_configured = True
    
    return logger

# Create default logger instance
logger = setup_logger(service_name)
