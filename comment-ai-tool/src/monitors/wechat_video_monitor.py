"""微信视频号评论监控器

对接微信视频号 API，通过 appid/secret 拉取评论。
视频号 API 目前仍在内测，接口可能变动。
"""
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator
from src.models.comment import Comment, Platform

logger = logging.getLogger(__name__)


class WechatVideoMonitor:
    """微信视频号评论监控"""

    PLATFORM = Platform.WECHAT_VIDEO

    def __init__(self, appid: str = "", secret: str = ""):
        self.appid = appid
        self.secret = secret
        self._access_token = ""
        self._token_expires = 0
        self._running = False
        self._has_creds = bool(appid and secret)

    async def _ensure_token(self):
        """刷新 access_token"""
        if not self._has_creds:
            return
        import time
        import httpx
        if self._access_token and time.time() < self._token_expires:
            return
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {"grant_type": "client_credential", "appid": self.appid, "secret": self.secret}
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(url, params=params)
                data = r.json()
                if "access_token" in data:
                    self._access_token = data["access_token"]
                    self._token_expires = time.time() + data.get("expires_in", 7200) - 300
                    logger.info("视频号: access_token 刷新成功")
                else:
                    logger.error(f"视频号token获取失败: {data}")
        except Exception as e:
            logger.error(f"视频号token请求异常: {e}")

    async def fetch_comments(self, video_id: str, cookie: str = "") -> list[Comment]:
        """拉取单条视频的评论"""
        if not self._has_creds:
            logger.warning("视频号: 未配置 appid/secret，跳过")
            return []

        await self._ensure_token()
        import httpx
        # 视频号评论接口（需关注创作者能力）
        url = "https://api.weixin.qq.com/channels/comment/list"
        headers = {"Content-Type": "application/json"}
        body = {"video_id": video_id, "cookie": cookie}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    f"{url}?access_token={self._access_token}",
                    headers=headers,
                    json=body,
                )
                data = r.json()
                if data.get("errcode", 0) != 0:
                    logger.error(f"视频号API错误: {data.get('errmsg')}")
                    return []
                comments = []
                for item in data.get("comment_list", []):
                    comments.append(Comment(
                        id=item.get("comment_id", ""),
                        platform=Platform.WECHAT_VIDEO,
                        content=item.get("content", ""),
                        author_id=item.get("commenter", {}).get("commenter_openid", ""),
                        author_name=item.get("commenter", {}).get("nickname", "微信用户"),
                        post_id=video_id,
                        post_title="",
                        likes=item.get("like_count", 0),
                        created_at=datetime.fromtimestamp(item.get("create_time", 0)),
                        raw_data=item,
                    ))
                logger.info(f"视频号: 拉取 {len(comments)} 条评论 (video={video_id})")
                return comments
        except Exception as e:
            logger.error(f"视频号评论拉取失败: {e}")
            return []

    async def poll_comments(self, video_ids: list[str], interval: int = 300) -> AsyncGenerator[Comment, None]:
        self._running = True
        seen = set()
        while self._running:
            for vid in video_ids:
                comments = await self.fetch_comments(vid)
                for c in comments:
                    if c.id not in seen:
                        seen.add(c.id)
                        yield c
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
