#!/usr/bin/env python3
"""API集成测试 — 使用SQLite内存数据库"""
import sys
import os
import asyncio

# 覆盖为 SQLite 内存数据库（测试用）
os.environ["DB_URL"] = "sqlite+aiosqlite:///:memory:"

sys.path.insert(0, '.')

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
    from httpx import AsyncClient, ASGITransport
    from src.core.database import init_db
    from src.main import app

    # 初始化数据库
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:

        # === 健康检查 ===
        print("\n📡 基础端点")
        r = await c.get("/")
        check("GET / 返回页面", r.status_code == 200 and "评论" in r.text)

        r = await c.get("/api/v1/health")
        check("GET /health", r.status_code == 200 and r.json()["status"] == "ok")

        # === 账号管理 ===
        print("\n📱 平台账号管理")

        # 创建抖音账号
        r = await c.post("/api/v1/accounts", json={
            "platform": "douyin", "account_id": "dy_001",
            "account_name": "测试抖音号", "remark": "运营测试",
        })
        check("POST /accounts 抖音", r.status_code == 200)
        dy_id = r.json()["id"]

        # 创建B站账号
        r = await c.post("/api/v1/accounts", json={
            "platform": "bilibili", "account_id": "bili_001",
            "account_name": "测试B站号",
        })
        check("POST /accounts B站", r.status_code == 200)
        bili_id = r.json()["id"]

        # 创建小红书账号
        r = await c.post("/api/v1/accounts", json={
            "platform": "xiaohongshu", "account_id": "xhs_001",
            "account_name": "测试小红书号",
        })
        check("POST /accounts 小红书", r.status_code == 200)

        # 创建视频号账号
        r = await c.post("/api/v1/accounts", json={
            "platform": "wechat_video", "account_id": "wx_001",
            "account_name": "测试视频号",
        })
        check("POST /accounts 视频号", r.status_code == 200)

        # 列表
        r = await c.get("/api/v1/accounts")
        check("GET /accounts 全部", r.json()["total"] == 4)

        # 按平台筛选
        r = await c.get("/api/v1/accounts?platform=douyin")
        check("GET /accounts?platform=douyin", r.json()["total"] == 1)

        # 更新
        r = await c.put(f"/api/v1/accounts/{dy_id}", json={"remark": "已更新"})
        check("PUT /accounts/:id", r.json()["ok"])

        # 获取单个
        r = await c.get(f"/api/v1/accounts/{dy_id}")
        check("GET /accounts/:id", r.json()["remark"] == "已更新")

        # 删除
        r = await c.delete(f"/api/v1/accounts/{bili_id}")
        check("DELETE /accounts/:id", r.json()["ok"])

        r = await c.get("/api/v1/accounts")
        check("删除后数量=3", r.json()["total"] == 3)

        # === 演示 ===
        print("\n🎬 Demo 全链路")
        r = await c.post("/api/v1/demo/run")
        check("POST /demo/run 200", r.status_code == 200)
        d = r.json()
        check("评论数=10", d["total_comments"] == 10, f"got {d['total_comments']}")
        check("潜客数>=3", d["leads_found"] >= 3, f"got {d['leads_found']}")
        check("回复数>=3", d["replies_generated"] >= 3, f"got {d['replies_generated']}")
        check("结果已排序", d["results"][0]["score"] >= d["results"][-1]["score"])

        # === 潜客管理 ===
        print("\n👤 潜客管理")
        r = await c.get("/api/v1/leads")
        check("GET /leads", r.status_code == 200)
        leads = r.json()
        check("潜客数匹配", leads["total"] == d["leads_found"])

        # 按平台筛选
        r = await c.get("/api/v1/leads?platform=douyin")
        check("GET /leads?platform=douyin", r.json()["total"] == d["leads_found"])

        # 按评分筛选
        r = await c.get("/api/v1/leads?min_score=0.7")
        high = r.json()
        check("GET /leads?min_score=0.7", high["total"] >= 2)
        for l in high["leads"]:
            check(f"  {l['author_name']} score>=0.7", l["lead_score"] >= 0.7)

        # 更新状态
        if leads["total"] > 0:
            lid = leads["leads"][0]["id"]
            r = await c.put(f"/api/v1/leads/{lid}/status?status=contacted")
            check("PUT /leads/:id/status", r.json()["ok"])

        # 导出CSV
        r = await c.get("/api/v1/leads/export")
        check("GET /leads/export CSV", r.status_code == 200 and "text/csv" in r.headers["content-type"])

        # === 分析日志 ===
        print("\n📋 分析日志")
        r = await c.get("/api/v1/logs")
        check("GET /logs", r.status_code == 200)
        logs = r.json()
        check("日志数>=10", logs["total"] >= 10)

        # 按意图筛选
        r = await c.get("/api/v1/logs?intent=potential_lead")
        check("GET /logs?intent=potential_lead", r.json()["total"] >= 2)

        # 按用户搜索
        r = await c.get("/api/v1/logs?author_name=科技")
        check("GET /logs?author_name=科技", r.json()["total"] >= 1)

        # === 统计 ===
        print("\n📊 统计接口")
        r = await c.get("/api/v1/stats/overview")
        check("GET /stats/overview", r.status_code == 200)
        ov = r.json()
        check("accounts>=3", ov["accounts"] >= 3)
        check("leads>=3", ov["leads"] >= 3)
        check("analyzed>=10", ov["analyzed"] >= 10)

        r = await c.get("/api/v1/stats/by-platform")
        check("GET /stats/by-platform", r.status_code == 200 and len(r.json()) >= 1)

        r = await c.get("/api/v1/stats/by-intent")
        check("GET /stats/by-intent", r.status_code == 200 and len(r.json()) >= 1)

        r = await c.get("/api/v1/stats/trend")
        check("GET /stats/trend", r.status_code == 200)

    print(f"\n{'='*40}")
    print(f"📊 结果: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


asyncio.run(test_api())
