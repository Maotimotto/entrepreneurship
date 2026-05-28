"""全局配置 — 从环境变量加载"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI
    ai_provider: str = "openai"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = "https://api.openai.com/v1"

    # 抖音
    douyin_client_key: str = ""
    douyin_client_secret: str = ""
    douyin_access_token: str = ""

    # 服务
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    log_level: str = "INFO"

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./comment_ai.db"

    # 业务参数
    check_interval_seconds: int = 300  # 评论检查间隔
    min_lead_score: float = 0.6       # 最低潜客评分
    max_reply_per_hour: int = 20      # 每小时最大回复数
    reply_delay_range: tuple = (30, 120)  # 回复延迟范围(秒)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
