from typing import List, Optional
from pydantic import BaseModel

# 数据模型
class InputItem(BaseModel):
    type: str  # "image" or "video"
    url: str   # S3 URL for images or videos

class Options(BaseModel):
    prompt: Optional[str] = None
    seed: Optional[int] = None  # 添加随机种子参数
    duration: Optional[int] = None  # 添加时长参数，单位为秒，范围4~10
    upload_url: Optional[str] = None  # 添加自定义上传URL参数
    upload_wasabi_url: Optional[str] = None  # 添加自定义上传wasabi URL参数
    resolution: Optional[str] = None  # 预设分辨率，例如 "512x512", "768x512" 等
    crf: Optional[int] = None # 输出视频的crf值

class GenerateRequest(BaseModel):
    model: str
    input: List[InputItem]
    options: Options
    webhookUrl: str

class GenerateResponse(BaseModel):
    id: str
    createdAt: str
    status: str
    model: str
    input: List[InputItem]
    webhookUrl: str
    options: dict = {}  # Default options as an empty dictionary
    stream: bool = True
    outputUrl: Optional[str] = None  # S3 URL
    localUrl: Optional[str] = None   # 本地文件下载地址
    outputWasabiUrl: Optional[str] = None # 上传失败为空
    error: Optional[str] = None