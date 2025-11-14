#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融知识图谱系统 - 缓存管理模块

提供高效的内存缓存和持久化缓存功能，减少重复计算和API调用。
采用装饰器模式设计，易于使用和扩展。
"""

import hashlib
import json
import time
import logging
from typing import Any, Optional, Dict, Callable, Union
from functools import wraps
from threading import Lock
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class SimpleCache:
    """简单内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 1800):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict] = {}
        self._lock = Lock()
        self._access_order = []  # 用于LRU淘汰
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 组合所有参数
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # 生成hash
        key_string = f"{prefix}:{json.dumps(key_data, sort_keys=True, default=str)}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: Dict) -> bool:
        """检查缓存是否过期"""
        if 'ttl' not in entry:
            return False
        return time.time() > entry['created_at'] + entry['ttl']
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
    
    def _evict_lru(self) -> None:
        """LRU淘汰策略"""
        if len(self._cache) >= self.max_size:
            # 移除最少使用的条目
            oldest_key = self._access_order[0] if self._access_order else None
            if oldest_key:
                del self._cache[oldest_key]
                self._access_order.remove(oldest_key)
                logger.debug(f"LRU淘汰缓存键: {oldest_key}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if self._is_expired(entry):
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return None
            
            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            # 清理过期缓存
            self._cleanup_expired()
            
            # LRU淘汰
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # 设置缓存
            entry = {
                'value': value,
                'created_at': time.time(),
                'ttl': ttl if ttl is not None else self.default_ttl
            }
            
            self._cache[key] = entry
            
            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            logger.debug(f"缓存设置成功: {key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            self._cleanup_expired()
            return {
                'total_entries': len(self._cache),
                'max_size': self.max_size,
                'usage_ratio': len(self._cache) / self.max_size
            }


class CacheManager:
    """缓存管理器 - 统一接口"""
    
    def __init__(self, cache_type: str = "memory", **kwargs):
        """
        初始化缓存管理器
        
        Args:
            cache_type: 缓存类型 ("memory", "sqlite")
            **kwargs: 缓存配置参数
        """
        self.cache_type = cache_type
        
        if cache_type == "memory":
            self.cache = SimpleCache(
                max_size=kwargs.get('max_size', 1000),
                default_ttl=kwargs.get('default_ttl', 1800)
            )
        else:
            raise ValueError(f"不支持的缓存类型: {cache_type}")
        
        logger.info(f"缓存管理器初始化完成: {cache_type}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        return self.cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        return self.cache.delete(key)
    
    def clear(self) -> None:
        """清空缓存"""
        return self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache.get_stats()


def cache_result(prefix: str, ttl: Optional[int] = None, 
                cache_manager: Optional[CacheManager] = None):
    """
    缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 过期时间（秒）
        cache_manager: 缓存管理器实例
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache_manager._cache._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {func.__name__} ({key})")
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            logger.debug(f"缓存设置: {func.__name__} ({key})")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache_manager._cache._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {func.__name__} ({key})")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            logger.debug(f"缓存设置: {func.__name__} ({key})")
            
            return result
        
        # 根据函数是否为异步选择包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局缓存管理器实例
cache_manager = CacheManager()


def get_cache() -> CacheManager:
    """获取全局缓存管理器实例"""
    return cache_manager


def clear_all_cache():
    """清空所有缓存"""
    cache_manager.clear()
    logger.info("所有缓存已清空")


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return cache_manager.get_stats()


# 预定义常用缓存前缀
CACHE_PREFIXES = {
    'ENTITY_EXTRACTION': 'entity_extraction',
    'RELATION_EXTRACTION': 'relation_extraction',
    'EVENT_EXTRACTION': 'event_extraction',
    'TEXT_ANALYSIS': 'text_analysis',
    'SIMILARITY_CALC': 'similarity_calc'
}