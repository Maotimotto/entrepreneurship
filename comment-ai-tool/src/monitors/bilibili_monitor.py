"""B站评论监控器

对接 Bilibili API，通过 Cookie 拉取视频评论。
B站评论 API 较稳定，无需开放平台认证。
"""
import asyncio
import hashlib
import logging
import time
import urllib.parse
from datetime import datetime
from typing import AsyncGenerator
from src.models.comment import Comment, Platform

logger = logging.getLogger(__name__)

BILI_COMMENT_URL = "https://api.bilibili.com/x/v2/reply/main"
BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}


class BilibiliMonitor:
    """B站评论监控"""

    PLATFORM = Platform.BILIBILI

    def __init__(self, cookie: str = "", csrf: str = ""):
        self.cookie = cookie
        self.csrf = csrf
        self._running = False

    async def fetch_comments(self, oid: int, next_offset: int = 0) -> list[Comment]:
        """拉取单条视频的评论

        Args:
            oid: 视频 aid (avid号)
            next_offset: 翻页偏移
        """
        import httpx
        headers = {**BILI_HEADERS}
        if self.cookie:
            headers["Cookie"] = self.cookie

        params = {
            "oid": oid,
            "type": 1,  # 1=视频
            "mode": 2,  # 2=按热度
            "next": next_offset,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(BILI_COMMENT_URL, headers=headers, params=params)
                data = r.json()
                if data.get("code") != 0:
                    logger.error(f"B站API错误: code={data.get('code')} msg={data.get('message')}")
                    return []

                comments = []
                for item in data.get("data", {}).get("replies", []):
                    member = item.get("member", {})
                    comments.append(Comment(
                        id=str(item.get("rpid", "")),
                        platform=Platform.BILIBILI,
                        content=item.get("content", {}).get("message", ""),
                        author_id=str(member.get("mid", "")),
                        author_name=member.get("uname", ""),
                        author_avatar=member.get("avatar", ""),
                        post_id=str(oid),
                        post_title="",
                        likes=item.get("like", 0),
                        created_at=datetime.fromtimestamp(item.get("ctime", 0)),
                        raw_data=item,
                    ))
                logger.info(f"B站: 拉取 {len(comments)} 条评论 (oid={oid})")
                return comments
        except Exception as e:
            logger.error(f"B站评论拉取失败: {e}")
            return []

    async def poll_comments(self, video_aids: list[int], interval: int = 300) -> AsyncGenerator[Comment, None]:
        """持续轮询多条视频的评论"""
        self._running = True
        seen = set()
        while self._running:
            for aid in video_aids:
                comments = await self.fetch_comments(aid)
                for c in comments:
                    if c.id not in seen:
                        seen.add(c.id)
                        yield c
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
