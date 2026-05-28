#!/usr/bin/env python3
"""Quick smoke test"""
import sys
sys.path.insert(0, '.')

from src.models.comment import Comment, Platform, LeadScore

c = Comment(
    id="test_001",
    platform=Platform.DOUYIN,
    content="这个怎么买？",
    author_id="u1",
    author_name="测试用户",
    post_id="p1",
    post_title="AI工具演示",
)
print(f"✅ Comment: {c.content} | Platform: {c.platform.value}")

score = LeadScore(
    comment_id="test_001",
    score=0.85,
    intent="potential_lead",
    urgency="high",
    keywords=["怎么买"],
    reasoning="明确购买意向",
)
print(f"✅ LeadScore: {score.score} | Intent: {score.intent}")
print("✅ ALL_MODELS_OK")
