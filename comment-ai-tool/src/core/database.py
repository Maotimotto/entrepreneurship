"""数据库模块 — SQLAlchemy async + MySQL"""
import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, update, delete, and_
from config.settings import settings
from src.models.comment import Base, PlatformAccount, Lead, AnalysisLog, ReplyLog

logger = logging.getLogger(__name__)

# ═══════════ Engine & Session ═══════════

engine = create_async_engine(settings.db_url, echo=False, pool_pre_ping=False, pool_recycle=3600)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成")


async def get_session() -> AsyncSession:
    return async_session()


# ═══════════ PlatformAccount CRUD ═══════════

class AccountStore:

    @staticmethod
    async def create(data: dict) -> PlatformAccount:
        async with async_session() as s:
            acc = PlatformAccount(**data)
            s.add(acc)
            await s.commit()
            await s.refresh(acc)
            return acc

    @staticmethod
    async def get(account_id: int) -> Optional[PlatformAccount]:
        async with async_session() as s:
            return await s.get(PlatformAccount, account_id)

    @staticmethod
    async def list_all(platform: Optional[str] = None, status: Optional[str] = None) -> list[PlatformAccount]:
        async with async_session() as s:
            q = select(PlatformAccount)
            if platform:
                q = q.where(PlatformAccount.platform == platform)
            if status:
                q = q.where(PlatformAccount.status == status)
            q = q.order_by(PlatformAccount.created_at.desc())
            result = await s.execute(q)
            return list(result.scalars().all())

    @staticmethod
    async def update(account_id: int, data: dict) -> bool:
        async with async_session() as s:
            data["updated_at"] = datetime.now()
            stmt = update(PlatformAccount).where(PlatformAccount.id == account_id).values(**data)
            r = await s.execute(stmt)
            await s.commit()
            return r.rowcount > 0

    @staticmethod
    async def delete(account_id: int) -> bool:
        async with async_session() as s:
            stmt = delete(PlatformAccount).where(PlatformAccount.id == account_id)
            r = await s.execute(stmt)
            await s.commit()
            return r.rowcount > 0

    @staticmethod
    async def count() -> int:
        async with async_session() as s:
            r = await s.execute(select(func.count(PlatformAccount.id)))
            return r.scalar() or 0


# ═══════════ Lead Store ═══════════

class LeadStore:

    @staticmethod
    async def save(lead_data: dict) -> Lead:
        async with async_session() as s:
            lead = Lead(**lead_data)
            s.add(lead)
            await s.commit()
            await s.refresh(lead)
            return lead

    @staticmethod
    async def get(lead_id: int) -> Optional[Lead]:
        async with async_session() as s:
            return await s.get(Lead, lead_id)

    @staticmethod
    async def list_all(
        platform: Optional[str] = None,
        status: Optional[str] = None,
        min_score: float = 0.0,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Lead], int]:
        async with async_session() as s:
            q = select(Lead).where(Lead.lead_score >= min_score)
            cnt_q = select(func.count(Lead.id)).where(Lead.lead_score >= min_score)
            if platform:
                q = q.where(Lead.platform == platform)
                cnt_q = cnt_q.where(Lead.platform == platform)
            if status:
                q = q.where(Lead.status == status)
                cnt_q = cnt_q.where(Lead.status == status)
            if start_time:
                q = q.where(Lead.created_at >= start_time)
                cnt_q = cnt_q.where(Lead.created_at >= start_time)
            if end_time:
                q = q.where(Lead.created_at <= end_time)
                cnt_q = cnt_q.where(Lead.created_at <= end_time)

            total = (await s.execute(cnt_q)).scalar() or 0
            q = q.order_by(Lead.created_at.desc()).limit(limit).offset(offset)
            result = await s.execute(q)
            return list(result.scalars().all()), total

    @staticmethod
    async def update_status(lead_id: int, status: str) -> bool:
        async with async_session() as s:
            stmt = update(Lead).where(Lead.id == lead_id).values(status=status, updated_at=datetime.now())
            r = await s.execute(stmt)
            await s.commit()
            return r.rowcount > 0


# ═══════════ AnalysisLog Store ═══════════

class AnalysisLogStore:

    @staticmethod
    async def save(log_data: dict) -> AnalysisLog:
        async with async_session() as s:
            log = AnalysisLog(**log_data)
            s.add(log)
            await s.commit()
            await s.refresh(log)
            return log

    @staticmethod
    async def list_all(
        platform: Optional[str] = None,
        intent: Optional[str] = None,
        author_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AnalysisLog], int]:
        async with async_session() as s:
            q = select(AnalysisLog)
            cnt_q = select(func.count(AnalysisLog.id))
            filters = []
            if platform:
                filters.append(AnalysisLog.platform == platform)
            if intent:
                filters.append(AnalysisLog.intent == intent)
            if author_name:
                filters.append(AnalysisLog.author_name.like(f"%{author_name}%"))
            if start_time:
                filters.append(AnalysisLog.created_at >= start_time)
            if end_time:
                filters.append(AnalysisLog.created_at <= end_time)

            if filters:
                q = q.where(and_(*filters))
                cnt_q = cnt_q.where(and_(*filters))

            total = (await s.execute(cnt_q)).scalar() or 0
            q = q.order_by(AnalysisLog.created_at.desc()).limit(limit).offset(offset)
            result = await s.execute(q)
            return list(result.scalars().all()), total


# ═══════════ ReplyLog Store ═══════════

class ReplyLogStore:

    @staticmethod
    async def save(log_data: dict) -> ReplyLog:
        async with async_session() as s:
            log = ReplyLog(**log_data)
            s.add(log)
            await s.commit()
            await s.refresh(log)
            return log

    @staticmethod
    async def list_all(
        platform: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReplyLog], int]:
        async with async_session() as s:
            q = select(ReplyLog)
            cnt_q = select(func.count(ReplyLog.id))
            filters = []
            if platform:
                filters.append(ReplyLog.platform == platform)
            if status:
                filters.append(ReplyLog.status == status)
            if filters:
                q = q.where(and_(*filters))
                cnt_q = cnt_q.where(and_(*filters))
            total = (await s.execute(cnt_q)).scalar() or 0
            q = q.order_by(ReplyLog.created_at.desc()).limit(limit).offset(offset)
            result = await s.execute(q)
            return list(result.scalars().all()), total


# ═══════════ 统计 ═══════════

class StatsStore:

    @staticmethod
    async def overview() -> dict:
        async with async_session() as s:
            # 账号数
            acc_cnt = (await s.execute(select(func.count(PlatformAccount.id)))).scalar() or 0
            # 潜客数
            lead_cnt = (await s.execute(select(func.count(Lead.id)))).scalar() or 0
            # 分析数
            log_cnt = (await s.execute(select(func.count(AnalysisLog.id)))).scalar() or 0
            # 回复数
            reply_cnt = (await s.execute(
                select(func.count(ReplyLog.id)).where(ReplyLog.status == "sent")
            )).scalar() or 0

            return {
                "accounts": acc_cnt,
                "leads": lead_cnt,
                "analyzed": log_cnt,
                "replies_sent": reply_cnt,
            }

    @staticmethod
    async def by_platform() -> list[dict]:
        async with async_session() as s:
            rows = (await s.execute(
                select(
                    Lead.platform,
                    func.count(Lead.id).label("leads"),
                    func.avg(Lead.lead_score).label("avg_score"),
                ).group_by(Lead.platform)
            )).all()
            return [
                {"platform": r[0], "leads": r[1], "avg_score": round(r[2] or 0, 2)}
                for r in rows
            ]

    @staticmethod
    async def by_intent() -> list[dict]:
        async with async_session() as s:
            rows = (await s.execute(
                select(
                    AnalysisLog.intent,
                    func.count(AnalysisLog.id).label("count"),
                ).where(AnalysisLog.intent.isnot(None)).group_by(AnalysisLog.intent)
            )).all()
            return [{"intent": r[0], "count": r[1]} for r in rows]

    @staticmethod
    async def daily_trend(days: int = 7) -> list[dict]:
        async with async_session() as s:
            rows = (await s.execute(
                select(
                    func.date(AnalysisLog.created_at).label("day"),
                    func.count(AnalysisLog.id).label("count"),
                    func.avg(AnalysisLog.score).label("avg_score"),
                ).group_by(func.date(AnalysisLog.created_at))
                 .order_by(func.date(AnalysisLog.created_at).desc())
                 .limit(days)
            )).all()
            return [
                {"day": str(r[0]), "count": r[1], "avg_score": round(r[2] or 0, 2)}
                for r in rows
            ]
