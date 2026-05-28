#!/usr/bin/env python3
"""API 集成测试 — 验证所有端点"""
import sys
import asyncio

sys.path.insert(0, '.')

from httpx import AsyncClient, ASGITransport
from src.main import app


async def test_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root
        r = await client.get("/")
        assert r.status_code == 200
        d = r.json()
        print(f"✅ GET / → {d['name']} v{d['version']}")

        # 2. Health
        r = await client.get("/api/v1/health")
        assert r.status_code == 200
        print(f"✅ GET /api/v1/health → {r.json()['status']}")

        # 3. Demo run — 核心链路
        r = await client.post("/api/v1/demo/run")
        assert r.status_code == 200
        result = r.json()
        assert result["total_comments"] == 5
        print(f"✅ POST /api/v1/demo/run → {result['total_comments']}条评论, {result['leads_found']}个潜客")
        for item in result["results"]:
            icon = "🔥" if item["score"] >= 0.7 else "👀" if item["score"] >= 0.5 else "💤"
            print(f"   {icon} [{item['score']:.2f}] {item['author']}: {item['comment'][:35]}")
            if item["reply"]:
                print(f"      💬 {item['reply']}")

        # 4. Leads list
        r = await client.get("/api/v1/leads")
        assert r.status_code == 200
        leads = r.json()
        print(f"✅ GET /api/v1/leads → {leads['total']}个潜客")

        # 5. Single analyze (keyword fallback)
        r = await client.post("/api/v1/analyze", json={
            "id": "manual_001",
            "platform": "douyin",
            "content": "想学这个技术，有教程吗？多少钱？",
            "author_id": "u_manual",
            "author_name": "手动测试",
            "post_id": "p1",
            "post_title": "AI自动化教程",
        })
        assert r.status_code == 200
        s = r.json()
        print(f"✅ POST /api/v1/analyze → score={s['score']}, intent={s['intent']}, keywords={s['keywords']}")

    print("\n🎉 ALL_API_TESTS_PASSED")


asyncio.run(test_api())
