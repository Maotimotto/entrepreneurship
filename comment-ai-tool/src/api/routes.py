"""API路由 — 管理后台接口"""
import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from src.models.comment import Comment, LeadScore, Lead, Platform
from src.core.database import LeadStore, ScoreStore, AnalysisLogStore
from src.core.logger import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.4", "leads": LeadStore.count()}


@router.get("/leads")
async def list_leads(
    status: Optional[str] = None,
    min_score: float = 0.0,
    platform: Optional[str] = None,
):
    """获取潜客列表"""
    results = LeadStore.list_all(status=status, min_score=min_score)
    if platform:
        results = [l for l in results if l.platform.value == platform]
    return {"total": len(results), "leads": [l.model_dump() for l in results]}


@router.get("/leads/export")
async def export_leads():
    """导出潜客为CSV"""
    leads = LeadStore.list_all()
    if not leads:
        raise HTTPException(404, "无潜客数据")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "平台", "用户ID", "昵称", "评分", "状态", "标签", "创建时间"])
    for lead in leads:
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
    lead = LeadStore.get(lead_id)
    if not lead:
        raise HTTPException(404, "潜客不存在")
    return lead.model_dump()


@router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str):
    """更新潜客状态"""
    lead = LeadStore.get(lead_id)
    if not lead:
        raise HTTPException(404, "潜客不存在")
    old = lead.status
    ok = LeadStore.update_status(lead_id, status)
    if ok:
        logger.info(f"潜客状态: {lead_id} {old} → {status}")
    return {"ok": ok, "old": old, "new": status}


@router.post("/analyze")
async def analyze_comment(comment: Comment):
    """手动分析单条评论"""
    from src.analyzers.intent_analyzer import IntentAnalyzer
    analyzer = IntentAnalyzer()
    score = await analyzer.analyze(comment)
    ScoreStore.save(score)
    AnalysisLogStore.log(comment.content, comment.author_name, comment.platform.value,
                         score.score, score.intent, "")
    logger.info(f"分析: [{score.score:.2f}] {comment.author_name}: {comment.content[:30]}")
    return score.model_dump()


@router.post("/demo/run")
async def demo_run():
    """演示模式 — 模拟数据跑完整流程"""
    from src.monitors.douyin_monitor import MOCK_COMMENTS
    from src.analyzers.intent_analyzer import IntentAnalyzer
    from src.repliers.reply_generator import ReplyGenerator

    logger.info("Demo 开始")
    analyzer = IntentAnalyzer()
    replier = ReplyGenerator()
    results = []

    for comment in MOCK_COMMENTS:
        score = await analyzer.analyze(comment)
        ScoreStore.save(score)

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
            LeadStore.save(lead)

        AnalysisLogStore.log(comment.content, comment.author_name, comment.platform.value,
                             score.score, score.intent, reply)

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
    logger.info(f"Demo 完成 — {len(results)}评论, {leads_n}潜客, {replies_n}回复")

    return {
        "total_comments": len(MOCK_COMMENTS),
        "leads_found": leads_n,
        "replies_generated": replies_n,
        "results": results,
    }


@router.get("/stats")
async def get_stats():
    """统计数据"""
    return {
        "total_analyzed": ScoreStore.count(),
        "leads": LeadStore.stats(),
    }
