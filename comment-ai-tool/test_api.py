#!/usr/bin/env python3
"""API 集成测试 — 覆盖全部端点和场景"""
import sys
import asyncio
sys.path.insert(0, '.')

from httpx import AsyncClient, ASGITransport
from src.main import app

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


async def test_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:

        # === 基础端点 ===
        print("\n📡 基础端点")
        r = await c.get("/")
        check("GET / 返回页面", r.status_code == 200 and "评论" in r.text)

        r = await c.get("/api/v1/health")
        check("GET /health", r.status_code == 200 and r.json()["status"] == "ok")

        # === Demo 全链路 ===
        print("\n🎬 Demo 全链路")
        r = await c.post("/api/v1/demo/run")
        check("POST /demo/run 200", r.status_code == 200)
        d = r.json()
        check("评论数=10", d["total_comments"] == 10, f"got {d['total_comments']}")
        check("潜客数>=3", d["leads_found"] >= 3, f"got {d['leads_found']}")
        check("回复数>=3", d["replies_generated"] >= 3, f"got {d['replies_generated']}")
        check("结果已排序", d["results"][0]["score"] >= d["results"][-1]["score"])

        # 验证高意向评论被正确识别
        high_scores = [r for r in d["results"] if r["score"] >= 0.7]
        check("高意向评论>=2", len(high_scores) >= 2)
        for h in high_scores[:2]:
            check(f"  {h['author']}有回复", len(h["reply"]) > 0)

        # 验证低意向评论
        low_scores = [r for r in d["results"] if r["score"] < 0.4]
        check("低意向评论>=2", len(low_scores) >= 2)

        # 验证结果字段完整性
        first = d["results"][0]
        for key in ["comment", "author", "score", "intent", "urgency", "keywords", "reply", "is_lead"]:
            check(f"字段 {key} 存在", key in first)

        # === 潜客管理 ===
        print("\n👤 潜客管理")
        r = await c.get("/api/v1/leads")
        check("GET /leads", r.status_code == 200)
        leads = r.json()
        check("潜客数匹配", leads["total"] == d["leads_found"])

        if leads["total"] > 0:
            lid = leads["leads"][0]["id"]
            r = await c.get(f"/api/v1/leads/{lid}")
            check("GET /leads/:id", r.status_code == 200)

            r = await c.put(f"/api/v1/leads/{lid}/status?status=contacted")
            check("PUT /leads/:id/status", r.status_code == 200)

        r = await c.get("/api/v1/leads/nonexistent")
        check("GET /leads/404", r.status_code == 404)

        # === 手动分析 ===
        print("\n🔍 手动分析")
        r = await c.post("/api/v1/analyze", json={
            "id": "manual_001", "platform": "douyin",
            "content": "想学这个，多少钱？有课程吗",
            "author_id": "u_m", "author_name": "手动测试",
            "post_id": "p1", "post_title": "AI教程",
        })
        check("POST /analyze 200", r.status_code == 200)
        s = r.json()
        check("score>=0.7", s["score"] >= 0.7, f"got {s['score']}")
        check("intent=potential_lead", s["intent"] == "potential_lead")
        check("识别关键词", len(s["keywords"]) >= 1)

        # 负面测试
        r = await c.post("/api/v1/analyze", json={
            "id": "manual_002", "platform": "douyin",
            "content": "哈哈哈哈笑死我了",
            "author_id": "u_m2", "author_name": "测试2",
            "post_id": "p1", "post_title": "AI教程",
        })
        check("负面: score<0.4", r.json()["score"] < 0.4)

    # === 汇总 ===
    print(f"\n{'='*40}")
    print(f"📊 结果: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


asyncio.run(test_api())
