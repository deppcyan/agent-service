import os
import sys
from pathlib import Path

# 自动将 PYTHONPATH 设置为 app 的上层目录
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.utils.utils import init_service_url
from app.core.model_config import load_model_configs, refresh_model_configs
from app.core.config_manager import config_manager
from app.storage.s3_manager import init_s3_providers
from app.routers import workflow, files, jobs, health, config as config_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    
    # Initialize service URL
    init_service_url()
    
    # Initialize S3 providers
    init_s3_providers()
    
    # Register file-specific config refreshers
    config_manager.register_file_refresher("config/model.json", refresh_model_configs)

    # Load model configurations (local first)
    load_model_configs("config/model.json")

    # Attempt to sync remote configs and refresh loaded configs if updated
    await config_manager.sync_from_remote()
    
    # Load workflow nodes
    from app.workflow.registry import node_registry
    node_registry.load_builtin_nodes()
    node_registry.load_custom_nodes("app/workflow/custom_nodes")
        
    # Startup complete
    yield
    
    # Cleanup on shutdown (if needed)
    pass

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有headers
)

# Include routers
app.include_router(workflow.router)
app.include_router(files.router)
app.include_router(jobs.router)
app.include_router(health.router)
app.include_router(config_router.router)

if __name__ == "__main__":
    import uvicorn
    # port改了，webhook端口也需要改
    uvicorn.run(app, host="0.0.0.0", port=8001)