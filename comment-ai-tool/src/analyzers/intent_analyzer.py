"""AI意图分析器 — 核心模块：识别评论意图和潜客评分"""
import json
import logging
from openai import AsyncOpenAI
from config.settings import settings
from src.models.comment import Comment, LeadScore

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
    """基于LLM的评论意图分析器，无API key时自动降级为关键词匹配"""

    # 意图关键词库 — 按优先级排序
    HIGH_INTENT_KEYWORDS = [
        "怎么买", "多少钱", "价格", "在哪买", "求链接", "想学", "怎么学",
        "有课程吗", "加微信", "联系方式", "合作", "代理", "报名", "购买",
        "在哪买", "收费吗", "怎么做", "求带", "收徒", "拜师",
    ]
    MEDIUM_INTENT_KEYWORDS = [
        "有用", "收藏", "太棒了", "干货", "厉害", "学到了", "感谢",
        "关注了", "已关注", "转了", "分享", "mark", "码住", "太强了",
    ]
    SPAM_KEYWORDS = [
        "互赞", "互关", "互粉", "涨粉", "666666", "路过",
    ]

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
            logger.info("IntentAnalyzer: 关键词降级模式 (未配置AI API Key)")

    async def analyze(self, comment: Comment) -> LeadScore:
        """分析单条评论，返回潜客评分"""
        # 无API key直接走降级
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
        """关键词匹配评分 — 无LLM时的降级方案"""
        text = comment.content.strip()
        matched_keywords = []
        score = 0.1
        intent = "neutral"

        # 高意向匹配
        for kw in self.HIGH_INTENT_KEYWORDS:
            if kw in text:
                matched_keywords.append(kw)

        if matched_keywords:
            score = min(0.6 + 0.1 * len(matched_keywords), 1.0)
            intent = "potential_lead"
        else:
            # 中意向匹配
            for kw in self.MEDIUM_INTENT_KEYWORDS:
                if kw in text:
                    matched_keywords.append(kw)
            if matched_keywords:
                score = min(0.3 + 0.1 * len(matched_keywords), 0.6)
                intent = "inquiry"
            else:
                # 垃圾评论检测
                for kw in self.SPAM_KEYWORDS:
                    if kw in text:
                        intent = "spam"
                        score = 0.0
                        matched_keywords.append(kw)
                        break

        urgency = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"

        return LeadScore(
            comment_id=comment.id,
            score=round(score, 2),
            intent=intent,
            urgency=urgency,
            keywords=matched_keywords,
            reasoning=f"关键词匹配: {matched_keywords}" if matched_keywords else "无匹配关键词",
        )

    async def batch_analyze(self, comments: list[Comment]) -> list[LeadScore]:
        """批量分析评论"""
        results = []
        for comment in comments:
            score = await self.analyze(comment)
            results.append(score)
        return results
