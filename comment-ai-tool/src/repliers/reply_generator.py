"""智能回复生成器 — 根据潜客评分和意图生成个性化回复"""
from openai import AsyncOpenAI
from config.settings import settings
from src.models.comment import Comment, LeadScore


REPLY_PROMPT = """你是一个友善、专业的短视频博主助手。根据以下信息生成一条回复评论。

原评论: "{comment}"
评论者意图: {intent}
潜客评分: {score}
作品标题: "{post_title}"
平台: {platform}

要求:
1. 回复要自然、真诚，像真人一样
2. 如果是高意向潜客 (score >= 0.7)，自然引导到私域 (如: "私信我详细聊聊")
3. 如果是中等意向 (0.4-0.7)，给出价值感回复，埋下钩子
4. 如果是低意向，简短友好回复即可
5. 不要太长，控制在50字以内
6. 不要用emoji堆砌，适度使用
7. 根据平台调整语气: 抖音偏活泼、小红书偏种草、视频号偏正式

只返回回复内容文本，不要其他。"""


class ReplyGenerator:
    """AI回复生成器"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
        )
        self.model = settings.ai_model

    async def generate(self, comment: Comment, score: LeadScore) -> str:
        """生成智能回复"""
        # 低分评论不回复
        if score.score < settings.min_lead_score:
            return ""

        prompt = REPLY_PROMPT.format(
            comment=comment.content,
            intent=score.intent,
            score=score.score,
            post_title=comment.post_title,
            platform=comment.platform.value,
        )

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return self._fallback_reply(comment, score)

    def _fallback_reply(self, comment: Comment, score: LeadScore) -> str:
        """降级回复模板"""
        if score.score >= 0.8:
            return "感谢关注！想了解更多可以私信我~"
        elif score.score >= 0.6:
            return "谢谢支持！有问题随时问我 😊"
        else:
            return "感谢评论 ❤️"
