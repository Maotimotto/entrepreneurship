"""抖音评论监控器

MVP阶段: 使用模拟数据，验证AI分析流程
正式版: 对接抖音开放平台API
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from src.models.comment import Comment, Platform


class DouyinMonitor:
    """抖音评论监控"""

    def __init__(self):
        self._running = False

    async def poll_comments(self, post_ids: list[str]) -> AsyncGenerator[Comment, None]:
        """轮询获取新评论
        
        MVP阶段用模拟数据，正式版对接API:
        - 抖音开放平台: POST /video/comment/list/
        - 需要: client_key + access_token
        """
        while self._running:
            # TODO: 替换为真实API调用
            # comments = await self._fetch_from_api(post_ids)
            # for c in comments:
            #     yield c
            await asyncio.sleep(300)  # 5分钟检查一次

    async def _fetch_from_api(self, post_ids: list[str]) -> list[Comment]:
        """调用抖音开放平台获取评论
        
        API文档: https://developer.open-douyin.com/
        接口: /video/comment/list/
        限流: 10次/秒
        """
        # TODO: 实现API调用
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get(
        #         "https://open.douyin.com/api/douyin/v1/video/comment/list/",
        #         headers={"access-token": settings.douyin_access_token},
        #         params={"item_id": post_id, "count": 50}
        #     )
        pass

    def start(self):
        self._running = True

    def stop(self):
        self._running = False


# === 模拟数据生成 (开发/演示用) ===

MOCK_COMMENTS = [
    Comment(
        id="mock_001",
        platform=Platform.DOUYIN,
        content="这个AI工具怎么做的？想学！",
        author_id="user_001",
        author_name="科技小王",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        created_at=datetime.now(),
    ),
    Comment(
        id="mock_002",
        platform=Platform.DOUYIN,
        content="多少钱能学会这个？有课程吗",
        author_id="user_002",
        author_name="创业小白",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        created_at=datetime.now(),
    ),
    Comment(
        id="mock_003",
        platform=Platform.DOUYIN,
        content="666 太厉害了",
        author_id="user_003",
        author_name="路人甲",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        created_at=datetime.now(),
    ),
    Comment(
        id="mock_004",
        platform=Platform.DOUYIN,
        content="求合作，我们公司也想做类似的东西，方便加个微信吗",
        author_id="user_004",
        author_name="B端客户李总",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        created_at=datetime.now(),
    ),
    Comment(
        id="mock_005",
        platform=Platform.DOUYIN,
        content="哈哈哈哈",
        author_id="user_005",
        author_name="吃瓜群众",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        created_at=datetime.now(),
    ),
]
