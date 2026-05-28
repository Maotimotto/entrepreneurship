#!/usr/bin/env python3
"""情感分析测试"""
import sys
sys.path.insert(0, '.')

from src.analyzers.sentiment import sentiment_analyzer, Sentiment

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


def test_sentiment():
    print("\n🧪 正面情感")
    cases = [
        ("太棒了", Sentiment.POSITIVE),
        ("厉害", Sentiment.POSITIVE),
        ("干货满满", Sentiment.POSITIVE),
        ("感谢分享", Sentiment.POSITIVE),
        ("想学这个", Sentiment.POSITIVE),
    ]
    for text, expected in cases:
        result = sentiment_analyzer.analyze(text)
        check(f"'{text}' → {expected.value}", result.sentiment == expected,
              f"got {result.sentiment.value}")

    print("\n🧪 负面情感")
    cases = [
        ("垃圾", Sentiment.NEGATIVE),
        ("骗人的", Sentiment.NEGATIVE),
        ("割韭菜", Sentiment.NEGATIVE),
    ]
    for text, expected in cases:
        result = sentiment_analyzer.analyze(text)
        check(f"'{text}' → {expected.value}", result.sentiment == expected,
              f"got {result.sentiment.value}")

    print("\n🧪 中性情感")
    cases = [
        ("今天星期一", Sentiment.NEUTRAL),
        ("12345", Sentiment.NEUTRAL),
        ("@#$%", Sentiment.NEUTRAL),
    ]
    for text, expected in cases:
        result = sentiment_analyzer.analyze(text)
        check(f"'{text}' → {expected.value}", result.sentiment == expected,
              f"got {result.sentiment.value}")

    print("\n🧪 混合/复杂情感")
    # "互赞互关" 包含负面词(互粉)和中性词(互赞互关)，可能是mixed
    result = sentiment_analyzer.analyze("互赞互关")
    check("'互赞互关' → negative或mixed", result.sentiment in [Sentiment.NEGATIVE, Sentiment.MIXED],
          f"got {result.sentiment.value}")

    # "还不错但是有点贵" — "不错"正面，"贵"可能是中性描述
    result = sentiment_analyzer.analyze("还不错但是有点贵")
    check("'还不错但是有点贵' → positive或mixed", result.sentiment in [Sentiment.POSITIVE, Sentiment.MIXED],
          f"got {result.sentiment.value}")

    print("\n🧪 空内容")
    result = sentiment_analyzer.analyze("")
    check("空字符串 → neutral", result.sentiment == Sentiment.NEUTRAL)
    result = sentiment_analyzer.analyze("   ")
    check("空格 → neutral", result.sentiment == Sentiment.NEUTRAL)

    print("\n🧪 置信度")
    result = sentiment_analyzer.analyze("太棒了")
    check("强正面 置信度>0.7", result.confidence > 0.7, f"got {result.confidence}")
    result = sentiment_analyzer.analyze("垃圾")
    check("强负面 置信度>0.7", result.confidence > 0.7, f"got {result.confidence}")

    print(f"\n{'='*40}")
    print(f"📊 情感分析测试: {PASS} 通过, {FAIL} 失败")
    if FAIL == 0:
        print("🎉 ALL_SENTIMENT_TESTS_PASSED")
    else:
        print("⚠️  有测试失败")
        sys.exit(1)


test_sentiment()
