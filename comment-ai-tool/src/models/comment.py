"""数据模型 — Pydantic + SQLAlchemy ORM"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.mysql import ENUM as MyENUM, JSON as MyJSON


# ═══════════ SQLAlchemy ORM Base ═══════════

class Base(DeclarativeBase):
    pass


class Platform(str, Enum):
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_VIDEO = "wechat_video"
    BILIBILI = "bilibili"


# ═══════════ 平台账号 ═══════════

class PlatformAccount(Base):
    """管理的平台账号"""
    __tablename__ = "platform_accounts"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(sa.String(128), nullable=False, comment="平台账号ID")
    account_name: Mapped[str] = mapped_column(sa.String(128), nullable=False, comment="账号昵称")
    account_url: Mapped[Optional[str]] = mapped_column(sa.String(512), comment="主页链接")
    avatar_url: Mapped[Optional[str]] = mapped_column(sa.String(512))
    status: Mapped[str] = mapped_column(sa.String(16), default="active")  # active/paused/error
    config: Mapped[Optional[str]] = mapped_column(sa.Text, comment="JSON: cookie/token/app_key")
    remark: Mapped[Optional[str]] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, onupdate=sa.func.now())

    __table_args__ = (
        sa.UniqueConstraint("platform", "account_id", name="uk_platform_account"),
    )


# ═══════════ 潜客 ═══════════

class Lead(Base):
    """潜客记录"""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    platform_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platform_accounts.id"))
    platform: Mapped[str] = mapped_column(sa.String(32), index=True)
    author_id: Mapped[str] = mapped_column(sa.String(128))
    author_name: Mapped[str] = mapped_column(sa.String(128))
    author_avatar: Mapped[Optional[str]] = mapped_column(sa.String(512))
    first_comment_content: Mapped[Optional[str]] = mapped_column(sa.Text)
    lead_score: Mapped[float] = mapped_column(sa.Float, default=0, index=True)
    status: Mapped[str] = mapped_column(sa.String(32), default="new", index=True)  # new/contacted/converted/lost
    tags: Mapped[Optional[str]] = mapped_column(sa.Text, comment="JSON array")
    notes: Mapped[Optional[str]] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, onupdate=sa.func.now())


# ═══════════ 分析日志 ═══════════

class AnalysisLog(Base):
    """评论分析日志"""
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    platform_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platform_accounts.id"))
    platform: Mapped[str] = mapped_column(sa.String(32), index=True)
    comment_id: Mapped[str] = mapped_column(sa.String(128))
    comment_content: Mapped[str] = mapped_column(sa.Text)
    author_id: Mapped[Optional[str]] = mapped_column(sa.String(128))
    author_name: Mapped[Optional[str]] = mapped_column(sa.String(128))
    post_id: Mapped[Optional[str]] = mapped_column(sa.String(128))
    post_title: Mapped[Optional[str]] = mapped_column(sa.String(512))
    score: Mapped[Optional[float]] = mapped_column(sa.Float, index=True)
    intent: Mapped[Optional[str]] = mapped_column(sa.String(32), index=True)
    urgency: Mapped[Optional[str]] = mapped_column(sa.String(16))
    keywords: Mapped[Optional[str]] = mapped_column(sa.Text, comment="JSON array")
    reasoning: Mapped[Optional[str]] = mapped_column(sa.Text)
    reply_content: Mapped[Optional[str]] = mapped_column(sa.Text)
    replied: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), index=True)


# ═══════════ 回复日志 ═══════════

class ReplyLog(Base):
    """自动回复日志"""
    __tablename__ = "reply_logs"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    analysis_log_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("analysis_logs.id"))
    platform_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platform_accounts.id"))
    platform: Mapped[str] = mapped_column(sa.String(32), index=True)
    comment_id: Mapped[Optional[str]] = mapped_column(sa.String(128))
    reply_content: Mapped[str] = mapped_column(sa.Text)
    status: Mapped[str] = mapped_column(sa.String(16), default="pending", index=True)  # pending/sent/failed
    error_msg: Mapped[Optional[str]] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now(), index=True)


# ═══════════ Pydantic Schemas (API 用) ═══════════

class Comment(BaseModel):
    """平台评论 (API 传输用)"""
    id: str
    platform: Platform
    content: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    post_id: str
    post_title: str
    parent_id: Optional[str] = None
    likes: int = 0
    created_at: Optional[datetime] = None
    raw_data: dict = {}


class LeadScore(BaseModel):
    """潜客评分"""
    comment_id: str
    score: float
    intent: str
    urgency: str
    keywords: list[str]
    reasoning: str


class AccountCreate(BaseModel):
    """创建账号请求"""
    platform: str
    account_id: str
    account_name: str
    account_url: Optional[str] = None
    config: Optional[str] = None
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    """更新账号请求"""
    account_name: Optional[str] = None
    account_url: Optional[str] = None
    status: Optional[str] = None
    config: Optional[str] = None
    remark: Optional[str] = None
