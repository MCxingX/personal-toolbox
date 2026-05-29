"""订阅规则和新闻推送服务 - 关键词匹配、聚合去重、免打扰."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# 免打扰时段（北京时间）
DO_NOT_DISTURB_START = 23  # 23:00
DO_NOT_DISTURB_END = 7     # 07:00


class NotificationService:
    """通知服务 - 订阅规则匹配、通知管理、聚合去重."""

    def __init__(self, repo):
        self.repo = repo

    # ===== 订阅规则管理 =====

    def create_rule(self, name: str, keywords: list[str], categories: list[str] = None,
                    regions: list[str] = None, sources: list[str] = None,
                    min_hotness: float = 0, min_credibility: float = 0,
                    frequency: str = "instant", enabled: bool = True) -> int:
        """创建订阅规则."""
        with self.repo.db.connect() as conn:
            conn.execute(
                """INSERT INTO subscription_rules(name, keywords, categories, regions, sources,
                min_hotness, min_credibility, frequency, enabled)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    name,
                    json.dumps(keywords, ensure_ascii=False),
                    json.dumps(categories or [], ensure_ascii=False),
                    json.dumps(regions or [], ensure_ascii=False),
                    json.dumps(sources or [], ensure_ascii=False),
                    min_hotness,
                    min_credibility,
                    frequency,
                    1 if enabled else 0,
                ),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def update_rule(self, rule_id: int, **kwargs) -> bool:
        """更新订阅规则."""
        allowed = {"name", "keywords", "categories", "regions", "sources",
                   "min_hotness", "min_credibility", "frequency", "enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        # 序列化列表字段
        for key in ["keywords", "categories", "regions", "sources"]:
            if key in updates and isinstance(updates[key], list):
                updates[key] = json.dumps(updates[key], ensure_ascii=False)
        if "enabled" in updates:
            updates["enabled"] = 1 if updates["enabled"] else 0

        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [rule_id]

        with self.repo.db.connect() as conn:
            cursor = conn.execute(f"UPDATE subscription_rules SET {set_clause} WHERE id=?", values)
            return cursor.rowcount > 0

    def delete_rule(self, rule_id: int) -> bool:
        """删除订阅规则."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute("DELETE FROM subscription_rules WHERE id=?", (rule_id,))
            return cursor.rowcount > 0

    def list_rules(self, enabled_only: bool = False) -> list[dict]:
        """列出订阅规则."""
        with self.repo.db.connect() as conn:
            if enabled_only:
                rows = conn.execute("SELECT * FROM subscription_rules WHERE enabled=1 ORDER BY id").fetchall()
            else:
                rows = conn.execute("SELECT * FROM subscription_rules ORDER BY id").fetchall()

            results = []
            for row in rows:
                result = dict(row)
                # 反序列化 JSON 字段
                for key in ["keywords", "categories", "regions", "sources"]:
                    if result.get(key):
                        try:
                            result[key] = json.loads(result[key])
                        except Exception:
                            result[key] = []
                    else:
                        result[key] = []
                results.append(result)
            return results

    def get_rule(self, rule_id: int) -> dict | None:
        """获取订阅规则详情."""
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM subscription_rules WHERE id=?", (rule_id,)).fetchone()
            if not row:
                return None

            result = dict(row)
            for key in ["keywords", "categories", "regions", "sources"]:
                if result.get(key):
                    try:
                        result[key] = json.loads(result[key])
                    except Exception:
                        result[key] = []
                else:
                    result[key] = []
            return result

    # ===== 文章匹配 =====

    def match_article(self, article: dict) -> list[dict]:
        """匹配文章与订阅规则."""
        matches = []
        with self.repo.db.connect() as conn:
            rules = conn.execute("SELECT * FROM subscription_rules WHERE enabled=1").fetchall()

        for rule in rules:
            match_result = self._check_rule_match(article, dict(rule))
            if match_result:
                matches.append(match_result)

        return matches

    def _check_rule_match(self, article: dict, rule: dict) -> dict | None:
        """检查文章是否匹配规则."""
        keywords = json.loads(rule.get("keywords", "[]"))
        categories = json.loads(rule.get("categories", "[]"))
        regions = json.loads(rule.get("regions", "[]"))
        sources = json.loads(rule.get("sources", "[]"))
        min_hotness = rule.get("min_hotness", 0)
        min_credibility = rule.get("min_credibility", 0)

        # 构建搜索文本
        haystack = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')} {article.get('tags', '')}"

        # 关键词匹配
        keyword_match = True
        matched_keyword = ""
        if keywords:
            keyword_match = False
            for kw in keywords:
                if kw.lower() in haystack.lower():
                    keyword_match = True
                    matched_keyword = kw
                    break

        # 分类匹配
        category_match = True
        if categories:
            category_match = article.get("category", "") in categories

        # 地区匹配
        region_match = True
        if regions:
            region_match = article.get("region", "") in regions

        # 来源匹配
        source_match = True
        if sources:
            source_match = article.get("source_name", "") in sources

        # 热度匹配
        hotness = article.get("importance_score", 0)
        hotness_match = hotness >= min_hotness

        # 可信度匹配
        credibility = article.get("credibility_score", 0)
        credibility_match = credibility >= min_credibility

        # 所有条件都满足才匹配
        if keyword_match and category_match and region_match and source_match and hotness_match and credibility_match:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "article_id": article.get("id"),
                "matched_keyword": matched_keyword,
                "match_reason": self._build_match_reason(
                    keyword_match, category_match, region_match,
                    source_match, hotness_match, credibility_match,
                    matched_keyword
                ),
            }

        return None

    def _build_match_reason(self, kw: bool, cat: bool, region: bool,
                           source: bool, hot: bool, cred: bool, keyword: str) -> str:
        """构建匹配原因."""
        reasons = []
        if kw and keyword:
            reasons.append(f"关键词: {keyword}")
        if cat:
            reasons.append("分类匹配")
        if region:
            reasons.append("地区匹配")
        if source:
            reasons.append("来源匹配")
        if hot:
            reasons.append("热度达标")
        if cred:
            reasons.append("可信度达标")
        return "; ".join(reasons) if reasons else "规则匹配"

    def check_and_notify(self, article: dict) -> list[int]:
        """检查文章并发送通知."""
        matches = self.match_article(article)
        notification_ids = []

        for match in matches:
            # 检查是否重复
            if self._is_duplicate_notification(article.get("id"), match["rule_id"]):
                continue

            # 检查免打扰
            if self._is_do_not_disturb():
                # 延迟发送
                notif_id = self._enqueue_notification(
                    title=f"[延迟] {article.get('title', '')}",
                    body=f"规则 [{match['rule_name']}] 匹配: {match['match_reason']}",
                    item_type="article",
                    item_id=article.get("id"),
                    priority=3,
                )
            else:
                # 立即发送
                notif_id = self._enqueue_notification(
                    title=article.get("title", ""),
                    body=f"规则 [{match['rule_name']}] 匹配: {match['match_reason']}",
                    item_type="article",
                    item_id=article.get("id"),
                    priority=7,
                )

            if notif_id:
                notification_ids.append(notif_id)

        return notification_ids

    def _is_duplicate_notification(self, article_id: int, rule_id: int) -> bool:
        """检查是否重复通知."""
        if not article_id:
            return False

        with self.repo.db.connect() as conn:
            # 检查最近 24 小时内是否有相同文章的通知
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            row = conn.execute(
                """SELECT id FROM notifications
                WHERE item_id=? AND created_at>?
                AND body LIKE ?""",
                (article_id, cutoff, f"%规则%匹配%"),
            ).fetchone()
            return row is not None

    def _is_do_not_disturb(self) -> bool:
        """检查是否在免打扰时段."""
        from datetime import timezone, timedelta as td
        beijing_tz = timezone(td(hours=8))
        now = datetime.now(beijing_tz)
        hour = now.hour
        return DO_NOT_DISTURB_START <= hour or hour < DO_NOT_DISTURB_END

    def _enqueue_notification(self, title: str, body: str, item_type: str = "article", item_id: int = None, priority: int = 5) -> int:
        """入队通知."""
        # 检查是否重复
        with self.repo.db.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM notifications WHERE title=? AND status='unread'",
                (title,),
            ).fetchone()

            if existing:
                # 合并通知
                conn.execute(
                    "UPDATE notifications SET body=body||'\\n'||?, priority=max(priority,?) WHERE id=?",
                    (body, priority, existing["id"]),
                )
                return existing["id"]

            # 创建新通知
            conn.execute(
                "INSERT INTO notifications(title, body, item_type, item_id, priority) VALUES(?,?,?,?,?)",
                (title, body, item_type, item_id, priority),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def enqueue(self, title: str, body: str, item_type: str = "", item_id: int = None, priority: int = 5) -> int:
        """入队通知（公共接口）."""
        return self._enqueue_notification(title, body, item_type or "system", item_id, priority)

    # ===== 通知管理 =====

    def list_notifications(self, status: str = None, limit: int = 50) -> list[dict]:
        """列出通知."""
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM notifications"
            params: list = []

            if status:
                sql += " WHERE status=?"
                params.append(status)

            sql += " ORDER BY priority DESC, created_at DESC LIMIT ?"
            params.append(limit)

            return [dict(row) for row in conn.execute(sql, params)]

    def mark_read(self, notification_id: int) -> bool:
        """标记已读."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE notifications SET status='read' WHERE id=?",
                (notification_id,),
            )
            return cursor.rowcount > 0

    def mark_all_read(self) -> int:
        """标记所有已读."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute("UPDATE notifications SET status='read' WHERE status='unread'")
            return cursor.rowcount

    def snooze(self, notification_id: int, minutes: int = 60) -> bool:
        """延迟通知."""
        snooze_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        with self.repo.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE notifications SET status='snoozed', body=body||? WHERE id=?",
                (f"\n[延迟到 {snooze_until}]", notification_id),
            )
            return cursor.rowcount > 0

    def block_similar(self, notification_id: int) -> int:
        """屏蔽相似通知."""
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT title FROM notifications WHERE id=?", (notification_id,)).fetchone()
            if not row:
                return 0

            # 提取关键词（前 20 字符）
            keyword = row["title"][:20]
            cursor = conn.execute(
                "UPDATE notifications SET status='blocked' WHERE title LIKE ? AND status='unread'",
                (f"%{keyword}%",),
            )
            return cursor.rowcount

    def delete_notification(self, notification_id: int) -> bool:
        """删除通知."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute("DELETE FROM notifications WHERE id=?", (notification_id,))
            return cursor.rowcount > 0

    def get_unread_count(self) -> int:
        """获取未读通知数."""
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE status='unread'").fetchone()
            return row["c"] if row else 0

    def get_notification_stats(self) -> dict:
        """获取通知统计."""
        with self.repo.db.connect() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM notifications").fetchone()["c"]
            unread = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE status='unread'").fetchone()["c"]
            snoozed = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE status='snoozed'").fetchone()["c"]
            blocked = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE status='blocked'").fetchone()["c"]

            # 按优先级统计
            by_priority = conn.execute(
                "SELECT priority, COUNT(*) as c FROM notifications WHERE status='unread' GROUP BY priority ORDER BY priority DESC"
            ).fetchall()

            return {
                "total": total,
                "unread": unread,
                "snoozed": snoozed,
                "blocked": blocked,
                "by_priority": [{"priority": r["priority"], "count": r["c"]} for r in by_priority],
            }

    def process_snoozed_notifications(self) -> int:
        """处理延迟通知（检查是否到期）."""
        now = datetime.now().isoformat()
        with self.repo.db.connect() as conn:
            # 找到所有延迟通知
            rows = conn.execute(
                "SELECT id, body FROM notifications WHERE status='snoozed'"
            ).fetchall()

            activated = 0
            for row in rows:
                # 检查是否到期
                body = row["body"]
                match = re.search(r'\[延迟到 (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\]', body)
                if match:
                    snooze_until = match.group(1)
                    if now >= snooze_until:
                        # 激活通知
                        new_body = re.sub(r'\n\[延迟到 .+\]', '', body)
                        conn.execute(
                            "UPDATE notifications SET status='unread', body=? WHERE id=?",
                            (new_body, row["id"]),
                        )
                        activated += 1

            return activated
