"""UAPI 热榜连接器 - 对接 uapis.cn 免费热榜 API."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from news_intelligence_desktop.connectors.sections import get_enabled_sections
from news_intelligence_desktop.storage.repository import Repository

logger = logging.getLogger(__name__)

# ===== 限速配置 =====
REQUEST_INTERVAL = 2.0  # 每次请求间隔（秒）
MAX_CONCURRENT = 5  # 最大并发数

# ===== 平台分类映射 =====
PLATFORM_CATEGORY = {
    # 新闻资讯
    "weibo": "news",
    "baidu": "news",
    "toutiao": "news",
    "qq-news": "news",
    "sina": "news",
    "sina-news": "news",
    "netease-news": "news",
    "thepaper": "news",
    "huxiu": "news",
    "ifanr": "news",
    # 科技
    "36kr": "tech",
    "ithome": "tech",
    "ithome-xijiayi": "tech",
    "sspai": "tech",
    "juejin": "tech",
    "jianshu": "tech",
    "v2ex": "tech",
    "51cto": "tech",
    "csdn": "tech",
    "nodeseek": "tech",
    "hellogithub": "tech",
    # 社区/论坛
    "zhihu": "news",
    "zhihu-daily": "news",
    "tieba": "news",
    "hupu": "news",
    "ngabbs": "news",
    "52pojie": "tech",
    "hostloc": "tech",
    "coolapk": "tech",
    "douban-movie": "culture",
    "douban-group": "news",
    "guokr": "science",
    # 视频/娱乐
    "bilibili": "culture",
    "acfun": "culture",
    "douyin": "culture",
    "kuaishou": "culture",
    # 游戏
    "lol": "odds",
    "genshin": "odds",
    "honkai": "odds",
    "starrail": "odds",
    # 音乐
    "netease-music": "culture",
    "qq-music": "culture",
    # 阅读
    "weread": "culture",
    # 天气/地震（特殊处理）
    "weatheralarm": "weather",
    "earthquake": "earthquake",
    "history": "news",
}

# ===== 缓存策略 =====
# 24小时刷新一次的数据
DAILY_TYPES = {"weatheralarm", "earthquake", "history"}
# 12小时刷新一次的数据（热榜类）
HOURLY_TYPES = set(PLATFORM_CATEGORY.keys()) - DAILY_TYPES


class UapiConnector:
    """UAPI 热榜连接器."""

    API_URL = "https://uapis.cn/api/v1/misc/hotboard"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from uapi import UapiClient
            self._client = UapiClient("https://uapis.cn")
        return self._client

    def fetch_hotboard(self, board_type: str) -> dict[str, Any]:
        """获取指定平台热榜数据.

        优先使用 SDK，失败时降级为直接 HTTP 请求.

        Returns:
            {"ok": bool, "data": list[dict], "error": str, "update_time": str}
        """
        # 先尝试 SDK
        result = self._fetch_via_sdk(board_type)
        if result["ok"]:
            return result

        # 降级为 HTTP 请求
        return self._fetch_via_http(board_type)

    def _fetch_via_sdk(self, board_type: str) -> dict[str, Any]:
        """通过 SDK 获取数据."""
        try:
            client = self._get_client()
            resp = client.misc.get_misc_hotboard(type=board_type)

            if not isinstance(resp, dict) or "list" not in resp:
                return {"ok": False, "data": [], "error": "SDK 返回格式异常", "update_time": ""}

            items = resp.get("list", [])
            update_time = resp.get("update_time", "")

            data = []
            for item in items:
                title = item.get("title", "").strip() if isinstance(item, dict) else str(item).strip()
                if not title:
                    continue
                data.append({
                    "title": title,
                    "url": item.get("url", "") if isinstance(item, dict) else "",
                    "hot_value": item.get("hot_value", 0) if isinstance(item, dict) else 0,
                    "index": item.get("index", 0) if isinstance(item, dict) else 0,
                    "source": f"uapi-{board_type}",
                    "category": PLATFORM_CATEGORY.get(board_type, "news"),
                })

            return {"ok": True, "data": data, "error": "", "update_time": update_time}

        except Exception as e:
            return {"ok": False, "data": [], "error": str(e), "update_time": ""}

    def _fetch_via_http(self, board_type: str) -> dict[str, Any]:
        """通过直接 HTTP 请求获取数据（降级方案）."""
        try:
            import requests
            import time

            # 限速：每次请求间隔
            time.sleep(REQUEST_INTERVAL)

            resp = requests.get(self.API_URL, params={"type": board_type}, timeout=15)
            resp.raise_for_status()
            result = resp.json()

            if not isinstance(result, dict) or "list" not in result:
                return {"ok": False, "data": [], "error": "HTTP 返回格式异常", "update_time": ""}

            items = result.get("list", [])
            update_time = result.get("update_time", result.get("update_at", ""))

            data = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = item.get("title", "").strip()
                if not title:
                    continue
                data.append({
                    "title": title,
                    "url": item.get("url", ""),
                    "hot_value": item.get("hot_value", 0),
                    "index": item.get("index", 0),
                    "source": f"uapi-{board_type}",
                    "category": PLATFORM_CATEGORY.get(board_type, "news"),
                })

            return {"ok": True, "data": data, "error": "", "update_time": update_time}

        except Exception as e:
            return {"ok": False, "data": [], "error": str(e), "update_time": ""}


def _is_chinese(text: str) -> bool:
    """判断文本是否主要是中文."""
    if not text:
        return False
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return False
    return chinese_chars / total_chars >= 0.3


def _should_fetch(board_type: str, last_fetch: datetime | None) -> bool:
    """判断是否应该抓取该类型的数据."""
    if last_fetch is None:
        return True
    now = datetime.now()
    if board_type in DAILY_TYPES:
        # 24小时刷新
        return (now - last_fetch) >= timedelta(hours=24)
    else:
        # 12小时刷新
        return (now - last_fetch) >= timedelta(hours=12)


def _enabled_board_types(settings: dict | None = None) -> set[str]:
    if not settings:
        return set(PLATFORM_CATEGORY)
    boards: set[str] = set()
    for section in get_enabled_sections(settings).values():
        for source in section.sources:
            if source.source_type == "hotboard":
                boards.add(source.url)
    return boards or set(PLATFORM_CATEGORY)


def collect_uapi_all(repo: Repository, settings: dict | None = None) -> dict[str, int]:
    """采集所有 UAPI 热榜数据，带智能缓存和限速.

    Returns:
        {platform: count} 各平台采集的数据量
    """
    connector = UapiConnector()
    results = {}

    # 获取上次采集时间
    last_fetch_times = _get_last_fetch_times(repo)

    # 限速统计
    total_fetched = 0
    total_skipped = 0

    enabled_boards = _enabled_board_types(settings)

    for board_type in PLATFORM_CATEGORY:
        if board_type not in enabled_boards:
            results[board_type] = 0
            total_skipped += 1
            continue
        # 检查缓存
        last_fetch = last_fetch_times.get(board_type)
        if not _should_fetch(board_type, last_fetch):
            logger.debug("UAPI %s 跳过（缓存有效）", board_type)
            results[board_type] = 0
            total_skipped += 1
            continue

        result = connector.fetch_hotboard(board_type)
        if not result["ok"]:
            logger.warning("UAPI %s 失败: %s", board_type, result["error"])
            results[board_type] = 0
            continue

        saved = 0
        for item in result["data"]:
            # 中文过滤
            if not _is_chinese(item["title"]):
                continue

            # hot_value 可能是字符串
            try:
                hot_val = float(item.get("hot_value", 0) or 0)
            except (ValueError, TypeError):
                hot_val = 0

            from news_intelligence_desktop.storage.repository import ArticleInput
            article = ArticleInput(
                title=item["title"],
                summary=item["title"],
                source_name=item["source"],
                source_url=item["url"],
                url=item["url"],
                category=item["category"],
                importance_score=min(0.5 + hot_val / 10000, 1.0),
                language="zh",
            )
            if repo.add_article(article):
                saved += 1

        # 记录采集时间
        _set_last_fetch_time(repo, board_type)
        results[board_type] = saved
        total_fetched += 1
        logger.info("UAPI %s: %d 条新数据", board_type, saved)

    logger.info("UAPI 采集完成: %d 个平台采集, %d 个平台跳过", total_fetched, total_skipped)
    return results


def _get_last_fetch_times(repo: Repository) -> dict[str, datetime]:
    """获取各平台上次采集时间."""
    times = {}
    try:
        with repo.db.connect() as conn:
            # 确保表存在
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uapi_fetch_log (
                    board_type TEXT PRIMARY KEY,
                    last_fetch_at TEXT NOT NULL
                )
            """)
            rows = conn.execute("SELECT board_type, last_fetch_at FROM uapi_fetch_log").fetchall()
            for row in rows:
                try:
                    times[row[0]] = datetime.fromisoformat(row[1])
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        logger.warning("读取 UAPI 采集日志失败: %s", e)
    return times


def _set_last_fetch_time(repo: Repository, board_type: str) -> None:
    """记录某平台的采集时间."""
    try:
        with repo.db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uapi_fetch_log (
                    board_type TEXT PRIMARY KEY,
                    last_fetch_at TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT OR REPLACE INTO uapi_fetch_log(board_type, last_fetch_at) VALUES(?,?)",
                (board_type, datetime.now().isoformat()),
            )
    except Exception as e:
        logger.warning("记录 UAPI 采集时间失败: %s", e)


def get_uapi_status(repo: Repository) -> list[dict]:
    """获取各平台的采集状态（用于 UI 展示）."""
    last_fetch_times = _get_last_fetch_times(repo)
    status_list = []
    for board_type, category in sorted(PLATFORM_CATEGORY.items(), key=lambda x: x[1]):
        last_fetch = last_fetch_times.get(board_type)
        if last_fetch:
            if board_type in DAILY_TYPES:
                next_fetch = last_fetch + timedelta(hours=24)
                cache_label = "24h"
            else:
                next_fetch = last_fetch + timedelta(hours=12)
                cache_label = "12h"
            now = datetime.now()
            if now >= next_fetch:
                status = "待更新"
            else:
                remaining = next_fetch - now
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                status = f"{hours}h{minutes}m 后更新"
        else:
            status = "未采集"
            cache_label = "24h" if board_type in DAILY_TYPES else "12h"

        status_list.append({
            "type": board_type,
            "category": category,
            "cache_ttl": cache_label,
            "last_fetch": last_fetch.isoformat() if last_fetch else None,
            "status": status,
        })
    return status_list
