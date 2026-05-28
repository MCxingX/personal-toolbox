from __future__ import annotations

from datetime import date


class HomeDashboardService:
    def __init__(self, repo, quote_service=None, tech_service=None):
        self.repo = repo
        self.quote_service = quote_service
        self.tech_service = tech_service

    def generate(self) -> dict:
        # 分别从各分类获取数据，避免某单一分类占满 limit
        tech_articles = self.repo.list_articles(category="tech", limit=10)
        news_articles = self.repo.list_articles(category="news", limit=15)
        policy_articles = self.repo.list_articles(category="policy", limit=10)
        hot_articles = self.repo.list_articles(category="hot", limit=10)
        all_articles = tech_articles + news_articles + policy_articles + hot_articles

        quote = self.quote_service.get_home_quote() if self.quote_service else {"content": "今天也要加油！", "style_label": "每日语录"}
        tech_changes = self.tech_service.list_changes(limit=5) if self.tech_service else []

        cards = [
            {"name": "今日总览", "summary": f"已有 {len(all_articles)} 条本地内容", "count": len(all_articles), "items": all_articles[:5]},
            {"name": "技术变化", "summary": self._first_title(tech_articles, "暂无技术变化"), "count": len(tech_articles), "items": tech_articles[:5]},
            {"name": "重要新闻", "summary": self._first_title(news_articles, "暂无重要新闻"), "count": len(news_articles), "items": news_articles[:5]},
            {"name": "政策变化", "summary": self._first_title(policy_articles, "暂无政策变化"), "count": len(policy_articles), "items": policy_articles[:5]},
            {"name": "本地事件", "summary": self._first_title(hot_articles, "暂无本地事件"), "count": len(hot_articles), "items": hot_articles[:5]},
            {"name": "热点吃瓜", "summary": self._first_title(hot_articles, "暂无热点"), "count": len(hot_articles), "items": hot_articles[:5]},
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
