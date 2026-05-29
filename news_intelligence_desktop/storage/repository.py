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
            sources = [
                ("Open-Meteo", "api", "weather", "https://open-meteo.com/"),
                ("USGS Earthquake", "api", "earthquake", "https://earthquake.usgs.gov/"),
                ("GitHub Trending", "web", "tech", "https://github.com/trending"),
                ("韩小韩 API", "api", "hot", "https://api.vvhan.com/"),
                ("GDELT", "api", "news", "https://api.gdeltproject.org/api/v2/doc/doc"),
                ("DEV.to", "api", "tech", "https://dev.to/api"),
                ("Lobsters", "api", "tech", "https://lobste.rs"),
                ("CEIC地震台网", "rss", "earthquake", "http://news.ceic.ac.cn/rss"),
                ("百度新闻", "api", "news", "https://news.baidu.com"),
                # 国内综合新闻
                ("澎湃新闻", "rss", "news", "https://www.thepaper.cn/rss_newsDetail.jsp"),
                ("中国新闻网", "rss", "news", "https://www.chinanews.com.cn/rss/scroll-news.xml"),
                ("财新", "rss", "news", "https://www.caixin.com/rss/"),
                ("新浪国内", "rss", "news", "http://rss.sina.com.cn/news/china/focus15.xml"),
                ("凤凰资讯", "rss", "news", "http://news.ifeng.com/rss/news.xml"),
                ("腾讯新闻", "rss", "news", "http://www.qq.com/rss/"),
                ("联合早报", "rss", "news", "https://www.zaobao.com/rss"),
                ("环球时报", "rss", "news", "https://rss.huanqiu.com/rss/china.xml"),
                ("中国日报", "rss", "news", "http://www.chinadaily.com.cn/rss/china_rss.xml"),
                ("广州日报", "rss", "news", "http://www.gzdaily.com/rss/gzb.xml"),
                ("经济观察报", "rss", "news", "http://www.eeo.com.cn/rss/rss.xml"),
                # 政策
                ("人民网", "rss", "policy", "http://www.people.com.cn/rss/politics.xml"),
                # 科技
                ("36氪", "rss", "tech", "https://36kr.com/feed"),
                ("IT之家", "rss", "tech", "https://www.ithome.com/rss/"),
                ("开源中国", "rss", "tech", "https://www.oschina.net/news/rss"),
                ("InfoQ中文", "rss", "tech", "https://www.infoq.cn/feed"),
                ("凤凰科技", "rss", "tech", "http://tech.ifeng.com/rss/tech.xml"),
                ("环球网科技", "rss", "tech", "https://rss.huanqiu.com/rss/tech.xml"),
                ("少数派", "rss", "tech", "https://sspai.com/feed"),
                # 安全
                ("FreeBuf", "rss", "security", "https://www.freebuf.com/feed"),
                # 财经
                ("环球网财经", "rss", "finance", "https://rss.huanqiu.com/rss/finance.xml"),
                # 军事
                ("凤凰军事", "rss", "military", "http://mil.ifeng.com/rss/mil.xml"),
                ("环球网军事", "rss", "military", "https://rss.huanqiu.com/rss/mil.xml"),
            ]
            if count == 0:
                conn.executemany("INSERT INTO source_configs(name, type, category, url) VALUES(?,?,?,?)", sources)
            else:
                for source in sources:
                    exists = conn.execute("SELECT 1 FROM source_configs WHERE name=?", (source[0],)).fetchone()
                    if not exists:
                        conn.execute("INSERT INTO source_configs(name, type, category, url) VALUES(?,?,?,?)", source)

            articles = conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
            if articles == 0:
                for item in default_articles():
                    self._insert_article(conn, item)

            quotes = conn.execute("SELECT COUNT(*) AS c FROM daily_quotes").fetchone()["c"]
            if quotes == 0:
                default_quotes = [
                    ("先定义问题，再寻找答案。", "", "thinking", "很多低效来自解错问题。", "把当前最烦的事改写成一个可执行问题。"),
                    ("复盘只问三件事：发生了什么、为什么、下次怎么做。", "", "productivity", "复盘面向改进，而非自责。", "用 3 行写完今天一次小复盘。"),
                    ("阅读新闻时区分事实、观点、推测。", "", "media", "事实可核验，观点需辨别立场，推测需要等待证据。", "打开一篇新闻，标出一句事实和一句观点。"),
                ]
                for content, author, style, lesson, action in default_quotes:
                    conn.execute("INSERT INTO daily_quotes(content, author, source, style, lesson, action) VALUES(?,?,?,?,?,?)", (content, author, "local", style, lesson, action))

            conn.execute("INSERT OR IGNORE INTO privacy_mode_state(id, enabled) VALUES(1, 0)")

    def get_source_id(self, name: str) -> int | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT id FROM source_configs WHERE name=?", (name,)).fetchone()
            return int(row["id"]) if row else None

    def add_article(self, article: ArticleInput) -> int:
        with self.db.connect() as conn:
            return self._insert_article(conn, article)

    def _insert_article(self, conn, article: ArticleInput) -> int:
        duplicate = conn.execute(
            "SELECT id FROM articles WHERE title=? AND source_name=?",
            (article.title, article.source_name),
        ).fetchone()
        if duplicate:
            return int(duplicate["id"])
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
        # 优先按 collected_at DESC 排序，确保最新采集的内容排前面
        sql += " ORDER BY collected_at DESC, COALESCE(published_at, '') DESC, id DESC LIMIT ?"
        params.append(limit)
        with self.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def count_articles(self, category: str | None = None) -> int:
        sql = "SELECT COUNT(*) AS c FROM articles"
        params: list = []
        if category:
            sql += " WHERE category=?"
            params.append(category)
        with self.db.connect() as conn:
            return int(conn.execute(sql, params).fetchone()["c"])

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

    def get_pref(self, key: str, default: str = "") -> str:
        with self.db.connect() as conn:
            row = conn.execute("SELECT value FROM user_prefs WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def set_pref(self, key: str, value: str) -> None:
        with self.db.connect() as conn:
            conn.execute("INSERT INTO user_prefs(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    # ===== 网页来源管理 =====

    def add_web_source(self, name: str, url: str, rules: dict = None) -> int:
        """添加网页来源."""
        rules = rules or {}
        with self.db.connect() as conn:
            conn.execute(
                """INSERT INTO web_page_sources(name, url, url_pattern, title_selector, link_selector,
                summary_selector, content_selector, date_selector, author_selector, item_selector,
                use_xpath, encoding, max_items, remove_selectors, category)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    name, url,
                    rules.get("url_pattern", ""),
                    rules.get("title_selector", ""),
                    rules.get("link_selector", "a[href]"),
                    rules.get("summary_selector", ""),
                    rules.get("content_selector", ""),
                    rules.get("date_selector", ""),
                    rules.get("author_selector", ""),
                    rules.get("item_selector", ""),
                    1 if rules.get("use_xpath") else 0,
                    rules.get("encoding", ""),
                    rules.get("max_items", 30),
                    json.dumps(rules.get("remove_selectors", []), ensure_ascii=False),
                    rules.get("category", "web"),
                ),
            )
            row = conn.execute("SELECT id FROM web_page_sources WHERE url=?", (url,)).fetchone()
            return int(row["id"]) if row else 0

    def get_web_source(self, source_id: int) -> dict | None:
        """获取网页来源."""
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM web_page_sources WHERE id=?", (source_id,)).fetchone()
            if row:
                result = dict(row)
                result["remove_selectors"] = json.loads(result.get("remove_selectors", "[]"))
                return result
            return None

    def get_web_source_by_url(self, url: str) -> dict | None:
        """根据 URL 获取网页来源."""
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM web_page_sources WHERE url=?", (url,)).fetchone()
            if row:
                result = dict(row)
                result["remove_selectors"] = json.loads(result.get("remove_selectors", "[]"))
                return result
            return None

    def list_web_sources(self, enabled_only: bool = True) -> list[dict]:
        """列出网页来源."""
        with self.db.connect() as conn:
            if enabled_only:
                rows = conn.execute("SELECT * FROM web_page_sources WHERE enabled=1 ORDER BY name").fetchall()
            else:
                rows = conn.execute("SELECT * FROM web_page_sources ORDER BY name").fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result["remove_selectors"] = json.loads(result.get("remove_selectors", "[]"))
                results.append(result)
            return results

    def update_web_source(self, source_id: int, **kwargs) -> bool:
        """更新网页来源."""
        allowed = {"name", "url", "url_pattern", "title_selector", "link_selector", "summary_selector",
                   "content_selector", "date_selector", "author_selector", "item_selector",
                   "use_xpath", "encoding", "max_items", "remove_selectors", "category", "enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        if "remove_selectors" in updates and isinstance(updates["remove_selectors"], list):
            updates["remove_selectors"] = json.dumps(updates["remove_selectors"], ensure_ascii=False)
        if "use_xpath" in updates:
            updates["use_xpath"] = 1 if updates["use_xpath"] else 0

        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [source_id]

        with self.db.connect() as conn:
            cursor = conn.execute(f"UPDATE web_page_sources SET {set_clause} WHERE id=?", values)
            return cursor.rowcount > 0

    def delete_web_source(self, source_id: int) -> bool:
        """删除网页来源."""
        with self.db.connect() as conn:
            cursor = conn.execute("DELETE FROM web_page_sources WHERE id=?", (source_id,))
            return cursor.rowcount > 0

    def update_web_source_fetch_time(self, source_id: int, error: str = "") -> None:
        """更新网页来源采集时间."""
        with self.db.connect() as conn:
            if error:
                conn.execute(
                    "UPDATE web_page_sources SET last_fetch_at=CURRENT_TIMESTAMP, last_error=? WHERE id=?",
                    (error, source_id)
                )
            else:
                conn.execute(
                    "UPDATE web_page_sources SET last_fetch_at=CURRENT_TIMESTAMP, last_error='' WHERE id=?",
                    (source_id,)
                )


def default_articles() -> list[ArticleInput]:
    return [
        ArticleInput(title="AI 工具更新：本地每日信息中枢原型完成", summary="技术变化卡片会优先展示 AI、开源、框架和安全方向的变化。", source_name="本地示例源", source_url="https://example.com/tech", url="https://example.com/tech/ai-local-dashboard", category="tech", content="Release Changelog Breaking Change AI open source framework security", credibility_score=0.75, importance_score=0.8),
        ArticleInput(title="今日政策观察：个人信息和数据安全仍是重点", summary="政策变化卡片会聚合全国、本地和行业政策更新。", source_name="本地示例源", source_url="https://example.com/policy", url="https://example.com/policy/data-security", category="policy", credibility_score=0.7, importance_score=0.7),
        ArticleInput(title="每日语录：你已经在认真生活了，今天也可以轻一点", summary="别委屈模式会提供低压力、温和的鼓励内容。", source_name="本地语录库", source_url="local://quotes", url="local://quotes/default-encourage", category="quote", credibility_score=1.0, importance_score=0.4),
        ArticleInput(title="Python 3.13 发布：性能提升和新特性", summary="Python 最新版本带来了性能优化和新的语言特性。", source_name="技术媒体", source_url="https://python.org", url="https://example.com/python-313", category="tech", tags="python,release", credibility_score=0.9, importance_score=0.7),
        ArticleInput(title="开源框架重大更新：React 19 正式发布", summary="React 19 带来了新的并发特性和性能改进。", source_name="技术媒体", source_url="https://react.dev", url="https://example.com/react-19", category="tech", tags="react,frontend", credibility_score=0.85, importance_score=0.75),
        ArticleInput(title="今日热点：互联网大厂动态汇总", summary="多家互联网公司发布重要产品更新和组织调整。", source_name="新闻聚合", source_url="https://example.com/hot", url="https://example.com/hot/internet", category="hot", credibility_score=0.6, importance_score=0.6),
    ]
