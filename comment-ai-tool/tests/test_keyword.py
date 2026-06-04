#!/usr/bin/env python3
"""关键词引擎测试 — 验证同义词、否定词、情感分析"""
import sys
sys.path.insert(0, '.')

from src.analyzers.keyword_engine import keyword_engine

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


def test_keyword_engine():
    print("\n🧪 高意向同义词")
    cases = [
        ("怎么买", "buy", 0.95),
        ("价格多少", "price", 0.85),
        ("想学这个", "learn", 0.90),
        ("加微信聊聊", "contact", 0.88),
        ("求合作", "cooperate", 0.92),
        ("在哪里购买", "buy", 0.95),
        ("收费吗", "price", 0.85),
        ("有教程吗", "learn", 0.90),
    ]
    for text, expected_group, min_score in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text}' → {expected_group} (score={result.score})", 
              result.score >= min_score and result.intent == "potential_lead",
              f"score={result.score}, intent={result.intent}")

    print("\n🧪 中意向同义词")
    cases = [
        ("太棒了", "positive", 0.4),
        ("收藏了", "collect", 0.45),
        ("已关注", "follow", 0.35),
        ("干货满满", "positive", 0.4),
    ]
    for text, expected_group, min_score in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text}' → {expected_group} (score={result.score})", 
              result.score >= min_score and result.intent == "inquiry",
              f"score={result.score}, intent={result.intent}")

    print("\n🧪 低意向/垃圾")
    cases = [
        ("互赞互关", "spam", 0.1),
        ("哈哈哈哈", "laugh", 0.15),
        ("666666", "laugh", 0.15),
        ("第一", "spam", 0.1),
    ]
    for text, expected_group, max_score in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text}' → {expected_group} (score={result.score})", 
              result.score <= max_score,
              f"score={result.score}")

    print("\n🧪 否定词处理")
    cases = [
        ("不想学", 0.3),
        ("不买", 0.3),
        ("没兴趣", 0.3),
        ("不要", 0.3),
    ]
    for text, max_score in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text}' 否定 (score={result.score})", 
              result.score <= max_score,
              f"score={result.score}")

    print("\n🧪 混合意图")
    cases = [
        ("价格多少？666", 0.6, "高+低混合"),
        ("太棒了想学", 0.5, "中+高混合"),
        ("哈哈多少钱", 0.5, "低+高混合"),
    ]
    for text, min_score, desc in cases:
        result = keyword_engine.analyze(text)
        check(f"{desc}: '{text}' (score={result.score})", 
              result.score >= min_score,
              f"score={result.score}")

    print("\n🧪 情感分析")
    cases = [
        ("太棒了", "positive"),
        ("互赞", "negative"),
        ("今天星期一", "neutral"),
        ("12345", "neutral"),
    ]
    for text, expected_sentiment in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text}' → {result.sentiment}", 
              result.sentiment == expected_sentiment,
              f"got {result.sentiment}")

    print("\n🧪 边界情况")
    cases = [
        ("", 0.0, "neutral"),
        ("   ", 0.0, "neutral"),
        ("@#$%", 0.1, "neutral"),
    ]
    for text, max_score, expected_intent in cases:
        result = keyword_engine.analyze(text)
        check(f"'{text[:10]}' → {expected_intent}", 
              result.score <= max_score and result.intent == expected_intent,
              f"score={result.score}, intent={result.intent}")

    print(f"\n{'='*40}")
    print(f"📊 关键词引擎测试: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_KEYWORD_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


test_keyword_engine()
