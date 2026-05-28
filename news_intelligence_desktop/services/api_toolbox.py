from __future__ import annotations

import json
from datetime import datetime


class ApiToolboxService:
    PROVIDERS = {
        "vvhan": {"name": "韩小韩 API", "base": "https://api.vvhan.com", "tier": 1},
        "yuafeng": {"name": "枫雨 API", "base": "https://api-v2.yuafeng.cn", "tier": 2},
        "tianapi": {"name": "天行数据", "base": "https://apis.tianapi.com", "tier": 2},
        "juhe": {"name": "聚合数据", "base": "https://apis.juhe.cn", "tier": 2},
    }

    def __init__(self, repo):
        self.repo = repo

    def seed_catalog(self) -> None:
        with self.repo.db.connect() as conn:
            apis = [
                # 韩小韩 API
                ("韩小韩-热榜", "vvhan", "热榜", "聚合热榜数据", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/{type}", "enabled", "free", 60, "json", "built_in", "", "hot"),
                ("韩小韩-天气", "vvhan", "天气", "天气查询", "No", 1, "unknown", "", "https://api.vvhan.com/api/weather", "enabled", "free", 60, "json", "built_in", "", "weather"),
                ("韩小韩-笑话", "vvhan", "娱乐", "随机笑话", "No", 1, "unknown", "", "https://api.vvhan.com/api/joke/randJoke", "enabled", "free", 60, "json", "built_in", "", "quote"),
                ("韩小韩-每日一言", "vvhan", "语录", "每日一言", "No", 1, "unknown", "", "https://api.vvhan.com/api/ian", "enabled", "free", 60, "json", "built_in", "", "quote"),
                ("韩小韩-随机壁纸", "vvhan", "图片", "随机壁纸", "No", 1, "unknown", "", "https://api.vvhan.com/api/bing", "enabled", "free", 60, "json", "built_in", "", "media"),
                ("韩小韩-微博热搜", "vvhan", "热榜", "微博热搜榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/wbHot", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-百度热搜", "vvhan", "热榜", "百度热搜榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/baiduRD", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-抖音热榜", "vvhan", "热榜", "抖音热搜榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/douyinHot", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-知乎热榜", "vvhan", "热榜", "知乎热榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/zhihuHot", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-B站热榜", "vvhan", "热榜", "B站热门榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/bili", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-快手热榜", "vvhan", "热榜", "快手热榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/ksHot", "enabled", "free", 30, "json", "built_in", "", "hot"),
                ("韩小韩-头条热榜", "vvhan", "热榜", "头条热榜", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/toutiao", "enabled", "free", 30, "json", "built_in", "", "hot"),

                # 枫雨 API
                ("枫雨-今日热门", "yuafeng", "热榜", "今日热门聚合", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/jinri_hot.php", "needs_config", "requires_key", 30, "json", "built_in", "", "hot"),
                ("枫雨-腾讯新闻", "yuafeng", "新闻", "腾讯新闻热搜", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/txxw.php", "needs_config", "requires_key", 30, "json", "built_in", "", "news"),
                ("枫雨-文本审核", "yuafeng", "AI", "AI文本审核", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/aiwenben.php", "needs_config", "requires_key", 30, "json", "built_in", "", "tool"),
                ("枫雨-天气查询", "yuafeng", "天气", "天气查询", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/tianqi.php", "needs_config", "requires_key", 30, "json", "built_in", "", "weather"),
                ("枫雨-每日一言", "yuafeng", "语录", "每日一言", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/yiyan.php", "needs_config", "requires_key", 30, "json", "built_in", "", "quote"),

                # 免费 API
                ("Open-Meteo", "open-meteo", "天气", "免费天气API", "No", 1, "yes", "https://open-meteo.com/en/docs", "https://api.open-meteo.com/v1/forecast", "enabled", "free", 60, "json", "built_in", "", "weather"),
                ("wttr.in天气", "wttr", "天气", "免费天气查询，支持中文城市名", "No", 1, "yes", "https://wttr.in", "https://wttr.in", "enabled", "free", 60, "json", "built_in", "", "weather"),
                ("USGS地震", "usgs", "地震", "全球地震数据", "No", 1, "yes", "https://earthquake.usgs.gov/fdsnws/event/1/", "https://earthquake.usgs.gov/fdsnws/event/1/query", "enabled", "free", 60, "json", "built_in", "", "earthquake"),
                ("CEIC地震台网", "ceic", "地震", "中国地震台网实时速报", "No", 1, "yes", "http://news.ceic.ac.cn", "http://news.ceic.ac.cn/rss", "enabled", "free", 60, "rss", "built_in", "", "earthquake"),
                ("GDELT", "gdelt", "新闻", "全球新闻搜索", "No", 1, "unknown", "https://blog.gdeltproject.org/gdelt-doc-2-0-api-discovery/", "https://api.gdeltproject.org/api/v2/doc/doc", "enabled", "free", 30, "json", "built_in", "", "news"),
                ("一言", "hitokoto", "语录", "随机语录API", "No", 1, "yes", "https://hitokoto.cn/api", "https://v1.hitokoto.cn", "enabled", "free", 60, "json", "built_in", "", "quote"),
                ("DEV.to", "devto", "技术", "开发者社区API", "No", 1, "yes", "https://developers.forem.com/api", "https://dev.to/api", "enabled", "free", 30, "json", "built_in", "", "tech"),
                ("Lobsters", "lobsters", "技术", "技术链接分享", "No", 1, "yes", "https://lobste.rs/about", "https://lobste.rs", "enabled", "free", 30, "json", "built_in", "", "tech"),
                ("arXiv", "arxiv", "学术", "学术论文搜索", "No", 1, "yes", "https://info.arxiv.org/help/api/index.html", "http://export.arxiv.org/api/query", "enabled", "free", 30, "atom", "built_in", "", "tech"),
                ("Wikipedia", "wikipedia", "知识", "维基百科API", "No", 1, "yes", "https://www.mediawiki.org/wiki/API:Main_page", "https://en.wikipedia.org/api/rest_v1", "enabled", "free", 60, "json", "built_in", "", "tool"),
                ("Open Library", "openlibrary", "图书", "开放图书馆API", "No", 1, "yes", "https://openlibrary.org/developers/api", "https://openlibrary.org", "enabled", "free", 60, "json", "built_in", "", "tool"),
                ("GitHub API", "github", "技术", "GitHub公开API", "No", 1, "yes", "https://docs.github.com/en/rest", "https://api.github.com", "enabled", "free", 60, "json", "built_in", "", "tech"),
                ("百度新闻搜索", "baidu", "新闻", "百度新闻关键词搜索", "No", 1, "yes", "https://news.baidu.com", "https://www.baidu.com/s", "enabled", "free", 60, "html", "built_in", "", "news"),
                ("JSONPlaceholder", "jsonplaceholder", "测试", "测试用REST API", "No", 1, "yes", "https://jsonplaceholder.typicode.com/", "https://jsonplaceholder.typicode.com", "enabled", "free", 60, "json", "built_in", "", "tool"),

                # 国内新闻 RSS 源（已验证可用 2026-05）
                ("澎湃新闻", "thepaper", "新闻", "澎湃新闻RSS", "No", 1, "yes", "https://www.thepaper.cn", "https://www.thepaper.cn/rss_newsDetail.jsp", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("中国新闻网", "chinanews", "新闻", "中国新闻网滚动新闻", "No", 1, "yes", "https://www.chinanews.com.cn", "https://www.chinanews.com.cn/rss/scroll-news.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("财新", "caixin", "新闻", "财新网RSS", "No", 1, "yes", "https://www.caixin.com", "https://www.caixin.com/rss/", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("新浪国内", "sina_cn", "新闻", "新浪国内焦点新闻", "No", 1, "yes", "http://rss.sina.com.cn", "http://rss.sina.com.cn/news/china/focus15.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("凤凰资讯", "ifeng_news", "新闻", "凤凰新闻资讯", "No", 1, "yes", "http://news.ifeng.com", "http://news.ifeng.com/rss/news.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("腾讯新闻", "qq_news", "新闻", "腾讯新闻RSS", "No", 1, "yes", "http://www.qq.com", "http://www.qq.com/rss/", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("联合早报", "zaobao", "新闻", "联合早报RSS", "No", 1, "yes", "https://www.zaobao.com", "https://www.zaobao.com/rss", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("环球时报", "huanqiu_cn", "新闻", "环球时报国内新闻", "No", 1, "yes", "https://rss.huanqiu.com", "https://rss.huanqiu.com/rss/china.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("中国日报", "chinadaily", "新闻", "中国日报RSS", "No", 1, "yes", "http://www.chinadaily.com.cn", "http://www.chinadaily.com.cn/rss/china_rss.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("广州日报", "gzdaily", "新闻", "广州日报RSS", "No", 1, "yes", "http://www.gzdaily.com", "http://www.gzdaily.com/rss/gzb.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("经济观察报", "eeo", "财经", "经济观察报RSS", "No", 1, "yes", "http://www.eeo.com.cn", "http://www.eeo.com.cn/rss/rss.xml", "enabled", "free", 60, "rss", "built_in", "", "news"),
                ("凤凰科技", "ifeng_tech", "科技", "凤凰科技RSS", "No", 1, "yes", "http://tech.ifeng.com", "http://tech.ifeng.com/rss/tech.xml", "enabled", "free", 60, "rss", "built_in", "", "tech"),
                ("环球网科技", "huanqiu_tech", "科技", "环球网科技RSS", "No", 1, "yes", "https://rss.huanqiu.com", "https://rss.huanqiu.com/rss/tech.xml", "enabled", "free", 60, "rss", "built_in", "", "tech"),
                ("环球网财经", "huanqiu_finance", "财经", "环球网财经RSS", "No", 1, "yes", "https://rss.huanqiu.com", "https://rss.huanqiu.com/rss/finance.xml", "enabled", "free", 60, "rss", "built_in", "", "finance"),
                ("凤凰军事", "ifeng_mil", "军事", "凤凰军事RSS", "No", 1, "yes", "http://mil.ifeng.com", "http://mil.ifeng.com/rss/mil.xml", "enabled", "free", 60, "rss", "built_in", "", "military"),
                ("环球网军事", "huanqiu_mil", "军事", "环球网军事RSS", "No", 1, "yes", "https://rss.huanqiu.com", "https://rss.huanqiu.com/rss/mil.xml", "enabled", "free", 60, "rss", "built_in", "", "military"),

                # 需要 Key 的 API
                ("NewsAPI", "newsapi", "新闻", "全球新闻聚合", "apiKey", 1, "yes", "https://newsapi.org/docs", "https://newsapi.org/v2", "needs_config", "requires_key", 100, "json", "built_in", "", "news"),
                ("天行数据", "tianapi", "综合", "国内数据服务", "apiKey", 1, "unknown", "https://www.tianapi.com/apiview", "https://apis.tianapi.com", "needs_config", "requires_key", 30, "json", "built_in", "", "news"),
                ("聚合数据", "juhe", "综合", "国内数据服务", "apiKey", 1, "unknown", "https://www.juhe.cn/docs", "https://apis.juhe.cn", "needs_config", "requires_key", 30, "json", "built_in", "", "news"),
            ]
            count = conn.execute("SELECT COUNT(*) AS c FROM api_catalog").fetchone()["c"]
            if count == 0:
                for api in apis:
                    conn.execute(
                        "INSERT INTO api_catalog(name, provider, category, description, auth_type, https, cors, docs_url, base_url, status, risk_tags, default_rate_limit, output_type, api_kind, api_key, target_module) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        api,
                    )
            else:
                for api in apis:
                    exists = conn.execute("SELECT 1 FROM api_catalog WHERE name=?", (api[0],)).fetchone()
                    if not exists:
                        conn.execute(
                            "INSERT INTO api_catalog(name, provider, category, description, auth_type, https, cors, docs_url, base_url, status, risk_tags, default_rate_limit, output_type, api_kind, api_key, target_module) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            api,
                        )

    def list_apis(self, category: str | None = None, provider: str | None = None) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM api_catalog WHERE 1=1"
            params: list = []
            if category:
                sql += " AND category = ?"
                params.append(category)
            if provider:
                sql += " AND provider = ?"
                params.append(provider)
            sql += " ORDER BY provider, name"
            return [dict(row) for row in conn.execute(sql, params)]

    def get_api(self, api_id: int) -> dict | None:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM api_catalog WHERE id=?", (api_id,)).fetchone()
            return dict(row) if row else None

    def toggle_api(self, api_id: int, status: str) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("UPDATE api_catalog SET status=? WHERE id=?", (status, api_id))

    def _validation_target(self, api: dict) -> tuple[str, dict]:
        provider = (api.get("provider") or "").lower()
        name = api.get("name", "")
        url = (api.get("base_url") or "").strip()
        params: dict = {}
        if provider == "open-meteo":
            params = {"latitude": 39.9042, "longitude": 116.4074, "daily": "temperature_2m_max", "forecast_days": 1}
        elif provider == "usgs":
            params = {"format": "geojson", "limit": 1}
        elif provider == "gdelt":
            params = {"query": "china", "mode": "ArtList", "maxrecords": 1, "format": "json"}
        elif provider == "hitokoto":
            params = {"encode": "json"}
        elif provider == "devto":
            url = "https://dev.to/api/articles"
            params = {"top": 1}
        elif provider == "lobsters":
            url = "https://lobste.rs/hottest.json"
        elif provider == "arxiv":
            params = {"search_query": "all:python", "start": 0, "max_results": 1}
        elif provider == "wikipedia":
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/Python_(programming_language)"
        elif provider == "openlibrary":
            url = "https://openlibrary.org/trending/daily.json"
            params = {"limit": 1}
        elif provider == "github":
            url = "https://api.github.com/repos/python/cpython"
        elif provider == "baidu":
            params = {"wd": "科技", "tn": "news"}
        elif provider == "jsonplaceholder":
            url = "https://jsonplaceholder.typicode.com/posts/1"
        elif provider == "wttr":
            url = "https://wttr.in/北京"
            params = {"format": "j1"}
        elif provider == "vvhan":
            if "热榜" in name or "微博" in name:
                url = "https://api.vvhan.com/api/hotlist/wbHot"
            elif "百度" in name:
                url = "https://api.vvhan.com/api/hotlist/baiduRD"
            elif "抖音" in name:
                url = "https://api.vvhan.com/api/hotlist/douyinHot"
            elif "知乎" in name:
                url = "https://api.vvhan.com/api/hotlist/zhihuHot"
            elif "B站" in name:
                url = "https://api.vvhan.com/api/hotlist/bili"
            elif "快手" in name:
                url = "https://api.vvhan.com/api/hotlist/ksHot"
            elif "头条" in name:
                url = "https://api.vvhan.com/api/hotlist/toutiao"
            elif "天气" in name:
                url = "https://api.vvhan.com/api/weather"
                params = {"city": "北京"}
            elif "笑话" in name:
                url = "https://api.vvhan.com/api/joke/randJoke"
            elif "每日一言" in name:
                url = "https://api.vvhan.com/api/ian"
        if "{" in url or "}" in url:
            url = url.replace("{type}", "wbHot").replace("{城市}", "北京").replace("{city}", "北京")
        return url, params

    def validate_api(self, api: dict) -> dict:
        """Validate an API/RSS entry with a lightweight real request."""
        if api.get("auth_type") != "No" and not api.get("api_key"):
            self.save_api(api["id"], status="needs_config", risk_tags="requires_key")
            return {"ok": False, "status": "needs_config", "message": "需要配置 API Key"}

        url, params = self._validation_target(api)
        if not url or "{" in url or "}" in url:
            self.save_api(api["id"], status="needs_config", risk_tags="needs_params")
            return {"ok": False, "status": "needs_config", "message": "需要参数后才能检测"}

        output_type = (api.get("output_type") or "json").lower()
        try:
            if output_type in {"rss", "atom"}:
                import feedparser
                import requests
                resp = requests.get(url, params=params, timeout=8, headers={"User-Agent": "NewsIntelligenceDesktop/0.3"})
                feed = feedparser.parse(resp.text) if resp.status_code < 400 else None
                ok = bool(resp.status_code < 400 and feed and feed.entries)
                msg = f"HTTP {resp.status_code}, {len(feed.entries) if feed else 0} 条"
            else:
                import requests
                resp = requests.get(url, params=params, timeout=8, headers={"User-Agent": "NewsIntelligenceDesktop/0.3"})
                ok = resp.status_code < 400 and bool(resp.content)
                msg = f"HTTP {resp.status_code}, {len(resp.content)} bytes"
            self.save_api(api["id"], status="enabled" if ok else "disabled", risk_tags="free" if ok else msg[:80])
            return {"ok": ok, "status": "enabled" if ok else "disabled", "message": msg}
        except Exception as e:
            msg = str(e)[:80]
            self.save_api(api["id"], status="disabled", risk_tags=msg)
            return {"ok": False, "status": "disabled", "message": msg}

    def validate_all_enabled_free(self) -> dict:
        apis = [a for a in self.list_apis() if a.get("auth_type") == "No" and a.get("api_kind") == "built_in"]
        results = []
        for api in apis:
            results.append({"name": api.get("name", ""), **self.validate_api(api)})
        return {
            "total": len(results),
            "ok": sum(1 for r in results if r["ok"]),
            "failed": [r for r in results if not r["ok"]],
            "results": results,
        }

    def log_call(self, api_id: int, endpoint: str, params: dict, status_code: int | None, response_size: int, response_time_ms: float, success: bool, error: str = "") -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO api_call_logs(api_id, endpoint, params, status_code, response_size, response_time_ms, success, error) VALUES(?,?,?,?,?,?,?,?)",
                (api_id, endpoint, json.dumps(params, ensure_ascii=False), status_code, response_size, response_time_ms, int(success), error),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def list_call_logs(self, api_id: int | None = None, limit: int = 50) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM api_call_logs"
            params: list = []
            if api_id:
                sql += " WHERE api_id = ?"
                params.append(api_id)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            return [dict(row) for row in conn.execute(sql, params)]

    def list_categories(self) -> list[str]:
        with self.repo.db.connect() as conn:
            return [row["category"] for row in conn.execute("SELECT DISTINCT category FROM api_catalog ORDER BY category")]

    def save_api(self, api_id: int, **fields) -> None:
        allowed = {"name", "provider", "category", "description", "auth_type", "docs_url", "base_url", "status", "risk_tags", "default_rate_limit", "output_type", "api_kind", "api_key", "target_module"}
        updates = []
        params = []
        for key, value in fields.items():
            if key not in allowed:
                raise ValueError(f"Invalid API field: {key}")
            updates.append(f"{key}=?")
            params.append(value)
        if not updates:
            return
        params.append(api_id)
        with self.repo.db.connect() as conn:
            conn.execute(f"UPDATE api_catalog SET {', '.join(updates)} WHERE id=?", params)

    def add_external_api(self, name: str, provider: str, category: str, base_url: str, target_module: str = "news", description: str = "", auth_type: str = "No", api_key: str = "") -> int:
        status = "enabled" if auth_type == "No" or api_key else "needs_config"
        with self.repo.db.connect() as conn:
            conn.execute(
                """INSERT INTO api_catalog(name, provider, category, description, auth_type, base_url, status, risk_tags, output_type, api_kind, api_key, target_module)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name, provider, category, description, auth_type, base_url, status, "external", "json", "external", api_key, target_module),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
