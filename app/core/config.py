from typing import Dict
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    API_KEY: str
    QWEN_VL_URL: str
    WAN_I2V_URL: str
    WAN_TALK_URL: str
    QWEN_EDIT_URL: str
    VIDEO_CONCAT_URL: str
    S3_BUCKET: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def get_service_urls() -> Dict[str, str]:
    settings = get_settings()
    return {
        "qwen-vl": settings.QWEN_VL_URL,
        "wan-i2v": settings.WAN_I2V_URL,
        "wan-talk": settings.WAN_TALK_URL,
        "qwen-edit": settings.QWEN_EDIT_URL,
        "concat-upscale": settings.VIDEO_CONCAT_URL
    }
