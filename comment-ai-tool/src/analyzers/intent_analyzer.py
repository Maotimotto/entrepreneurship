"""AI意图分析器 — 核心模块：识别评论意图和潜客评分"""
import json
import logging
from openai import AsyncOpenAI
from config.settings import settings
from src.models.comment import Comment, LeadScore
from src.analyzers.keyword_engine import keyword_engine

logger = logging.getLogger(__name__)

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
    """基于LLM的评论意图分析器，无API key时使用增强关键词引擎"""

    def __init__(self):
        self._has_api_key = bool(settings.ai_api_key and settings.ai_api_key != "your-api-key")
        if self._has_api_key:
            self.client = AsyncOpenAI(
                api_key=settings.ai_api_key,
                base_url=settings.ai_base_url,
            )
            self.model = settings.ai_model
            logger.info(f"IntentAnalyzer: LLM模式 ({settings.ai_provider}/{self.model})")
        else:
            self.client = None
            logger.info("IntentAnalyzer: 增强关键词模式 (未配置AI API Key)")

    async def analyze(self, comment: Comment) -> LeadScore:
        """分析单条评论，返回潜客评分"""
        if not self._has_api_key:
            return self._keyword_score(comment)

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
            logger.warning(f"LLM调用失败，降级为关键词: {e}")
            return self._keyword_score(comment)

    def _keyword_score(self, comment: Comment) -> LeadScore:
        """增强关键词评分 — 使用同义词引擎"""
        result = keyword_engine.analyze(comment.content)

        return LeadScore(
            comment_id=comment.id,
            score=result.score,
            intent=result.intent,
            urgency=result.urgency,
            keywords=result.keywords,
            reasoning=result.reasoning,
        )

    async def batch_analyze(self, comments: list[Comment]) -> list[LeadScore]:
        """批量分析评论"""
        results = []
        for comment in comments:
            score = await self.analyze(comment)
            results.append(score)
        return results
