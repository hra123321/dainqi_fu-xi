"""
============================================
 内存 LRU 缓存（第一层缓存）
============================================
【作用】
在程序内存中缓存 AI 响应结果，避免短时间内重复调用 API。
LRU = Least Recently Used（最近最少使用），
当缓存满了优先淘汰最久没用过的条目。

【核心机制】
1. TTL（Time To Live）：每个缓存条目有存活时间，超时自动失效
2. 最大条目数：内存占用保护，防止缓存无限膨胀
3. 惰性淘汰：每次读写时检查过期条目并清除，不单独开定时器

【数据流】
  请求 → 查缓存（命中且未过期）→ 直接返回结果（快！）
       ↘ （未命中/已过期）→ 调用 API → 写入缓存 → 返回结果
"""

import time
from collections import OrderedDict
from typing import Optional, Any

from app.config import settings


class MemoryCache:
    """
    【内存缓存类】
    
    OrderedDict 是 Python 中"有序字典"，能记住元素插入顺序。
    用它实现 LRU 淘汰：每次访问某条目就把它移到末尾，
    那么"最久没用的"永远在开头，淘汰时删开头即可。
    """

    def __init__(self, maxsize: int = None, ttl: int = None):
        """
        【初始化缓存】
        
        参数:
            maxsize: 最大缓存条目数（默认从配置文件读取）
            ttl: 缓存存活秒数（默认从配置文件读取）
        """
        self._maxsize = maxsize or settings.MEMORY_CACHE_MAXSIZE
        self._ttl = ttl or settings.MEMORY_CACHE_TTL
        # OrderedDict 有序字典，用于 LRU 淘汰
        self._cache: OrderedDict = OrderedDict()
        
        # 统计信息
        self._hits = 0      # 命中次数
        self._misses = 0    # 未命中次数

    def get(self, key: str) -> Optional[Any]:
        """
        【获取缓存值】
        
        参数:
            key: 缓存键
        
        返回:
            如果命中且未过期 → 缓存的值
            如果未命中或已过期 → None
        
        原理:
            1. 检查 key 是否存在
            2. 检查是否过期（当前时间 > 存入时间 + TTL）
            3. 如果有效：移动到末尾（表示刚用过），返回数据
            4. 如果无效：删除该条目
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, expire_time = self._cache[key]
        
        # 检查是否过期
        if time.time() > expire_time:
            # 已过期，删除并返回 None
            del self._cache[key]
            self._misses += 1
            return None
        
        # 命中！把这条记录移到末尾（LRU 算法核心）
        # 删除再插入 = 移到最后
        self._cache.move_to_end(key)
        self._hits += 1
        return value

    def set(self, key: str, value: Any):
        """
        【写入缓存】
        
        参数:
            key: 缓存键
            value: 要缓存的值
        
        原理:
            1. 如果 key 已存在，先删除旧的
            2. 计算过期时间 = 当前时间 + TTL
            3. 存入缓存
            4. 如果超出最大条目数，删除最旧的（开头的条目）
        """
        # 如果已存在，先删除（后续会重新插入到末尾）
        if key in self._cache:
            del self._cache[key]
        
        # 计算过期时间
        expire_time = time.time() + self._ttl
        
        # 存入缓存
        self._cache[key] = (value, expire_time)
        
        # 如果超出最大条目数，删除最久没用过的（第一个元素）
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)  # last=False 弹出第一个

    def delete(self, key: str):
        """删除指定缓存条目"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """清空全部缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def size(self) -> int:
        """当前缓存条目数"""
        return len(self._cache)

    @property
    def stats(self) -> dict:
        """
        【获取缓存统计信息】
        
        用于管理页面监控缓存效率
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": self.size,
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self._ttl,
        }


# ==================== 创建全局缓存实例 ====================
# 整个项目共用一个缓存实例
cache = MemoryCache()
