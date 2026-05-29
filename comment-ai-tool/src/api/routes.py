"""API路由 — 管理平台接口

账号管理 | 潜客筛选 | 分析日志 | 统计看板
"""
import json
import csv
import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime

from src.models.comment import (
    Comment, LeadScore, AccountCreate, AccountUpdate, Platform,
)
from src.core.database import (
    AccountStore, LeadStore, AnalysisLogStore, ReplyLogStore, StatsStore,
)
from src.core.logger import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


# ═══════════ 健康检查 ═══════════

@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0", "accounts": await AccountStore.count()}


# ═══════════ 平台账号管理 ═══════════

@router.post("/accounts")
async def create_account(data: AccountCreate):
    """创建平台账号"""
    acc = await AccountStore.create(data.model_dump())
    logger.info(f"创建账号: [{data.platform}] {data.account_name}")
    return {"ok": True, "id": acc.id}


@router.get("/accounts")
async def list_accounts(
    platform: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取账号列表"""
    accounts = await AccountStore.list_all(platform=platform, status=status)
    result = []
    for a in accounts:
        result.append({
            "id": a.id,
            "platform": a.platform,
            "account_id": a.account_id,
            "account_name": a.account_name,
            "account_url": a.account_url,
            "avatar_url": a.avatar_url,
            "status": a.status,
            "config": a.config,
            "remark": a.remark,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })
    return {"total": len(result), "accounts": result}


@router.get("/accounts/{account_id}")
async def get_account(account_id: int):
    """获取单个账号"""
    acc = await AccountStore.get(account_id)
    if not acc:
        raise HTTPException(404, "账号不存在")
    return {
        "id": acc.id,
        "platform": acc.platform,
        "account_id": acc.account_id,
        "account_name": acc.account_name,
        "account_url": acc.account_url,
        "avatar_url": acc.avatar_url,
        "status": acc.status,
        "config": acc.config,
        "remark": acc.remark,
        "created_at": acc.created_at.isoformat() if acc.created_at else None,
        "updated_at": acc.updated_at.isoformat() if acc.updated_at else None,
    }


@router.put("/accounts/{account_id}")
async def update_account(account_id: int, data: AccountUpdate):
    """更新账号"""
    acc = await AccountStore.get(account_id)
    if not acc:
        raise HTTPException(404, "账号不存在")
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(400, "无更新内容")
    ok = await AccountStore.update(account_id, update_data)
    return {"ok": ok}


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: int):
    """删除账号"""
    ok = await AccountStore.delete(account_id)
    if not ok:
        raise HTTPException(404, "账号不存在")
    return {"ok": True}


# ═══════════ 潜客管理 ═══════════

@router.get("/leads")
async def list_leads(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    min_score: float = 0.0,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """潜客列表 — 支持平台/状态/评分/时间筛选"""
    offset = (page - 1) * page_size
    leads, total = await LeadStore.list_all(
        platform=platform, status=status, min_score=min_score,
        start_time=start_time, end_time=end_time,
        limit=page_size, offset=offset,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "leads": [
            {
                "id": l.id,
                "platform": l.platform,
                "author_id": l.author_id,
                "author_name": l.author_name,
                "first_comment_content": l.first_comment_content,
                "lead_score": l.lead_score,
                "status": l.status,
                "tags": l.tags,
                "notes": l.notes,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in leads
        ],
    }


@router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, status: str):
    """更新潜客状态"""
    lead = await LeadStore.get(lead_id)
    if not lead:
        raise HTTPException(404, "潜客不存在")
    ok = await LeadStore.update_status(lead_id, status)
    return {"ok": ok, "old": lead.status, "new": status}


@router.get("/leads/export")
async def export_leads(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    min_score: float = 0.0,
):
    """导出潜客CSV"""
    leads, _ = await LeadStore.list_all(
        platform=platform, status=status, min_score=min_score, limit=10000,
    )
    if not leads:
        raise HTTPException(404, "无潜客数据")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "平台", "用户ID", "昵称", "评分", "状态", "首条评论", "创建时间"])
    for l in leads:
        writer.writerow([
            l.id, l.platform, l.author_id, l.author_name,
            l.lead_score, l.status, (l.first_comment_content or "")[:50],
            l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


# ═══════════ 分析日志 ═══════════

@router.get("/logs")
async def list_logs(
    platform: Optional[str] = None,
    intent: Optional[str] = None,
    author_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """分析日志 — 支持平台/意图/用户/时间筛选"""
    offset = (page - 1) * page_size
    logs, total = await AnalysisLogStore.list_all(
        platform=platform, intent=intent, author_name=author_name,
        start_time=start_time, end_time=end_time,
        limit=page_size, offset=offset,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": [
            {
                "id": l.id,
                "platform": l.platform,
                "comment_id": l.comment_id,
                "comment_content": l.comment_content,
                "author_name": l.author_name,
                "post_title": l.post_title,
                "score": l.score,
                "intent": l.intent,
                "urgency": l.urgency,
                "keywords": l.keywords,
                "reply_content": l.reply_content,
                "replied": l.replied,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# ═══════════ 回复日志 ═══════════

@router.get("/replies")
async def list_replies(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """回复日志"""
    offset = (page - 1) * page_size
    logs, total = await ReplyLogStore.list_all(
        platform=platform, status=status,
        limit=page_size, offset=offset,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "replies": [
            {
                "id": l.id,
                "platform": l.platform,
                "comment_id": l.comment_id,
                "reply_content": l.reply_content,
                "status": l.status,
                "error_msg": l.error_msg,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# ═══════════ 统计 ═══════════

@router.get("/stats/overview")
async def stats_overview():
    """总览统计"""
    return await StatsStore.overview()


@router.get("/stats/by-platform")
async def stats_by_platform():
    """按平台统计"""
    return await StatsStore.by_platform()


@router.get("/stats/by-intent")
async def stats_by_intent():
    """按意图统计"""
    return await StatsStore.by_intent()


@router.get("/stats/trend")
async def stats_trend(days: int = Query(7, ge=1, le=30)):
    """趋势统计"""
    return await StatsStore.daily_trend(days)


# ═══════════ 演示 ═══════════

@router.post("/demo/run")
async def demo_run():
    """演示模式 — mock 数据跑完整流程"""
    from src.monitors.douyin_monitor import MOCK_COMMENTS
    from src.analyzers.intent_analyzer import IntentAnalyzer
    from src.repliers.reply_generator import ReplyGenerator

    logger.info("Demo 开始")
    analyzer = IntentAnalyzer()
    replier = ReplyGenerator()
    results = []

    # 确保有演示账号
    accounts = await AccountStore.list_all(platform="douyin")
    if not accounts:
        acc = await AccountStore.create({
            "platform": "douyin", "account_id": "demo_001",
            "account_name": "演示抖音号", "status": "active",
        })
        account_id = acc.id
    else:
        account_id = accounts[0].id

    for comment in MOCK_COMMENTS:
        score = await analyzer.analyze(comment)
        reply = ""
        if score.score >= 0.5:
            reply = await replier.generate(comment, score)

        # 存分析日志
        await AnalysisLogStore.save({
            "platform_account_id": account_id,
            "platform": comment.platform.value,
            "comment_id": comment.id,
            "comment_content": comment.content,
            "author_id": comment.author_id,
            "author_name": comment.author_name,
            "post_id": comment.post_id,
            "post_title": comment.post_title,
            "score": score.score,
            "intent": score.intent,
            "urgency": score.urgency,
            "keywords": json.dumps(score.keywords),
            "reply_content": reply,
            "replied": bool(reply),
        })

        # 高意向存潜客
        if score.score >= 0.5:
            await LeadStore.save({
                "platform_account_id": account_id,
                "platform": comment.platform.value,
                "author_id": comment.author_id,
                "author_name": comment.author_name,
                "first_comment_content": comment.content,
                "lead_score": score.score,
                "tags": json.dumps(score.keywords),
            })

        results.append({
            "comment": comment.content,
            "author": comment.author_name,
            "score": score.score,
            "intent": score.intent,
            "urgency": score.urgency,
            "keywords": score.keywords,
            "reply": reply,
            "is_lead": score.score >= 0.5,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    leads_n = sum(1 for r in results if r["is_lead"])
    replies_n = sum(1 for r in results if r["reply"])

    return {
        "total_comments": len(MOCK_COMMENTS),
        "leads_found": leads_n,
        "replies_generated": replies_n,
        "results": results,
    }


# ═══════════ 视频生产 (MoneyPrinterTurbo) ═══════════

@router.get("/producer/status")
async def producer_status():
    """检查 MoneyPrinterTurbo 服务状态"""
    from src.producers.video_producer import video_producer
    healthy = await video_producer.health_check()
    return {"ok": healthy, "base_url": video_producer.base_url}


@router.post("/producer/generate")
async def producer_generate(data: dict):
    """从评论关键词生成视频

    Body: { "topic": "...", "keywords": [...], "script": "...", "aspect": "9:16" }
    """
    from src.producers.video_producer import video_producer, VideoRequest

    topic = data.get("topic", "")
    keywords = data.get("keywords", [])
    script = data.get("script", "")
    aspect = data.get("aspect", "9:16")

    if not topic:
        raise HTTPException(400, "topic 不能为空")

    task = await video_producer.produce_from_comments(
        topic=topic,
        keywords=keywords,
        script=script,
        aspect=aspect,
    )

    return {
        "ok": task.status == "completed",
        "task_id": task.task_id,
        "status": task.status,
        "video_url": task.video_url,
        "error": task.error,
    }


@router.get("/producer/task/{task_id}")
async def producer_task_status(task_id: str):
    """查询视频生成任务状态"""
    from src.producers.video_producer import video_producer
    task = await video_producer.query_task(task_id)
    return {
        "task_id": task.task_id,
        "status": task.status,
        "video_url": task.video_url,
        "error": task.error,
    }


# ═══════════ 内容摄入 (MarkItDown) ═══════════

@router.post("/ingest/file")
async def ingest_file(data: dict):
    """摄入单个文件 → Markdown

    Body: { "file_path": "...", "title": "...", "save_to_obsidian": true }
    """
    from src.ingestors.content_ingestor import content_ingestor
    from config.settings import settings

    file_path = data.get("file_path", "")
    title = data.get("title", "")
    save_to_obsidian = data.get("save_to_obsidian", settings.obsidian_auto_save)

    if not file_path:
        raise HTTPException(400, "file_path 不能为空")

    if save_to_obsidian:
        result = content_ingestor.ingest_to_obsidian(
            file_path=file_path,
            vault_path=settings.obsidian_vault_path,
            title=title,
        )
    else:
        result = content_ingestor.ingest_file(file_path, title)

    return {
        "ok": result.success,
        "title": result.title,
        "markdown_length": len(result.markdown),
        "error": result.error,
    }


@router.post("/ingest/directory")
async def ingest_directory(data: dict):
    """批量摄入目录文件

    Body: { "dir_path": "...", "extensions": [".pdf", ".docx"], "save_to_obsidian": true }
    """
    from src.ingestors.content_ingestor import content_ingestor
    from config.settings import settings

    dir_path = data.get("dir_path", "")
    extensions = data.get("extensions")
    save_to_obsidian = data.get("save_to_obsidian", settings.obsidian_auto_save)

    if not dir_path:
        raise HTTPException(400, "dir_path 不能为空")

    results = content_ingestor.ingest_directory(dir_path, extensions)

    if save_to_obsidian:
        for r in results:
            if r.success:
                content_ingestor.ingest_to_obsidian(
                    file_path=r.source_path,
                    vault_path=settings.obsidian_vault_path,
                    title=r.title,
                )

    return {
        "ok": True,
        "total": len(results),
        "success": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "files": [{"path": r.source_path, "title": r.title, "ok": r.success} for r in results],
    }


@router.post("/ingest/url")
async def ingest_url(data: dict):
    """摄入 URL 内容（YouTube / 网页）

    Body: { "url": "...", "save_to_obsidian": true }
    """
    from src.ingestors.content_ingestor import content_ingestor
    from config.settings import settings

    url = data.get("url", "")
    save_to_obsidian = data.get("save_to_obsidian", settings.obsidian_auto_save)

    if not url:
        raise HTTPException(400, "url 不能为空")

    result = content_ingestor.ingest_url(url)

    if save_to_obsidian and result.success:
        content_ingestor.ingest_to_obsidian(
            file_path=url,
            vault_path=settings.obsidian_vault_path,
            title=result.title,
        )

    return {
        "ok": result.success,
        "title": result.title,
        "markdown_length": len(result.markdown),
        "error": result.error,
    }
