"""抖音评论监控器

对接抖音开放平台 API，拉取评论数据。
无凭证时使用模拟数据做演示。
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator
from src.models.comment import Comment, Platform

logger = logging.getLogger(__name__)


class DouyinMonitor:
    """抖音评论监控"""

    PLATFORM = Platform.DOUYIN

    def __init__(self, client_key: str = "", client_secret: str = "", access_token: str = ""):
        self.client_key = client_key
        self.client_secret = client_secret
        self.access_token = access_token
        self._running = False
        self._has_creds = bool(access_token)

    async def fetch_comments(self, post_id: str, cursor: str = "") -> list[Comment]:
        """拉取单条视频的评论列表"""
        if not self._has_creds:
            logger.warning("抖音: 未配置 access_token，跳过")
            return []

        import httpx
        url = "https://open.douyin.com/api/douyin/v1/comment/list/"
        headers = {"access-token": self.access_token}
        params = {"item_id": post_id, "cursor": cursor, "count": 50}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(url, headers=headers, params=params)
                data = r.json()
                if data.get("status_code") != 0:
                    logger.error(f"抖音API错误: {data.get('description')}")
                    return []
                comments = []
                for item in data.get("data", {}).get("comments", []):
                    comments.append(Comment(
                        id=item.get("cid", ""),
                        platform=Platform.DOUYIN,
                        content=item.get("text", ""),
                        author_id=item.get("user", {}).get("uid", ""),
                        author_name=item.get("user", {}).get("nickname", ""),
                        author_avatar=item.get("user", {}).get("avatar_thumb", {}).get("url_list", [None])[0],
                        post_id=post_id,
                        post_title="",
                        likes=item.get("digg_count", 0),
                        created_at=datetime.fromtimestamp(item.get("create_time", 0)),
                        raw_data=item,
                    ))
                logger.info(f"抖音: 拉取 {len(comments)} 条评论 (post={post_id})")
                return comments
        except Exception as e:
            logger.error(f"抖音评论拉取失败: {e}")
            return []

    async def poll_comments(self, post_ids: list[str], interval: int = 300) -> AsyncGenerator[Comment, None]:
        """持续轮询多条视频的评论"""
        self._running = True
        seen = set()
        while self._running:
            for pid in post_ids:
                comments = await self.fetch_comments(pid)
                for c in comments:
                    if c.id not in seen:
                        seen.add(c.id)
                        yield c
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False


# ═══════════ 模拟数据 (无凭证时) ═══════════

MOCK_COMMENTS = [
    Comment(
        id="mock_001", platform=Platform.DOUYIN,
        content="这个AI工具怎么做的？想学！有没有教程",
        author_id="user_001", author_name="科技小王",
        post_id="post_001", post_title="用Python做了个AI自动回复工具",
        likes=23, created_at=datetime.now() - timedelta(minutes=15),
    ),
    Comment(
        id="mock_002", platform=Platform.DOUYIN,
        content="多少钱能学会这个？有课程吗？想报名",
        author_id="user_002", author_name="创业小白",
        post_id="post_001", post_title="用Python做了个AI自动回复工具",
        likes=8, created_at=datetime.now() - timedelta(minutes=30),
    ),
    Comment(
        id="mock_003", platform=Platform.DOUYIN,
        content="太厉害了！大佬能带带我吗？可以付费学习",
        author_id="user_003", author_name="程序猿阿杰",
        post_id="post_001", post_title="用Python做了个AI自动回复工具",
        likes=15, created_at=datetime.now() - timedelta(hours=1),
    ),
    Comment(
        id="mock_004", platform=Platform.DOUYIN,
        content="这个产品怎么卖的？想给公司采购几套",
        author_id="user_004", author_name="B端客户李总",
        post_id="post_002", post_title="AI自动化办公实操",
        likes=5, created_at=datetime.now() - timedelta(hours=2),
    ),
    Comment(
        id="mock_005", platform=Platform.DOUYIN,
        content="不错不错，先收藏了",
        author_id="user_005", author_name="路过的咸鱼",
        post_id="post_001", post_title="用Python做了个AI自动回复工具",
        likes=3, created_at=datetime.now() - timedelta(hours=3),
    ),
    Comment(
        id="mock_006", platform=Platform.DOUYIN,
        content="哈哈哈哈笑死我了",
        author_id="user_006", author_name="吃瓜群众",
        post_id="post_002", post_title="AI自动化办公实操",
        likes=42, created_at=datetime.now() - timedelta(hours=4),
    ),
    Comment(
        id="mock_007", platform=Platform.DOUYIN,
        content="我之前学过类似的，效果一般般",
        author_id="user_007", author_name="谨慎观望",
        post_id="post_002", post_title="AI自动化办公实操",
        likes=1, created_at=datetime.now() - timedelta(hours=5),
    ),
    Comment(
        id="mock_008", platform=Platform.DOUYIN,
        content="求私信！急！老板催着要方案",
        author_id="user_008", author_name="打工人小刘",
        post_id="post_003", post_title="评论区自动获客实战",
        likes=19, created_at=datetime.now() - timedelta(minutes=45),
    ),
    Comment(
        id="mock_009", platform=Platform.DOUYIN,
        content="👍",
        author_id="user_009", author_name="沉默的大多数",
        post_id="post_003", post_title="评论区自动获客实战",
        likes=0, created_at=datetime.now() - timedelta(hours=6),
    ),
    Comment(
        id="mock_010", platform=Platform.DOUYIN,
        content="有没有试用版？想先体验下再决定",
        author_id="user_010", author_name="理性消费者",
        post_id="post_003", post_title="评论区自动获客实战",
        likes=7, created_at=datetime.now() - timedelta(hours=8),
    ),
]
