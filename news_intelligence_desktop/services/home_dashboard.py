from __future__ import annotations

from datetime import date


class HomeDashboardService:
    def __init__(self, repo, quote_service=None, tech_service=None):
        self.repo = repo
        self.quote_service = quote_service
        self.tech_service = tech_service

    def generate(self) -> dict:
        articles = self.repo.list_articles(limit=30)
        quote = self.quote_service.get_home_quote() if self.quote_service else {"content": "今天也要加油！", "style_label": "每日语录"}
        tech_changes = self.tech_service.list_changes(limit=5) if self.tech_service else []

        categories = {}
        for art in articles:
            cat = art.get("category", "general")
            categories.setdefault(cat, []).append(art)

        cards = [
            {"name": "今日总览", "summary": f"已有 {len(articles)} 条本地内容", "count": len(articles), "items": articles[:5]},
            {"name": "技术变化", "summary": self._first_title(categories.get("tech", []), "暂无技术变化"), "count": len(categories.get("tech", [])), "items": categories.get("tech", [])[:5]},
            {"name": "重要新闻", "summary": self._first_title(categories.get("news", []), "暂无重要新闻"), "count": len(categories.get("news", [])), "items": categories.get("news", [])[:5]},
            {"name": "政策变化", "summary": self._first_title(categories.get("policy", []), "暂无政策变化"), "count": len(categories.get("policy", [])), "items": categories.get("policy", [])[:5]},
            {"name": "本地事件", "summary": self._first_title(categories.get("local", categories.get("accident", [])), "暂无本地事件"), "count": len(categories.get("local", categories.get("accident", []))), "items": categories.get("local", categories.get("accident", []))[:5]},
            {"name": "热点吃瓜", "summary": self._first_title(categories.get("hot", []), "暂无热点"), "count": len(categories.get("hot", [])), "items": categories.get("hot", [])[:5]},
            {"name": "天气地震", "summary": self._weather_summary(), "count": self._weather_count(), "items": []},
            {"name": "每日语录", "summary": quote.get("content", ""), "count": 1, "items": [], "quote": quote},
        ]

        return {
            "title": f"{date.today().isoformat()} 个人每日信息中枢",
            "date": date.today().isoformat(),
            "privacy_mode": self.repo.privacy_mode_enabled(),
            "cards": cards,
            "special_tabs": self.repo.list_special_tabs(),
            "tech_changes": tech_changes,
        }

    def _first_title(self, items: list[dict], fallback: str) -> str:
        return items[0]["title"] if items else fallback

    def _weather_summary(self) -> str:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM weather_forecasts ORDER BY collected_at DESC LIMIT 1").fetchone()
            if row:
                return f"{row['location_name']} {row['forecast_date']} {row['description']}"
        return "暂无天气数据"

    def _weather_count(self) -> int:
        with self.repo.db.connect() as conn:
            return conn.execute("SELECT COUNT(*) AS c FROM weather_forecasts").fetchone()["c"]
