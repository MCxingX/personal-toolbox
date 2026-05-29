"""数据保留策略 - 基于北京时间凌晨自动清理过期数据."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# 北京时间时区
BEIJING_TZ = timezone(timedelta(hours=8))

# 默认保留天数（含当天，实际保留 7+1=8 天）
DEFAULT_NEWS_DAYS = 7
DEFAULT_IMPORTANT_DAYS = 15


def _get_beijing_now() -> datetime:
    """获取北京时间."""
    return datetime.now(BEIJING_TZ)


def _get_beijing_midnight_today() -> datetime:
    """获取北京时间今天凌晨 0 点."""
    now = _get_beijing_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _should_cleanup_today(repo) -> bool:
    """判断今天是否需要执行清理.

    规则：每天凌晨只执行一次清理，记录上次清理日期避免重复执行。
    """
    try:
        with repo.db.connect() as conn:
            # 检查是否有记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_log (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_cleanup_date TEXT NOT NULL
                )
            """)
            row = conn.execute("SELECT last_cleanup_date FROM cleanup_log WHERE id = 1").fetchone()

            if row:
                last_date = row["last_cleanup_date"]
                today = _get_beijing_now().strftime("%Y-%m-%d")
                if last_date == today:
                    logger.debug("今天已执行过清理，跳过")
                    return False
            return True
    except Exception:
        return True


def _record_cleanup_date(repo) -> None:
    """记录今天的清理日期."""
    try:
        today = _get_beijing_now().strftime("%Y-%m-%d")
        with repo.db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_log (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_cleanup_date TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT OR REPLACE INTO cleanup_log (id, last_cleanup_date) VALUES (1, ?)",
                (today,)
            )
    except Exception as e:
        logger.warning("记录清理日期失败: %s", e)


def cleanup_expired_data(repo, news_days: int = DEFAULT_NEWS_DAYS, important_days: int = DEFAULT_IMPORTANT_DAYS, force: bool = False) -> dict:
    """清理过期数据.

    规则：
    - 普通新闻/热榜数据：保留 7 天（含当天共 8 天）
    - 重要文章（importance_score >= 0.8）：保留 15 天（含当天共 16 天）
    - 天气/地震数据：保留 7 天
    - 语录/设置等核心数据不删除
    - 每天凌晨北京时间只执行一次

    Args:
        force: 强制执行清理（忽略日期检查）

    Returns:
        {"deleted_articles": int, "deleted_weather": int, "deleted_earthquake": int, "skipped": bool}
    """
    results = {"deleted_articles": 0, "deleted_weather": 0, "deleted_earthquake": 0, "skipped": False}

    # 检查今天是否已清理
    if not force and not _should_cleanup_today(repo):
        results["skipped"] = True
        return results

    # 计算截止时间（北京时间凌晨 0 点）
    midnight_today = _get_beijing_midnight_today()
    news_cutoff = (midnight_today - timedelta(days=news_days + 1)).isoformat()
    important_cutoff = (midnight_today - timedelta(days=important_days + 1)).isoformat()

    try:
        with repo.db.connect() as conn:
            # 1. 删除普通过期文章（importance_score < 0.8）
            cursor = conn.execute(
                """DELETE FROM articles
                WHERE collected_at < ?
                AND (importance_score IS NULL OR importance_score < 0.8)""",
                (news_cutoff,),
            )
            results["deleted_articles"] = cursor.rowcount

            # 2. 删除过期的重要文章
            cursor2 = conn.execute(
                """DELETE FROM articles
                WHERE collected_at < ?
                AND importance_score >= 0.8""",
                (important_cutoff,),
            )
            results["deleted_articles"] += cursor2.rowcount

            # 3. 清理过期天气数据
            cursor3 = conn.execute(
                "DELETE FROM weather_forecasts WHERE collected_at < ?",
                (news_cutoff,),
            )
            results["deleted_weather"] = cursor3.rowcount

            # 4. 清理过期地震数据
            cursor4 = conn.execute(
                "DELETE FROM earthquake_events WHERE collected_at < ?",
                (news_cutoff,),
            )
            results["deleted_earthquake"] = cursor4.rowcount

            # 5. 清理 UAPI 采集日志中超过 7 天的记录
            conn.execute(
                "DELETE FROM uapi_fetch_log WHERE last_fetch_at < ?",
                (news_cutoff,),
            )

        # 记录清理日期
        _record_cleanup_date(repo)

        total = sum(v for k, v in results.items() if k != "skipped")
        if total > 0:
            logger.info("数据清理完成: 删除 %d 条文章, %d 条天气, %d 条地震",
                       results["deleted_articles"], results["deleted_weather"], results["deleted_earthquake"])
        else:
            logger.debug("无过期数据需要清理")

    except Exception as e:
        logger.warning("数据清理失败: %s", e)

    return results


def get_data_stats(repo) -> dict:
    """获取数据统计信息."""
    stats = {}
    try:
        with repo.db.connect() as conn:
            # 文章总数和分类统计
            row = conn.execute("SELECT COUNT(*) as c FROM articles").fetchone()
            stats["total_articles"] = row["c"] if row else 0

            rows = conn.execute(
                "SELECT category, COUNT(*) as c FROM articles GROUP BY category ORDER BY c DESC"
            ).fetchall()
            stats["by_category"] = {r["category"]: r["c"] for r in rows}

            # 最旧和最新文章时间
            row = conn.execute("SELECT MIN(collected_at) as oldest, MAX(collected_at) as newest FROM articles").fetchone()
            stats["oldest_article"] = row["oldest"] if row else None
            stats["newest_article"] = row["newest"] if row else None

            # 天气数据
            row = conn.execute("SELECT COUNT(*) as c FROM weather_forecasts").fetchone()
            stats["total_weather"] = row["c"] if row else 0

            # 地震数据
            row = conn.execute("SELECT COUNT(*) as c FROM earthquake_events").fetchone()
            stats["total_earthquake"] = row["c"] if row else 0

            # UAPI 平台状态
            rows = conn.execute("SELECT COUNT(*) as c FROM uapi_fetch_log").fetchone()
            stats["uapi_platforms"] = rows["c"] if rows else 0

    except Exception as e:
        logger.warning("获取数据统计失败: %s", e)

    return stats


def check_and_cleanup_if_needed(repo) -> dict | None:
    """检查并执行清理（如果需要）.

    此函数应在应用启动时调用，判断是否需要执行清理。
    只有在凌晨 0 点后且今天未清理过时才执行。

    Returns:
        清理结果字典，如果跳过则返回 None
    """
    now = _get_beijing_now()

    # 只在凌晨 0 点后执行（0-6 点之间）
    if 0 <= now.hour <= 6:
        if _should_cleanup_today(repo):
            logger.info("凌晨时段，执行数据清理...")
            return cleanup_expired_data(repo, force=True)

    return None
