"""评论AI — 主入口"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from src.api.routes import router
from src.core.logger import setup_logging
from src.core.database import init_db
from src.scheduler import scheduler
import os

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库 + 启动调度器"""
    await init_db()
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(
    title="评论AI",
    description="短视频评论智能识别与自动转化管理平台",
    version="0.2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"name": "评论AI", "version": "0.2.1", "status": "running", "docs": "/docs"}


# 调度器控制
@app.get("/api/v1/scheduler/status")
async def scheduler_status():
    return {"running": scheduler.is_running}


@app.post("/api/v1/scheduler/start")
async def scheduler_start():
    scheduler.start()
    return {"ok": True, "running": True}


@app.post("/api/v1/scheduler/stop")
async def scheduler_stop():
    scheduler.stop()
    return {"ok": True, "running": False}


@app.post("/api/v1/scheduler/tick")
async def scheduler_tick():
    """手动触发一次轮询"""
    await scheduler.poll_and_analyze()
    await scheduler.execute_pending_replies()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
