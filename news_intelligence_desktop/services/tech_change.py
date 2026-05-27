from __future__ import annotations

import json
from datetime import date


class TechChangeService:
    CHANNELS = ["ai", "opensource", "language", "framework", "cloud", "security", "enterprise"]

    def __init__(self, repo):
        self.repo = repo

    def detect_and_store(self) -> int:
        articles = self.repo.list_articles(category="tech", limit=100)
        count = 0
        from news_intelligence_desktop.analysis import detect_tech_change
        for art in articles:
            result = detect_tech_change(art["title"], art.get("summary", ""))
            if result:
                with self.repo.db.connect() as conn:
                    conn.execute(
                        "INSERT INTO tech_changes(title, summary, channel, impact, source_url, source_name, change_type, published_at, importance) VALUES(?,?,?,?,?,?,?,?,?)",
                        (art["title"], art.get("summary", ""), ",".join(result["change_types"]), "", art.get("url", ""), art.get("source_name", ""), ",".join(result["change_types"]), art.get("published_at"), result["importance"]),
                    )
                count += 1
        return count

    def list_changes(self, channel: str | None = None, limit: int = 50) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM tech_changes"
            params: list = []
            if channel:
                sql += " WHERE channel LIKE ?"
                params.append(f"%{channel}%")
            sql += " ORDER BY COALESCE(published_at, collected_at) DESC, id DESC LIMIT ?"
            params.append(limit)
            return [dict(row) for row in conn.execute(sql, params)]

    def get_channels(self) -> list[dict]:
        labels = {"ai": "AI", "opensource": "开源", "language": "编程语言", "framework": "框架", "cloud": "云服务", "security": "安全", "enterprise": "大厂动态"}
        return [{"key": k, "label": labels.get(k, k)} for k in self.CHANNELS]
