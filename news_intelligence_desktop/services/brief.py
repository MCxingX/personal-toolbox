from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from news_intelligence_desktop.services.news_quality import news_digest_line, parse_news_time


class BriefService:
    SECTIONS = ["技术变化", "重要新闻", "政策变化", "本地事件", "热点吃瓜", "天气地震", "每日语录"]
    CATEGORY_MAP = {"技术变化": "tech", "重要新闻": "news", "政策变化": "policy", "本地事件": "local", "热点吃瓜": "hot", "天气地震": "earthquake"}

    def __init__(self, repo, quote_service=None):
        self.repo = repo
        self.quote_service = quote_service

    def generate(self, brief_type: str, brief_date: date | None = None) -> dict:
        brief_date = brief_date or date.today()
        articles = self._recent_articles(self.repo.list_articles(limit=200), brief_date)
        articles = sorted(
            articles,
            key=lambda a: (
                1 if a.get("language") == "zh" else 0,
                float(a.get("importance_score", 0)),
                parse_news_time(a.get("published_at") or a.get("collected_at")) or datetime.min,
            ),
            reverse=True,
        )
        sections: dict[str, list[dict]] = {s: [] for s in self.SECTIONS}
        for art in articles:
            cat = art.get("category", "")
            if cat == "tech":
                sections["技术变化"].append(art)
            elif cat == "news":
                sections["重要新闻"].append(art)
            elif cat == "policy":
                sections["政策变化"].append(art)
            elif cat in ("local", "accident"):
                sections["本地事件"].append(art)
            elif cat == "hot":
                sections["热点吃瓜"].append(art)
            elif cat == "earthquake":
                sections["天气地震"].append(art)

        lines = [f"# {brief_date.isoformat()} {brief_type}", "", "覆盖范围：今天和昨天的高价值信息，优先展示有时间、来源、数字和明确影响的内容。", ""]
        for section in self.SECTIONS:
            lines.append(f"## {section}")
            items = sections.get(section, [])
            if items:
                for art in items[:6]:
                    lines.append(news_digest_line(art))
            else:
                lines.append("- 暂无内容")
            lines.append("")

        if self.quote_service:
            q = self.quote_service.get_quote()
            lines.append(f"## 每日语录")
            lines.append(f"> {q['content']}")
            if q.get("author"):
                lines.append(f"> —— {q['author']}")

        body = "\n".join(lines)
        title = f"{brief_date.isoformat()} {brief_type}"

        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_briefs(brief_type, brief_date, title, body) VALUES(?,?,?,?)",
                (brief_type, brief_date.isoformat(), title, body),
            )
            row = conn.execute("SELECT * FROM daily_briefs WHERE brief_type=? AND brief_date=?", (brief_type, brief_date.isoformat())).fetchone()
            return dict(row)

    def _recent_articles(self, articles: list[dict], brief_date: date) -> list[dict]:
        start = datetime.combine(brief_date - timedelta(days=1), datetime.min.time())
        end = datetime.combine(brief_date + timedelta(days=1), datetime.min.time())
        recent = []
        unknown_time = []
        for art in articles:
            dt = parse_news_time(art.get("published_at") or art.get("collected_at"))
            if dt is None:
                unknown_time.append(art)
            elif start <= dt < end:
                recent.append(art)
        if recent:
            return recent + unknown_time[:20]
        return articles[:80]

    def list_briefs(self, brief_type: str | None = None) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM daily_briefs"
            params: list = []
            if brief_type:
                sql += " WHERE brief_type = ?"
                params.append(brief_type)
            sql += " ORDER BY brief_date DESC LIMIT 30"
            return [dict(row) for row in conn.execute(sql, params)]

    def get_brief(self, brief_type: str, brief_date: str) -> dict | None:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM daily_briefs WHERE brief_type=? AND brief_date=?", (brief_type, brief_date)).fetchone()
            return dict(row) if row else None
