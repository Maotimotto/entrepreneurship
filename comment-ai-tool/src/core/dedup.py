"""评论去重模块"""
import hashlib
from collections import OrderedDict
from threading import Lock
from src.core.logger import logging

logger = logging.getLogger(__name__)


class CommentDeduplicator:
    """评论去重器 — 基于内容哈希 + 滑动窗口"""

    def __init__(self, window_size: int = 10000):
        self._seen: OrderedDict[str, float] = OrderedDict()
        self._window_size = window_size
        self._lock = Lock()
        self._duplicates = 0
        self._total = 0

    def _make_key(self, content: str, author_id: str, platform: str) -> str:
        """生成去重键 — 内容+作者+平台"""
        raw = f"{platform}:{author_id}:{content.strip()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def is_duplicate(self, content: str, author_id: str, platform: str) -> bool:
        """检查是否重复评论"""
        import time
        key = self._make_key(content, author_id, platform)

        with self._lock:
            self._total += 1
            if key in self._seen:
                self._duplicates += 1
                return True

            # 滑动窗口
            if len(self._seen) >= self._window_size:
                self._seen.popitem(last=False)

            self._seen[key] = time.time()
            return False

    def stats(self) -> dict:
        """去重统计"""
        with self._lock:
            return {
                "total": self._total,
                "duplicates": self._duplicates,
                "unique": self._total - self._duplicates,
                "dedup_rate": round(self._duplicates / self._total, 3) if self._total > 0 else 0,
                "window_size": self._window_size,
                "current_window": len(self._seen),
            }

    def clear(self):
        """清空去重记录"""
        with self._lock:
            self._seen.clear()
            self._duplicates = 0
            self._total = 0


# 全局去重器
deduplicator = CommentDeduplicator()
