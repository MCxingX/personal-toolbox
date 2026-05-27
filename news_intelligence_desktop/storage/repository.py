from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class ArticleInput:
    title: str
    summary: str
    source_name: str
    source_url: str
    url: str
    category: str = "news"
    content: str = ""
    published_at: str | None = None
    credibility_score: float = 0.6
    importance_score: float = 0.5
    region: str = ""
    channel: str = ""
    language: str = "zh"
    tags: str = ""


class Repository:
    def __init__(self, db):
        self.db = db

    def seed_defaults(self) -> None:
        with self.db.connect() as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM source_configs").fetchone()["c"]
            if count == 0:
                sources = [
                    ("Open-Meteo", "api", "weather", "https://open-meteo.com/"),
                    ("USGS Earthquake", "api", "earthquake", "https://earthquake.usgs.gov/"),
                    ("GitHub Trending", "web", "tech", "https://github.com/trending"),
                    ("韩小韩 API", "api", "hot", "https://api.vvhan.com/"),
                    ("36氪 RSS", "rss", "news", "https://36kr.com/feed"),
                    ("虎嗅 RSS", "rss", "news", "https://www.huxiu.com/rss/0.xml"),
                    ("GDELT", "api", "news", "https://api.gdeltproject.org/api/v2/doc/doc"),
                    ("BBC中文 RSS", "rss", "news", "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"),
                    ("Hacker News", "rss", "tech", "https://hnrss.org/frontpage"),
                    ("少数派", "rss", "tech", "https://sspai.com/feed"),
                    ("V2EX", "rss", "tech", "https://www.v2ex.com/index.xml"),
                    ("DEV.to", "api", "tech", "https://dev.to/api"),
                    ("Lobsters", "api", "tech", "https://lobste.rs"),
                ]
                conn.executemany("INSERT INTO source_configs(name, type, category, url) VALUES(?,?,?,?)", sources)

            articles = conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
            if articles == 0:
                for item in default_articles():
                    self._insert_article(conn, item)

            quotes = conn.execute("SELECT COUNT(*) AS c FROM daily_quotes").fetchone()["c"]
            if quotes == 0:
                default_quotes = [
                    ("你已经在认真生活了，今天也可以轻一点。", "", "encourage"),
                    ("不必事事完美，能走到这里已经很好了。", "", "comfort"),
                    ("今天也是元气满满的一天！", "", "happy"),
                    ("代码写不出来的时候，先去喝杯水。", "", "tech"),
                    ("人生苦短，我用 Python。", "Tim Peters", "tech"),
                    ("Talk is cheap. Show me the code.", "Linus Torvalds", "tech"),
                    ("每一个不曾起舞的日子，都是对生命的辜负。", "尼采", "philosophy"),
                    ("先完成，再完美。", "", "encourage"),
                    ("没有 bug 的代码是不存在的，包括这段话。", "", "humor"),
                    ("种一棵树最好的时间是十年前，其次是现在。", "", "encourage"),
                ]
                for content, author, style in default_quotes:
                    conn.execute("INSERT INTO daily_quotes(content, author, source, style) VALUES(?,?,?,?)", (content, author, "local", style))

            conn.execute("INSERT OR IGNORE INTO privacy_mode_state(id, enabled) VALUES(1, 0)")

    def add_article(self, article: ArticleInput) -> int:
        with self.db.connect() as conn:
            return self._insert_article(conn, article)

    def _insert_article(self, conn, article: ArticleInput) -> int:
        conn.execute(
            """INSERT OR IGNORE INTO articles(title, summary, content, source_name, source_url, url, category, tags, published_at, credibility_score, importance_score, region, channel, language)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (article.title, article.summary, article.content, article.source_name, article.source_url,
             article.url, article.category, article.tags, article.published_at, article.credibility_score,
             article.importance_score, article.region, article.channel, article.language),
        )
        row = conn.execute("SELECT id FROM articles WHERE url=?", (article.url,)).fetchone()
        if not row:
            return 0
        aid = int(row["id"])
        conn.execute("INSERT OR IGNORE INTO search_index(item_type, item_id, title, body, tags, source) VALUES('article',?,?,?,?,?)",
                     (aid, article.title, f"{article.summary}\n{article.content}", article.category, article.source_name))
        conn.execute("INSERT OR REPLACE INTO credibility_explanations(item_type, item_id, score, explanation) VALUES('article',?,?,?)",
                     (aid, article.credibility_score, self._cred_explanation(article.credibility_score, article.source_name)))
        return aid

    def list_articles(self, category: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM articles"
        params: list = []
        if category:
            sql += " WHERE category=?"
            params.append(category)
        sql += " ORDER BY COALESCE(published_at, collected_at) DESC, id DESC LIMIT ?"
        params.append(limit)
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def get_article(self, article_id: int) -> dict | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
            return dict(row) if row else None

    def record_source_success(self, source_id: int, response_ms: float) -> None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM source_health_metrics WHERE source_id=?", (source_id,)).fetchone()
            if not row:
                conn.execute("INSERT INTO source_health_metrics(source_id, success_count, avg_response_ms, last_success_at) VALUES(?,?,?,CURRENT_TIMESTAMP)", (source_id, 1, response_ms))
            else:
                cnt = row["success_count"] + 1
                avg = ((row["avg_response_ms"] * row["success_count"]) + response_ms) / cnt
                conn.execute("UPDATE source_health_metrics SET success_count=?, avg_response_ms=?, last_success_at=CURRENT_TIMESTAMP, paused=0 WHERE source_id=?", (cnt, avg, source_id))

    def record_source_failure(self, source_id: int, error: str) -> None:
        with self.db.connect() as conn:
            conn.execute("""INSERT INTO source_health_metrics(source_id, failure_count, last_error, paused) VALUES(?,?,?,0)
                ON CONFLICT(source_id) DO UPDATE SET failure_count=failure_count+1, last_error=excluded.last_error,
                paused=CASE WHEN failure_count+1>=3 THEN 1 ELSE paused END""", (source_id, 1, error))

    def privacy_mode_enabled(self) -> bool:
        with self.db.connect() as conn:
            row = conn.execute("SELECT enabled FROM privacy_mode_state WHERE id=1").fetchone()
            return bool(row and row["enabled"])

    def list_special_tabs(self) -> list[dict]:
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM special_favorite_sources WHERE enabled=1 ORDER BY tab_order, id")]

    def _cred_explanation(self, score: float, source: str) -> str:
        if score >= 0.8:
            return f"可信度较高：来源 {source} 稳定。"
        if score >= 0.5:
            return f"可信度中等：来源 {source} 可用，建议结合原始链接确认。"
        return f"待确认：来源 {source} 支撑较弱。"


def default_articles() -> list[ArticleInput]:
    return [
        ArticleInput(title="AI 工具更新：本地每日信息中枢原型完成", summary="技术变化卡片会优先展示 AI、开源、框架和安全方向的变化。", source_name="本地示例源", source_url="https://example.com/tech", url="https://example.com/tech/ai-local-dashboard", category="tech", content="Release Changelog Breaking Change AI open source framework security", credibility_score=0.75, importance_score=0.8),
        ArticleInput(title="今日政策观察：个人信息和数据安全仍是重点", summary="政策变化卡片会聚合全国、本地和行业政策更新。", source_name="本地示例源", source_url="https://example.com/policy", url="https://example.com/policy/data-security", category="policy", credibility_score=0.7, importance_score=0.7),
        ArticleInput(title="每日语录：你已经在认真生活了，今天也可以轻一点", summary="别委屈模式会提供低压力、温和的鼓励内容。", source_name="本地语录库", source_url="local://quotes", url="local://quotes/default-encourage", category="quote", credibility_score=1.0, importance_score=0.4),
        ArticleInput(title="Python 3.13 发布：性能提升和新特性", summary="Python 最新版本带来了性能优化和新的语言特性。", source_name="技术媒体", source_url="https://python.org", url="https://example.com/python-313", category="tech", tags="python,release", credibility_score=0.9, importance_score=0.7),
        ArticleInput(title="开源框架重大更新：React 19 正式发布", summary="React 19 带来了新的并发特性和性能改进。", source_name="技术媒体", source_url="https://react.dev", url="https://example.com/react-19", category="tech", tags="react,frontend", credibility_score=0.85, importance_score=0.75),
        ArticleInput(title="今日热点：互联网大厂动态汇总", summary="多家互联网公司发布重要产品更新和组织调整。", source_name="新闻聚合", source_url="https://example.com/hot", url="https://example.com/hot/internet", category="hot", credibility_score=0.6, importance_score=0.6),
    ]
