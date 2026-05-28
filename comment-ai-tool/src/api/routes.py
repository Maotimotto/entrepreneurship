"""API路由 — 管理后台接口"""
import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from src.models.comment import Comment, LeadScore, Lead, Platform
from src.core.logger import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

# 内存存储 (MVP)
leads_db: dict[str, Lead] = {}
scores_db: dict[str, LeadScore] = {}


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.2"}


@router.get("/leads")
async def list_leads(
    status: Optional[str] = None,
    min_score: float = 0.0,
    platform: Optional[str] = None,
):
    """获取潜客列表"""
    results = list(leads_db.values())
    if status:
        results = [l for l in results if l.status == status]
    results = [l for l in results if l.lead_score >= min_score]
    if platform:
        results = [l for l in results if l.platform.value == platform]
    results.sort(key=lambda x: x.lead_score, reverse=True)
    return {"total": len(results), "leads": [l.model_dump() for l in results]}


@router.get("/leads/export")
async def export_leads():
    """导出潜客为CSV"""
    if not leads_db:
        raise HTTPException(404, "无潜客数据")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "平台", "用户ID", "昵称", "评分", "状态", "标签", "创建时间"])
    for lead in sorted(leads_db.values(), key=lambda x: x.lead_score, reverse=True):
        writer.writerow([
            lead.id, lead.platform.value, lead.author_id, lead.author_name,
            lead.lead_score, lead.status, ",".join(lead.tags),
            lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """获取单个潜客详情"""
    if lead_id not in leads_db:
        raise HTTPException(404, "潜客不存在")
    return leads_db[lead_id].model_dump()


@router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str):
    """更新潜客状态"""
    if lead_id not in leads_db:
        raise HTTPException(404, "潜客不存在")
    old = leads_db[lead_id].status
    leads_db[lead_id].status = status
    leads_db[lead_id].updated_at = datetime.now()
    logger.info(f"潜客状态更新: {lead_id} {old} → {status}")
    return {"ok": True, "old": old, "new": status}


@router.post("/analyze")
async def analyze_comment(comment: Comment):
    """手动分析单条评论"""
    from src.analyzers.intent_analyzer import IntentAnalyzer
    analyzer = IntentAnalyzer()
    score = await analyzer.analyze(comment)
    scores_db[comment.id] = score
    logger.info(f"评论分析: [{score.score:.2f}] {comment.author_name}: {comment.content[:30]}")
    return score.model_dump()


@router.post("/demo/run")
async def demo_run():
    """
    演示模式 — 用模拟数据跑完整流程
    评论采集 → AI分析 → 评分 → 生成回复
    """
    from src.monitors.douyin_monitor import MOCK_COMMENTS
    from src.analyzers.intent_analyzer import IntentAnalyzer
    from src.repliers.reply_generator import ReplyGenerator

    leads_db.clear()
    logger.info("Demo 开始 — 清空旧数据")

    analyzer = IntentAnalyzer()
    replier = ReplyGenerator()
    results = []

    for comment in MOCK_COMMENTS:
        score = await analyzer.analyze(comment)
        scores_db[comment.id] = score

        reply = ""
        if score.score >= 0.5:
            reply = await replier.generate(comment, score)

        if score.score >= 0.5:
            lead = Lead(
                id=f"lead_{comment.id}",
                platform=comment.platform,
                author_id=comment.author_id,
                author_name=comment.author_name,
                first_comment_id=comment.id,
                lead_score=score.score,
                tags=score.keywords,
                created_at=datetime.now(),
            )
            leads_db[lead.id] = lead

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
    logger.info(f"Demo 完成 — {len(results)}条评论, {leads_n}个潜客, {replies_n}条回复")

    return {
        "total_comments": len(MOCK_COMMENTS),
        "leads_found": leads_n,
        "replies_generated": replies_n,
        "results": results,
    }


@router.get("/stats")
async def get_stats():
    """统计数据"""
    total_leads = len(leads_db)
    by_status = {}
    by_score = {"high": 0, "medium": 0, "low": 0}

    for lead in leads_db.values():
        by_status[lead.status] = by_status.get(lead.status, 0) + 1
        if lead.lead_score >= 0.7:
            by_score["high"] += 1
        elif lead.lead_score >= 0.4:
            by_score["medium"] += 1
        else:
            by_score["low"] += 1

    return {
        "total_comments_analyzed": len(scores_db),
        "total_leads": total_leads,
        "by_status": by_status,
        "by_score_level": by_score,
    }
