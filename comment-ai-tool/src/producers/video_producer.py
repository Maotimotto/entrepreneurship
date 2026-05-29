"""MoneyPrinterTurbo 客户端

将评论分析结果转化为短视频：
  评论关键词 → 视频主题 → 自动出片
"""
import asyncio
import logging
from typing import Optional
from dataclasses import dataclass, field

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class VideoTask:
    """视频生成任务"""
    task_id: str = ""
    status: str = "pending"  # pending / processing / completed / failed
    video_url: str = ""
    error: str = ""


@dataclass
class VideoRequest:
    """视频生成请求"""
    subject: str                    # 视频主题
    script: str = ""               # 自定义文案（空则自动生成）
    terms: list[str] = field(default_factory=list)  # 搜索关键词
    aspect: str = "9:16"           # 9:16 / 16:9 / 1:1
    voice_name: str = ""           # 配音（空则默认）
    video_source: str = "pexels"   # pexels / pixabay
    video_count: int = 1


class VideoProducer:
    """MoneyPrinterTurbo API 客户端"""

    def __init__(self, base_url: str = ""):
        self.base_url = (base_url or settings.mpt_base_url).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """检查 MoneyPrinterTurbo 服务是否可用"""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/")
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"MoneyPrinterTurbo 健康检查失败: {e}")
            return False

    async def generate_video(self, req: VideoRequest) -> VideoTask:
        """提交视频生成任务"""
        client = await self._get_client()

        payload = {
            "video_subject": req.subject,
            "video_script": req.script,
            "video_terms": req.terms if req.terms else None,
            "video_aspect": req.aspect,
            "video_source": req.video_source,
            "video_count": req.video_count,
        }
        if req.voice_name:
            payload["voice_name"] = req.voice_name

        # 去掉 None 值
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            resp = await client.post(
                f"{self.base_url}/api/v1/videos",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == 200:
                task_data = data.get("data", {})
                return VideoTask(
                    task_id=task_data.get("task_id", ""),
                    status="processing",
                )
            else:
                return VideoTask(
                    status="failed",
                    error=data.get("message", "未知错误"),
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"视频生成请求失败: {e.response.status_code}")
            return VideoTask(status="failed", error=str(e))
        except Exception as e:
            logger.error(f"视频生成异常: {e}")
            return VideoTask(status="failed", error=str(e))

    async def query_task(self, task_id: str) -> VideoTask:
        """查询任务状态"""
        client = await self._get_client()

        try:
            resp = await client.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == 200:
                task_data = data.get("data", {})
                return VideoTask(
                    task_id=task_id,
                    status=task_data.get("status", "unknown"),
                    video_url=task_data.get("video_url", ""),
                    error=task_data.get("error", ""),
                )
            return VideoTask(task_id=task_id, status="failed", error=data.get("message", ""))
        except Exception as e:
            logger.error(f"查询任务状态失败: {e}")
            return VideoTask(task_id=task_id, status="failed", error=str(e))

    async def wait_for_task(self, task_id: str, timeout: int = 600, poll_interval: int = 10) -> VideoTask:
        """等待任务完成"""
        elapsed = 0
        while elapsed < timeout:
            task = await self.query_task(task_id)
            if task.status == "completed":
                return task
            if task.status == "failed":
                return task
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return VideoTask(task_id=task_id, status="failed", error="超时")

    async def produce_from_comments(
        self,
        topic: str,
        keywords: list[str],
        script: str = "",
        aspect: str = "9:16",
    ) -> VideoTask:
        """从评论分析结果生成视频（核心业务方法）

        Args:
            topic: 从评论中提取的主题
            keywords: 高频关键词列表
            script: 可选的自定义文案
            aspect: 视频比例
        """
        req = VideoRequest(
            subject=topic,
            script=script,
            terms=keywords,
            aspect=aspect,
        )

        logger.info(f"开始生成视频: 主题={topic}, 关键词={keywords}")
        task = await self.generate_video(req)

        if task.status == "processing" and task.task_id:
            logger.info(f"视频任务已提交: {task.task_id}")
            task = await self.wait_for_task(task.task_id)
            if task.status == "completed":
                logger.info(f"视频生成完成: {task.video_url}")
            else:
                logger.error(f"视频生成失败: {task.error}")

        return task


# 全局实例
video_producer = VideoProducer()
