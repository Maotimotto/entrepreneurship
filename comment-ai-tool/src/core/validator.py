"""配置验证模块"""
from config.settings import settings
from src.core.logger import logging

logger = logging.getLogger(__name__)


def validate_config() -> dict:
    """验证配置，返回状态"""
    issues = []
    warnings = []

    # AI 配置
    if not settings.ai_api_key or settings.ai_api_key == "your-api-key":
        warnings.append("未配置 AI API Key，将使用关键词降级模式")
    else:
        if settings.ai_provider == "openai" and not settings.ai_base_url:
            warnings.append("OpenAI 模式但未配置 base_url，可能无法访问")

    # 服务配置
    if settings.server_port < 1024 or settings.server_port > 65535:
        issues.append(f"端口号 {settings.server_port} 不在有效范围 (1024-65535)")

    # 业务参数
    if settings.min_lead_score < 0 or settings.min_lead_score > 1:
        issues.append(f"min_lead_score {settings.min_lead_score} 不在 0-1 范围")

    if settings.max_reply_per_hour < 1:
        issues.append(f"max_reply_per_hour {settings.max_reply_per_hour} 必须 >= 1")

    # 数据库
    if not settings.database_url:
        issues.append("未配置数据库连接")

    result = {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "config": {
            "ai_provider": settings.ai_provider,
            "ai_model": settings.ai_model,
            "has_api_key": bool(settings.ai_api_key and settings.ai_api_key != "your-api-key"),
            "server_port": settings.server_port,
            "database": settings.database_url.split("///")[-1] if "///" in settings.database_url else settings.database_url,
        }
    }

    if issues:
        for issue in issues:
            logger.error(f"配置错误: {issue}")
    if warnings:
        for warning in warnings:
            logger.warning(f"配置警告: {warning}")

    return result
