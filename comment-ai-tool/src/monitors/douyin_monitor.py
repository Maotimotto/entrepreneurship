"""抖音评论监控器

MVP阶段: 使用模拟数据，验证AI分析流程
正式版: 对接抖音开放平台API
"""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from src.models.comment import Comment, Platform


class DouyinMonitor:
    """抖音评论监控"""

    def __init__(self):
        self._running = False

    async def poll_comments(self, post_ids: list[str]) -> AsyncGenerator[Comment, None]:
        """轮询获取新评论"""
        while self._running:
            # TODO: 替换为真实API调用
            await asyncio.sleep(300)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False


# === 模拟数据 — 覆盖各种真实场景 ===

MOCK_COMMENTS = [
    # 🔥 高意向 — 明确购买/学习意向
    Comment(
        id="mock_001",
        platform=Platform.DOUYIN,
        content="这个AI工具怎么做的？想学！有没有教程",
        author_id="user_001",
        author_name="科技小王",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=23,
        created_at=datetime.now() - timedelta(minutes=15),
    ),
    Comment(
        id="mock_002",
        platform=Platform.DOUYIN,
        content="多少钱能学会这个？有课程吗？想报名",
        author_id="user_002",
        author_name="创业小白",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=8,
        created_at=datetime.now() - timedelta(minutes=12),
    ),
    Comment(
        id="mock_004",
        platform=Platform.DOUYIN,
        content="求合作，我们公司也想做类似的东西，方便加个微信吗",
        author_id="user_004",
        author_name="B端客户李总",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=3,
        created_at=datetime.now() - timedelta(minutes=8),
    ),

    # 👀 中意向 — 正面反馈但无明确购买信号
    Comment(
        id="mock_003",
        platform=Platform.DOUYIN,
        content="太厉害了，干货满满，已收藏",
        author_id="user_003",
        author_name="路人甲",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=45,
        created_at=datetime.now() - timedelta(minutes=10),
    ),
    Comment(
        id="mock_006",
        platform=Platform.DOUYIN,
        content="关注了！期待后续更新",
        author_id="user_006",
        author_name="学习达人",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=12,
        created_at=datetime.now() - timedelta(minutes=5),
    ),

    # 💤 低意向 — 闲聊、表情、无关
    Comment(
        id="mock_005",
        platform=Platform.DOUYIN,
        content="哈哈哈哈笑死",
        author_id="user_005",
        author_name="吃瓜群众",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=67,
        created_at=datetime.now() - timedelta(minutes=6),
    ),
    Comment(
        id="mock_007",
        platform=Platform.DOUYIN,
        content="666666",
        author_id="user_007",
        author_name="路过的大哥",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=3,
        created_at=datetime.now() - timedelta(minutes=4),
    ),
    Comment(
        id="mock_008",
        platform=Platform.DOUYIN,
        content="第一",
        author_id="user_008",
        author_name="抢沙发",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=1,
        created_at=datetime.now() - timedelta(minutes=3),
    ),

    # 🎯 特殊场景 — 需要精细识别
    Comment(
        id="mock_009",
        platform=Platform.DOUYIN,
        content="我在做短视频运营，每天手动回复评论累死了，这个能帮我自动化吗？",
        author_id="user_009",
        author_name="运营小美",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=19,
        created_at=datetime.now() - timedelta(minutes=2),
    ),
    Comment(
        id="mock_010",
        platform=Platform.DOUYIN,
        content="之前买过别的课程，感觉被割韭菜了，你这个靠谱吗",
        author_id="user_010",
        author_name="谨慎观望",
        post_id="post_001",
        post_title="用Python做了个AI自动回复工具",
        likes=31,
        created_at=datetime.now() - timedelta(minutes=1),
    ),
]
