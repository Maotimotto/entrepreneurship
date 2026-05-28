"""情感分析模块 — 评论情感识别 + 缓存"""
from dataclasses import dataclass
from enum import Enum
from src.core.cache import sentiment_cache, make_cache_key


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class SentimentResult:
    sentiment: Sentiment
    confidence: float
    positive_score: float
    negative_score: float
    keywords: list[str]


class SentimentAnalyzer:
    """基于词典的中文情感分析 + LRU缓存"""

    POSITIVE_WORDS = [
        "太棒了", "厉害", "牛", "优秀", "精品", "神器", "宝藏", "绝了", "封神",
        "好", "不错", "赞", "棒", "强", "优秀", "实用", "有用", "干货", "良心",
        "感谢", "谢谢", "支持", "喜欢", "爱了", "收藏", "关注",
        "想学", "教程", "课程", "学习", "教学",
    ]

    NEGATIVE_WORDS = [
        "垃圾", "骗人", "割韭菜", "坑", "假的", "骗子", "恶心",
        "差", "烂", "失望", "后悔", "浪费", "没用", "不行",
        "难用", "太难", "看不懂", "学不会",
        "互赞", "互关", "互粉", "涨粉",
    ]

    INTENSIFIERS = ["太", "真的", "非常", "特别", "超级", "简直", "实在", "真"]

    def analyze(self, text: str) -> SentimentResult:
        """分析文本情感（带缓存）"""
        if not text or not text.strip():
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL, confidence=1.0,
                positive_score=0.0, negative_score=0.0, keywords=[]
            )

        text = text.strip()

        # 检查缓存
        cache_key = make_cache_key(text, "sentiment")
        cached = sentiment_cache.get(cache_key)
        if cached:
            return cached

        # 分析
        result = self._analyze_impl(text)

        # 存入缓存
        sentiment_cache.set(cache_key, result)
        return result

    def _analyze_impl(self, text: str) -> SentimentResult:
        """实际分析逻辑"""
        pos_words = [w for w in self.POSITIVE_WORDS if w in text]
        neg_words = [w for w in self.NEGATIVE_WORDS if w in text]

        pos_score = len(pos_words) * 0.3
        neg_score = len(neg_words) * 0.3

        for intensifier in self.INTENSIFIERS:
            if intensifier in text:
                pos_score *= 1.2
                break

        total = pos_score + neg_score
        if total > 0:
            pos_norm = pos_score / total
            neg_norm = neg_score / total
        else:
            pos_norm = 0.5
            neg_norm = 0.5

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
