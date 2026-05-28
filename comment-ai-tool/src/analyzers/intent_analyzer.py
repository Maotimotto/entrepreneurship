"""AI意图分析器 — 核心模块：识别评论意图和潜客评分"""
import json
from openai import AsyncOpenAI
from config.settings import settings
from src.models.comment import Comment, LeadScore


INTENT_PROMPT = """你是一个短视频评论分析专家。分析以下评论，判断评论者是否为潜在客户。

评论内容: "{comment}"
作品标题: "{post_title}"
平台: {platform}

请返回JSON格式:
{{
    "intent": "inquiry|complaint|praise|spam|potential_lead|neutral",
    "score": 0.0-1.0,
    "urgency": "high|medium|low",
    "keywords": ["触发关键词"],
    "reasoning": "简短推理说明"
}}

评分标准:
- 1.0: 明确表达购买/学习/合作意向
- 0.7-0.9: 强烈兴趣信号 (询问价格、怎么买、在哪学)
- 0.4-0.6: 潜在兴趣 (点赞、正面评论、关注相关话题)
- 0.0-0.3: 无购买意向 (闲聊、表情、无关评论)

只返回JSON，不要其他内容。"""


class IntentAnalyzer:
    """基于LLM的评论意图分析器"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
        )
        self.model = settings.ai_model

    async def analyze(self, comment: Comment) -> LeadScore:
        """分析单条评论，返回潜客评分"""
        prompt = INTENT_PROMPT.format(
            comment=comment.content,
            post_title=comment.post_title,
            platform=comment.platform.value,
        )

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            result = json.loads(resp.choices[0].message.content)

            return LeadScore(
                comment_id=comment.id,
                score=float(result.get("score", 0)),
                intent=result.get("intent", "neutral"),
                urgency=result.get("urgency", "low"),
                keywords=result.get("keywords", []),
                reasoning=result.get("reasoning", ""),
            )
        except Exception as e:
            # 降级: 关键词匹配
            return self._fallback_score(comment)

    def _fallback_score(self, comment: Comment) -> LeadScore:
        """关键词降级方案 — API不可用时的兜底"""
        high_intent = ["怎么买", "多少钱", "价格", "在哪买", "求链接", "想学", "怎么学",
                       "有课程吗", "加微信", "联系方式", "合作", "代理"]
        medium_intent = ["有用", "收藏", "太棒了", "干货", "厉害", "学到了", "感谢"]

        text = comment.content
        score = 0.1
        intent = "neutral"
        keywords = []

        for kw in high_intent:
            if kw in text:
                score = 0.85
                intent = "potential_lead"
                keywords.append(kw)

        if not keywords:
            for kw in medium_intent:
                if kw in text:
                    score = 0.5
                    intent = "inquiry"
                    keywords.append(kw)

        return LeadScore(
            comment_id=comment.id,
            score=score,
            intent=intent,
            urgency="high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
            keywords=keywords,
            reasoning=f"关键词匹配降级: {keywords}" if keywords else "无匹配关键词",
        )

    async def batch_analyze(self, comments: list[Comment]) -> list[LeadScore]:
        """批量分析评论"""
        results = []
        for comment in comments:
            score = await self.analyze(comment)
            results.append(score)
        return results
