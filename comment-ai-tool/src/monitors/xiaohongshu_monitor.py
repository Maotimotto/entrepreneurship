"""小红书评论监控器

对接小红书 Web API，通过 Cookie 认证拉取笔记评论。
"""
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator
from src.models.comment import Comment, Platform

logger = logging.getLogger(__name__)

XHS_COMMENT_URL = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
XHS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://www.xiaohongshu.com",
    "Referer": "https://www.xiaohongshu.com/",
}


class XiaohongshuMonitor:
    """小红书评论监控"""

    PLATFORM = Platform.XIAOHONGSHU

    def __init__(self, cookie: str = ""):
        self.cookie = cookie
        self._running = False
        self._has_creds = bool(cookie)

    async def fetch_comments(self, note_id: str, cursor: str = "") -> list[Comment]:
        """拉取单篇笔记的评论"""
        if not self._has_creds:
            logger.warning("小红书: 未配置 cookie，跳过")
            return []

        import httpx
        headers = {**XHS_HEADERS, "Cookie": self.cookie}
        params = {"note_id": note_id, "cursor": cursor, "top_comment_id": ""}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(XHS_COMMENT_URL, headers=headers, params=params)
                data = r.json()
                if data.get("code") != 0:
                    logger.error(f"小红书API错误: {data.get('msg')}")
                    return []
                comments = []
                for item in data.get("data", {}).get("comments", []):
                    comments.append(Comment(
                        id=item.get("id", ""),
                        platform=Platform.XIAOHONGSHU,
                        content=item.get("content", ""),
                        author_id=item.get("user_info", {}).get("user_id", ""),
                        author_name=item.get("user_info", {}).get("nickname", ""),
                        author_avatar=item.get("user_info", {}).get("image", ""),
                        post_id=note_id,
                        post_title="",
                        likes=item.get("like_count", 0),
                        created_at=datetime.fromtimestamp(item.get("create_time", 0) / 1000),
                        raw_data=item,
                    ))
                logger.info(f"小红书: 拉取 {len(comments)} 条评论 (note={note_id})")
                return comments
        except Exception as e:
            logger.error(f"小红书评论拉取失败: {e}")
            return []

    async def poll_comments(self, note_ids: list[str], interval: int = 300) -> AsyncGenerator[Comment, None]:
        self._running = True
        seen = set()
        while self._running:
            for nid in note_ids:
                comments = await self.fetch_comments(nid)
                for c in comments:
                    if c.id not in seen:
                        seen.add(c.id)
                        yield c
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
