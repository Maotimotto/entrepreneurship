#!/usr/bin/env python3
"""边界测试 — 覆盖极端场景和异常输入"""
import sys
import asyncio
sys.path.insert(0, '.')

from httpx import AsyncClient, ASGITransport
from src.main import app
from src.models.comment import Comment, Platform
from src.analyzers.intent_analyzer import IntentAnalyzer

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


async def test_edge_cases():
    analyzer = IntentAnalyzer()

    # === 空内容 ===
    print("\n🧪 空内容")
    c = Comment(id="e1", platform=Platform.DOUYIN, content="", author_id="u", author_name="n", post_id="p", post_title="t")
    s = await analyzer.analyze(c)
    check("空评论 score<=0.2", s.score <= 0.2, f"got {s.score}")

    # === 超长内容 ===
    print("\n🧪 超长内容")
    c = Comment(id="e2", platform=Platform.DOUYIN, content="想学" * 200, author_id="u", author_name="n", post_id="p", post_title="t")
    s = await analyzer.analyze(c)
    check("超长评论不崩溃", s.score >= 0)  # 只要不报错就行

    # === 特殊字符 ===
    print("\n🧪 特殊字符")
    for text in ["@#$%^&*", "🎉🎉🎉", "1234567890", "   ", "\n\n\n"]:
        c = Comment(id=f"e_{text[:3]}", platform=Platform.DOUYIN, content=text, author_id="u", author_name="n", post_id="p", post_title="t")
        s = await analyzer.analyze(c)
        check(f"特殊字符 '{text[:10]}' 不崩溃", s.score >= 0, f"score={s.score}")

    # === 混合意图 ===
    print("\n🧪 混合意图")
    cases = [
        ("价格多少？666", 0.6, "高意向+垃圾混合"),
        ("太棒了想学", 0.5, "中+高混合"),
        ("哈哈多少钱", 0.5, "低+高混合"),
    ]
    for text, min_score, desc in cases:
        c = Comment(id=f"m_{desc}", platform=Platform.DOUYIN, content=text, author_id="u", author_name="n", post_id="p", post_title="t")
        s = await analyzer.analyze(c)
        check(f"{desc}: score>={min_score}", s.score >= min_score, f"got {s.score}")

    # === 不同平台 ===
    print("\n🧪 不同平台")
    for platform in [Platform.DOUYIN, Platform.XIAOHONGSHU, Platform.WECHAT_VIDEO]:
        c = Comment(id=f"p_{platform.value}", platform=platform, content="想学这个", author_id="u", author_name="n", post_id="p", post_title="t")
        s = await analyzer.analyze(c)
        check(f"{platform.value} 平台正常", s.score > 0)

    # === API 边界 ===
    print("\n🧪 API 边界")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 缺失字段
        r = await client.post("/api/v1/analyze", json={"id": "bad"})
        check("缺失字段返回422", r.status_code == 422, f"got {r.status_code}")

        # 空 body
        r = await client.post("/api/v1/analyze", content="{}", headers={"content-type": "application/json"})
        check("空body返回422", r.status_code == 422)

    # === 汇总 ===
    print(f"\n{'='*40}")
    print(f"📊 边界测试: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_EDGE_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


asyncio.run(test_edge_cases())
