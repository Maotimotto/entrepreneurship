"""缓存模块 — LRU缓存 + 批量处理优化"""
import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Any
from threading import Lock


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float
    hits: int = 0


class LRUCache:
    """线程安全的LRU缓存"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # 检查TTL
                if time.time() - entry.created_at > self._ttl:
                    del self._cache[key]
                    self._misses += 1
                    return None
                # 移到末尾（最近使用）
                self._cache.move_to_end(key)
                entry.hits += 1
                self._hits += 1
                return entry.value
            self._misses += 1
            return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key].value = value
                self._cache[key].created_at = time.time()
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = CacheEntry(value=value, created_at=time.time())

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
            }


def make_cache_key(text: str, prefix: str = "") -> str:
    """生成缓存键"""
    content = f"{prefix}:{text}" if prefix else text
    return hashlib.md5(content.encode()).hexdigest()


# 全局缓存实例
intent_cache = LRUCache(max_size=2000, ttl_seconds=1800)  # 意图分析缓存，30分钟
sentiment_cache = LRUCache(max_size=2000, ttl_seconds=1800)  # 情感分析缓存


class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size: int = 50):
        self._batch_size = batch_size

    async def process_batch(self, items: list, processor_fn) -> list:
        """批量处理项目"""
        results = []
        for i in range(0, len(items), self._batch_size):
            batch = items[i:i + self._batch_size]
            batch_results = await processor_fn(batch)
            results.extend(batch_results)
        return results

    def chunk(self, items: list) -> list[list]:
        """分块"""
        return [items[i:i + self._batch_size] for i in range(0, len(items), self._batch_size)]


# 全局批量处理器
batch_processor = BatchProcessor()
