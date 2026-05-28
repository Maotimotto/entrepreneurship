"""关键词引擎 — 增强版意图识别，支持同义词、否定词、上下文"""
import re
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果"""
    score: float
    intent: str
    urgency: str
    keywords: list[str]
    reasoning: str
    sentiment: str = "neutral"


class KeywordEngine:
    """增强版关键词引擎"""

    SYNONYM_GROUPS = {
        "buy": ["怎么买", "哪里买", "在哪买", "购买", "下单", "买", "想要", "想买", "求购"],
        "price": ["多少钱", "价格", "收费", "费用", "贵不贵", "便宜", "划算", "性价比"],
        "learn": ["想学", "怎么学", "在哪学", "教程", "课程", "培训", "教学", "学习", "学会"],
        "contact": ["加微信", "联系方式", "怎么联系", "私信", "加你", "找你", "联系"],
        "cooperate": ["合作", "代理", "加盟", "一起做", "合伙", "商务"],
        "positive": ["厉害", "太棒了", "牛", "强", "优秀", "精品", "干货", "实用", "有用", "不错"],
        "collect": ["收藏", "已收藏", "mark", "码住", "转了", "分享", "保存"],
        "follow": ["关注", "已关注", "关注了", "粉丝"],
        "spam": ["互赞", "互关", "互粉", "涨粉", "路过", "第一", "沙发"],
        "laugh": ["哈哈", "笑死", "666", "666666", "哈哈哈", "lol", "笑哭"],
    }

    # 否定词 — 仅在句首或特定句式中生效
    NEGATION_PATTERNS = [
        r"^不想", r"^不要", r"^不会", r"^不能", r"^不买", r"^不学",
        r"^没兴趣", r"^没用", r"^没必要",
        r"不想学", r"不想买", r"不要", r"不会买",
    ]

    HIGH_INTENT_GROUPS = ["buy", "price", "learn", "contact", "cooperate"]
    MEDIUM_INTENT_GROUPS = ["positive", "collect", "follow"]
    LOW_INTENT_GROUPS = ["spam", "laugh"]

    SCORE_WEIGHTS = {
        "buy": 0.95, "price": 0.85, "learn": 0.90, "contact": 0.88, "cooperate": 0.92,
        "positive": 0.45, "collect": 0.50, "follow": 0.40,
        "spam": 0.05, "laugh": 0.10,
    }

    INTENT_MAP = {
        "buy": "potential_lead", "price": "potential_lead", "learn": "potential_lead",
        "contact": "potential_lead", "cooperate": "potential_lead",
        "positive": "inquiry", "collect": "inquiry", "follow": "inquiry",
        "spam": "spam", "laugh": "neutral",
    }

    def analyze(self, text: str) -> MatchResult:
        """分析文本"""
        if not text or not text.strip():
            return MatchResult(score=0.0, intent="neutral", urgency="low",
                             keywords=[], reasoning="空内容", sentiment="neutral")

        text = text.strip()

        # 1. 同义词匹配
        matched_groups = self._match_synonyms(text)

        if not matched_groups:
            return MatchResult(score=0.1, intent="neutral", urgency="low",
                             keywords=[], reasoning="无匹配关键词", sentiment="neutral")

        # 2. 取最高分组
        best_group = max(matched_groups.keys(), key=lambda g: self.SCORE_WEIGHTS.get(g, 0))
        best_score = self.SCORE_WEIGHTS.get(best_group, 0.1)
        matched_keywords = matched_groups[best_group]

        # 3. 否定词检测 — 仅对高意向关键词做否定检查
        has_negation = False
        if best_group in self.HIGH_INTENT_GROUPS:
            has_negation = self._check_negation(text, matched_keywords)

        if has_negation:
            best_score *= 0.2
            intent = "neutral"
            reasoning = f"否定词匹配: {matched_keywords}"
        else:
            intent = self.INTENT_MAP.get(best_group, "neutral")
            reasoning = f"同义词组[{best_group}]: {matched_keywords}"

        urgency = "high" if best_score >= 0.7 else "medium" if best_score >= 0.4 else "low"
        sentiment = self._analyze_sentiment(matched_groups)

        return MatchResult(score=round(best_score, 2), intent=intent, urgency=urgency,
                         keywords=matched_keywords, reasoning=reasoning, sentiment=sentiment)

    def _check_negation(self, text: str, keywords: list[str]) -> bool:
        """检查否定词 — 智能上下文检测"""
        for pattern in self.NEGATION_PATTERNS:
            if re.search(pattern, text):
                return True

        # 检查关键词前面是否有否定词
        for kw in keywords:
            idx = text.find(kw)
            if idx > 0:
                prefix = text[max(0, idx-3):idx]
                if any(neg in prefix for neg in ["不", "没", "别", "未", "非"]):
                    return True
        return False

    def _match_synonyms(self, text: str) -> dict[str, list[str]]:
        """同义词匹配"""
        matched = {}
        for group_name, synonyms in self.SYNONYM_GROUPS.items():
            found = [syn for syn in synonyms if syn in text]
            if found:
                matched[group_name] = found
        return matched

    def _analyze_sentiment(self, matched_groups: dict) -> str:
        """情感分析"""
        positive_groups = {"positive", "collect", "follow", "buy", "learn", "contact", "cooperate"}
        negative_groups = {"spam"}

        if any(g in positive_groups for g in matched_groups):
            return "positive"
        elif any(g in negative_groups for g in matched_groups):
            return "negative"
        return "neutral"


keyword_engine = KeywordEngine()
