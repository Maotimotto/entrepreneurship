"""日志配置"""
import logging
import sys


def setup_logging(level: str = "INFO"):
    """配置全局日志"""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # 降低第三方库日志级别
    for lib in ["httpx", "httpcore", "openai", "uvicorn.access"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
