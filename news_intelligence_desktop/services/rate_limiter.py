"""爬虫速率限制器 - 防止被封禁."""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RateLimiter:
    """全局限速器：每个域名独立限速."""

    def __init__(self, default_interval: float = 2.0, max_workers: int = 10):
        """
        Args:
            default_interval: 默认请求间隔（秒）
            max_workers: 最大并发数
        """
        self._interval = default_interval
        self._max_workers = max_workers
        self._last_request: dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_workers)
        self._stats: dict[str, int] = defaultdict(int)

    def wait(self, domain: str) -> None:
        """等待直到可以对该域名发起请求."""
        self._semaphore.acquire()
        try:
            with self._lock:
                now = time.time()
                last = self._last_request.get(domain, 0)
                wait_time = max(0, self._interval - (now - last))
                if wait_time > 0:
                    logger.debug("限速: %s 等待 %.1fs", domain, wait_time)
                    time.sleep(wait_time)
                self._last_request[domain] = time.time()
                self._stats[domain] += 1
        finally:
            self._semaphore.release()

    def get_stats(self) -> dict[str, int]:
        """获取各域名请求次数统计."""
        return dict(self._stats)

    def reset(self) -> None:
        """重置统计."""
        self._stats.clear()
        self._last_request.clear()


# 全局限速器实例
_global_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    """获取全局限速器实例."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter


def init_limiter(default_interval: float = 2.0, max_workers: int = 10) -> RateLimiter:
    """初始化全局限速器."""
    global _global_limiter
    _global_limiter = RateLimiter(default_interval, max_workers)
    return _global_limiter


def rate_limited(domain_func: Callable[..., str] | str | None = None):
    """装饰器：对函数进行速率限制.

    用法:
        @rate_limited(lambda *args: "api.github.com")
        def fetch_github():
            ...

        @rate_limited("rss.example.com")
        def fetch_rss():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_limiter()
            if callable(domain_func):
                domain = domain_func(*args, **kwargs)
            elif isinstance(domain_func, str):
                domain = domain_func
            else:
                # 从 URL 提取域名
                url = args[0] if args else kwargs.get("url", "")
                from urllib.parse import urlparse
                domain = urlparse(str(url)).netloc or "unknown"

            limiter.wait(domain)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def extract_domain(url: str) -> str:
    """从 URL 提取域名."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc or "unknown"
