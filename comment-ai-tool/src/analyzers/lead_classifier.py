"""潜客标签自动分类模块"""
from dataclasses import dataclass
from enum import Enum


class LeadCategory(str, Enum):
    """潜客分类"""
    BUYER = "buyer"           # 购买意向
    LEARNER = "learner"       # 学习意向
    PARTNER = "partner"       # 合作意向
    INQUIRER = "inquirer"     # 咨询意向
    FOLLOWER = "follower"     # 关注/收藏
    SPAM = "spam"             # 垃圾/无价值


@dataclass
class LeadClassification:
    """潜客分类结果"""
    category: LeadCategory
    confidence: float
    tags: list[str]
    reasoning: str


class LeadClassifier:
    """潜客自动分类器"""

    # 关键词到分类的映射
    CATEGORY_KEYWORDS = {
        LeadCategory.BUYER: [
            "怎么买", "购买", "下单", "要", "想要", "想买", "求购",
            "多少钱", "价格", "收费", "费用",
        ],
        LeadCategory.LEARNER: [
            "想学", "怎么学", "在哪学", "教程", "课程", "培训", "教学",
            "学习", "学会", "学", "有教程吗",
        ],
        LeadCategory.PARTNER: [
            "合作", "代理", "加盟", "一起做", "合伙", "商务",
            "求合作", "公司",
        ],
        LeadCategory.INQUIRER: [
            "怎么联系", "联系方式", "加微信", "私信", "加你",
            "怎么", "如何", "是什么", "什么意思",
        ],
        LeadCategory.FOLLOWER: [
            "关注", "已关注", "关注了", "粉丝",
            "收藏", "已收藏", "mark", "码住", "转了",
        ],
        LeadCategory.SPAM: [
            "互赞", "互关", "互粉", "涨粉",
            "第一", "沙发", "路过",
        ],
    }

    def classify(self, content: str, keywords: list[str] = None, score: float = 0.0) -> LeadClassification:
        """分类潜客"""
        if not content:
            return LeadClassification(
                category=LeadCategory.SPAM,
                confidence=1.0,
                tags=[],
                reasoning="空内容"
            )

        # 用关键词匹配
        matched = {}
        for category, cat_keywords in self.CATEGORY_KEYWORDS.items():
            found = [kw for kw in cat_keywords if kw in content]
            if found:
                matched[category] = found

        if not matched:
            # 默认分类
            if score >= 0.7:
                return LeadClassification(
                    category=LeadCategory.INQUIRER,
                    confidence=0.5,
                    tags=keywords or [],
                    reasoning="高分但无明确分类关键词"
                )
            return LeadClassification(
                category=LeadCategory.FOLLOWER,
                confidence=0.3,
                tags=keywords or [],
                reasoning="无匹配关键词"
            )

        # 取匹配最多的分类
        best_category = max(matched.keys(), key=lambda c: len(matched[c]))
        best_keywords = matched[best_category]

        # 置信度 = 匹配关键词数 / 总关键词数
        total_keywords = sum(len(v) for v in matched.values())
        confidence = len(best_keywords) / total_keywords if total_keywords > 0 else 0.5

        # 标签 = 所有匹配的关键词
        all_tags = []
        for kws in matched.values():
            all_tags.extend(kws)

        return LeadClassification(
            category=best_category,
            confidence=round(confidence, 2),
            tags=list(set(all_tags)),
            reasoning=f"匹配分类 {best_category.value}: {best_keywords}"
        )


# 全局分类器
lead_classifier = LeadClassifier()
