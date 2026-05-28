"""情感分析模块 — 评论情感识别"""
from dataclasses import dataclass
from enum import Enum


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class SentimentResult:
    sentiment: Sentiment
    confidence: float  # 0-1
    positive_score: float
    negative_score: float
    keywords: list[str]


class SentimentAnalyzer:
    """基于词典的中文情感分析"""

    POSITIVE_WORDS = [
        # 强正面
        "太棒了", "厉害", "牛", "优秀", "精品", "神器", "宝藏", "绝了", "封神",
        # 正面
        "好", "不错", "赞", "棒", "强", "优秀", "实用", "有用", "干货", "良心",
        "感谢", "谢谢", "支持", "喜欢", "爱了", "收藏", "关注",
        # 学习意向（正面）
        "想学", "教程", "课程", "学习", "教学",
    ]

    NEGATIVE_WORDS = [
        # 强负面
        "垃圾", "骗人", "割韭菜", "坑", "假的", "骗子", "恶心",
        # 负面
        "差", "烂", "失望", "后悔", "浪费", "没用", "不行",
        "难用", "太难", "看不懂", "学不会",
        # 垃圾评论
        "互赞", "互关", "互粉", "涨粉",
    ]

    INTENSIFIERS = ["太", "真的", "非常", "特别", "超级", "简直", "实在", "真"]
    NEGATIVES = ["不", "没", "别", "非", "未", "无"]

    def analyze(self, text: str) -> SentimentResult:
        """分析文本情感"""
        if not text or not text.strip():
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL, confidence=1.0,
                positive_score=0.0, negative_score=0.0, keywords=[]
            )

        text = text.strip()
        pos_words = []
        neg_words = []

        # 正面词匹配
        for word in self.POSITIVE_WORDS:
            if word in text:
                pos_words.append(word)

        # 负面词匹配
        for word in self.NEGATIVE_WORDS:
            if word in text:
                neg_words.append(word)

        # 计算分数
        pos_score = len(pos_words) * 0.3
        neg_score = len(neg_words) * 0.3

        # 强化词检测
        for intensifier in self.INTENSIFIERS:
            if intensifier in text:
                pos_score *= 1.2
                break

        # 归一化
        total = pos_score + neg_score
        if total > 0:
            pos_norm = pos_score / total
            neg_norm = neg_score / total
        else:
            pos_norm = 0.5
            neg_norm = 0.5

        # 判断情感
        if pos_words and not neg_words:
            sentiment = Sentiment.POSITIVE
            confidence = min(pos_norm, 1.0)
        elif neg_words and not pos_words:
            sentiment = Sentiment.NEGATIVE
            confidence = min(neg_norm, 1.0)
        elif pos_words and neg_words:
            sentiment = Sentiment.MIXED
            confidence = 0.5
        else:
            sentiment = Sentiment.NEUTRAL
            confidence = 0.8

        return SentimentResult(
            sentiment=sentiment,
            confidence=round(confidence, 2),
            positive_score=round(pos_score, 2),
            negative_score=round(neg_score, 2),
            keywords=pos_words + neg_words,
        )


sentiment_analyzer = SentimentAnalyzer()
