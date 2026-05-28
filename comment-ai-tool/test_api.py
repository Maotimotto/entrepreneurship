#!/usr/bin/env python3
"""API 集成测试 — 使用测试数据库"""
import sys
import os
import asyncio
import tempfile

# 使用临时数据库
os.environ["COMMENT_AI_DB"] = os.path.join(tempfile.gettempdir(), "test_comment_ai.db")

sys.path.insert(0, '.')
from httpx import AsyncClient, ASGITransport
from src.core.database import init_db

# 初始化测试数据库
init_db()

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

        print("\n📡 基础端点")
        r = await c.get("/")
        check("GET / 返回页面", r.status_code == 200 and "评论" in r.text)

        r = await c.get("/api/v1/health")
        check("GET /health", r.status_code == 200 and r.json()["status"] == "ok")

        print("\n🎬 Demo 全链路")
        r = await c.post("/api/v1/demo/run")
        check("POST /demo/run 200", r.status_code == 200)
        d = r.json()
        check("评论数=10", d["total_comments"] == 10, f"got {d['total_comments']}")
        check("潜客数>=3", d["leads_found"] >= 3, f"got {d['leads_found']}")
        check("回复数>=3", d["replies_generated"] >= 3, f"got {d['replies_generated']}")
        check("结果已排序", d["results"][0]["score"] >= d["results"][-1]["score"])

        high_scores = [r for r in d["results"] if r["score"] >= 0.7]
        check("高意向>=2", len(high_scores) >= 2)
        for h in high_scores[:2]:
            check(f"  {h['author']}有回复", len(h["reply"]) > 0)

        low_scores = [r for r in d["results"] if r["score"] < 0.4]
        check("低意向>=2", len(low_scores) >= 2)

        first = d["results"][0]
        for key in ["comment", "author", "score", "intent", "urgency", "keywords", "reply", "is_lead"]:
            check(f"字段{key}", key in first)

        print("\n👤 潜客管理 (持久化)")
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

            # 验证持久化
            r = await c.get(f"/api/v1/leads/{lid}")
            check("状态已持久化", r.json()["status"] == "contacted")

        r = await c.get("/api/v1/leads/nonexistent")
        check("GET /leads/404", r.status_code == 404)

        print("\n🔍 手动分析")
        r = await c.post("/api/v1/analyze", json={
            "id": "m1", "platform": "douyin", "content": "想学这个，多少钱？",
            "author_id": "u1", "author_name": "测试", "post_id": "p1", "post_title": "AI",
        })
        check("POST /analyze 200", r.status_code == 200)
        s = r.json()
        check("score>=0.7", s["score"] >= 0.7, f"got {s['score']}")
        check("intent=potential_lead", s["intent"] == "potential_lead")
        check("识别关键词", len(s["keywords"]) >= 1)

        r = await c.post("/api/v1/analyze", json={
            "id": "m2", "platform": "douyin", "content": "哈哈哈哈笑死我了",
            "author_id": "u2", "author_name": "测试2", "post_id": "p1", "post_title": "AI",
        })
        check("负面: score<0.4", r.json()["score"] < 0.4)

        print("\n📊 统计")
        r = await c.get("/api/v1/stats")
        check("GET /stats", r.status_code == 200)
        st = r.json()
        check("total_analyzed>=10", st["total_analyzed"] >= 10)
        check("leads.total>=3", st["leads"]["total"] >= 3)

    print(f"\n{'='*40}")
    print(f"📊 结果: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


asyncio.run(test_api())
