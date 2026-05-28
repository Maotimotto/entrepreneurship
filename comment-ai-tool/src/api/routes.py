"""API路由 — 管理后台接口"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from src.models.comment import Comment, LeadScore, Lead, Platform

router = APIRouter(prefix="/api/v1")

# 内存存储 (MVP)
leads_db: dict[str, Lead] = {}
scores_db: dict[str, LeadScore] = {}


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0-mvp"}


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
    return {"total": len(results), "leads": [l.model_dump() for l in results]}


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
    leads_db[lead_id].status = status
    return {"ok": True}


@router.post("/analyze")
async def analyze_comment(comment: Comment):
    """手动分析单条评论"""
    from src.analyzers.intent_analyzer import IntentAnalyzer
    analyzer = IntentAnalyzer()
    score = await analyzer.analyze(comment)
    scores_db[comment.id] = score
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

    analyzer = IntentAnalyzer()
    replier = ReplyGenerator()
    results = []

    for comment in MOCK_COMMENTS:
        score = await analyzer.analyze(comment)
        scores_db[comment.id] = score

        reply = ""
        if score.score >= 0.6:
            reply = await replier.generate(comment, score)

        # 高分评论自动建档为潜客
        if score.score >= 0.5:
            lead = Lead(
                id=f"lead_{comment.id}",
                platform=comment.platform,
                author_id=comment.author_id,
                author_name=comment.author_name,
                first_comment_id=comment.id,
                lead_score=score.score,
                tags=score.keywords,
            )
            leads_db[lead.id] = lead

        results.append({
            "comment": comment.content,
            "author": comment.author_name,
            "score": score.score,
            "intent": score.intent,
            "reply": reply,
            "is_lead": score.score >= 0.5,
        })

    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "total_comments": len(MOCK_COMMENTS),
        "leads_found": sum(1 for r in results if r["is_lead"]),
        "results": results,
    }
