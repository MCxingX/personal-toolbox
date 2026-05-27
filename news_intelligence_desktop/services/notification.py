from __future__ import annotations

import json
from datetime import date, datetime


class NotificationService:
    def __init__(self, repo):
        self.repo = repo

    def create_rule(self, name: str, keywords: list[str], categories: list[str] | None = None, frequency: str = "instant") -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO subscription_rules(name, keywords, categories, frequency) VALUES(?,?,?,?)",
                (name, json.dumps(keywords, ensure_ascii=False), json.dumps(categories or [], ensure_ascii=False), frequency),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def list_rules(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM subscription_rules ORDER BY id")]

    def match_article(self, article: dict) -> list[dict]:
        matches = []
        with self.repo.db.connect() as conn:
            rules = conn.execute("SELECT * FROM subscription_rules WHERE enabled = 1").fetchall()
        for rule in rules:
            keywords = json.loads(rule["keywords"])
            categories = json.loads(rule["categories"])
            haystack = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')}"
            keyword_match = any(kw.lower() in haystack.lower() for kw in keywords)
            category_match = not categories or article.get("category", "") in categories
            if keyword_match and category_match:
                matches.append({"rule_id": rule["id"], "rule_name": rule["name"], "article_id": article.get("id")})
        return matches

    def enqueue(self, title: str, body: str, item_type: str = "", item_id: int | None = None, priority: int = 5) -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO notifications(title, body, item_type, item_id, priority) VALUES(?,?,?,?,?)",
                (title, body, item_type, item_id, priority),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def list_notifications(self, status: str | None = None, limit: int = 50) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM notifications"
            params: list = []
            if status:
                sql += " WHERE status = ?"
                params.append(status)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            return [dict(row) for row in conn.execute(sql, params)]

    def mark_read(self, notification_id: int) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("UPDATE notifications SET status = 'read' WHERE id = ?", (notification_id,))

    def snooze(self, notification_id: int) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("UPDATE notifications SET status = 'snoozed' WHERE id = ?", (notification_id,))

    def block_similar(self, notification_id: int) -> None:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
            if row:
                conn.execute("UPDATE notifications SET status = 'blocked' WHERE title LIKE ?", (f"%{row['title'][:20]}%",))
