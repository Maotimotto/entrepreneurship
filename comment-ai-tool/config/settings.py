"""全局配置 — MySQL + 环境变量"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # === 数据库 ===
    db_url: str = "mysql+asyncmy://commentai:comment_ai_pass@localhost:3306/comment_ai"

    # === AI ===
    ai_provider: str = "openai"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_base_url: str = "https://api.openai.com/v1"

    # === 抖音开放平台 ===
    douyin_client_key: str = ""
    douyin_client_secret: str = ""
    douyin_access_token: str = ""

    # === 小红书 ===
    xhs_cookie: str = ""

    # === 微信视频号 ===
    wechat_appid: str = ""
    wechat_secret: str = ""

    # === B站 ===
    bilibili_cookie: str = ""
    bilibili_csrf: str = ""

    # === 抖音 Cookie ===
    douyin_cookie: str = ""

    # === MoneyPrinterTurbo ===
    mpt_base_url: str = "http://localhost:8080"
    mpt_enabled: bool = False

    # === Obsidian ===
    obsidian_vault_path: str = "/mnt/c/Users/24961/Documents/大模型笔记"
    obsidian_auto_save: bool = True

    # === 服务 ===
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    log_level: str = "INFO"

    # === 业务参数 ===
    check_interval_seconds: int = 300
    min_lead_score: float = 0.6
    max_reply_per_hour: int = 20
    reply_delay_range: tuple = (30, 120)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
