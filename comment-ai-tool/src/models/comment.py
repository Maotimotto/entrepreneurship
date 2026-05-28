"""评论数据模型"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_VIDEO = "wechat_video"


class Comment(BaseModel):
    """平台评论"""
    id: str                          # 平台评论ID
    platform: Platform               # 来源平台
    content: str                     # 评论内容
    author_id: str                   # 评论者ID
    author_name: str                 # 评论者昵称
    author_avatar: Optional[str] = None
    post_id: str                     # 所属作品ID
    post_title: str                  # 作品标题
    parent_id: Optional[str] = None  # 父评论ID (回复)
    likes: int = 0                   # 点赞数
    created_at: datetime = None      # 评论时间
    raw_data: dict = {}              # 原始数据


class LeadScore(BaseModel):
    """潜客评分"""
    comment_id: str
    score: float          # 0-1 综合评分
    intent: str           # 意图分类: inquiry / complaint / praise / spam / potential_lead
    urgency: str          # 紧急度: high / medium / low
    keywords: list[str]   # 触发关键词
    reasoning: str        # AI推理说明


class ReplyTemplate(BaseModel):
    """回复模板"""
    id: str
    name: str
    platform: Platform
    intent_type: str             # 适用的意图类型
    template: str                # 回复模板 (支持 {变量})
    tone: str = "friendly"       # 语气: friendly / professional / humorous
    include_contact: bool = False # 是否包含联系方式


class Lead(BaseModel):
    """潜客记录"""
    id: str
    platform: Platform
    author_id: str
    author_name: str
    first_comment_id: str
    lead_score: float
    status: str = "new"           # new / contacted / converted / lost
    tags: list[str] = []
    notes: str = ""
    created_at: datetime = None
    updated_at: datetime = None
