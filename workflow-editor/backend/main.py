from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import os

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Connection(BaseModel):
    from_node: str
    from_port: str
    to_node: str
    to_port: str

class WorkflowData(BaseModel):
    nodes: Dict
    connections: List[Connection]

WORKFLOW_DIR = "/home/digen/ssd2/workspace/agent-service/config/workflows"

@app.get("/api/workflows")
async def list_workflows():
    """列出所有可用的workflow配置文件"""
    try:
        files = [f for f in os.listdir(WORKFLOW_DIR) if f.endswith('.json')]
        return {"workflows": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows/{filename}")
async def get_workflow(filename: str):
    """获取特定workflow的配置"""
    try:
        file_path = os.path.join(WORKFLOW_DIR, filename)
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/workflows/{filename}")
async def update_workflow(filename: str, workflow: WorkflowData):
    """更新workflow配置"""
    try:
        file_path = os.path.join(WORKFLOW_DIR, filename)
        with open(file_path, 'w') as f:
            json.dump(workflow.dict(), f, indent=4)
        return {"message": "Workflow updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
