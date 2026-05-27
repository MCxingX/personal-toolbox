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
            count = conn.execute("SELECT COUNT(*) AS c FROM api_catalog").fetchone()["c"]
            if count > 0:
                return
            apis = [
                # 韩小韩 API
                ("韩小韩-热榜", "vvhan", "热榜", "聚合热榜数据", "No", 1, "unknown", "", "https://api.vvhan.com/api/hotlist/{type}", "enabled", "free", 60, "json"),
                ("韩小韩-天气", "vvhan", "天气", "天气查询", "No", 1, "unknown", "", "https://api.vvhan.com/api/weather", "enabled", "free", 60, "json"),
                ("韩小韩-笑话", "vvhan", "娱乐", "随机笑话", "No", 1, "unknown", "", "https://api.vvhan.com/api/joke", "enabled", "free", 60, "json"),
                ("韩小韩-每日一言", "vvhan", "语录", "每日一言", "No", 1, "unknown", "", "https://api.vvhan.com/api/ian", "enabled", "free", 60, "json"),
                ("韩小韩-随机壁纸", "vvhan", "图片", "随机壁纸", "No", 1, "unknown", "", "https://api.vvhan.com/api/bing", "enabled", "free", 60, "json"),
                
                # 枫雨 API
                ("枫雨-今日热门", "yuafeng", "热榜", "今日热门聚合", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/jinri_hot.php", "needs_config", "requires_key", 30, "json"),
                ("枫雨-腾讯新闻", "yuafeng", "新闻", "腾讯新闻热搜", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/txxw.php", "needs_config", "requires_key", 30, "json"),
                ("枫雨-文本审核", "yuafeng", "AI", "AI文本审核", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/aiwenben.php", "needs_config", "requires_key", 30, "json"),
                ("枫雨-天气查询", "yuafeng", "天气", "天气查询", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/tianqi.php", "needs_config", "requires_key", 30, "json"),
                ("枫雨-每日一言", "yuafeng", "语录", "每日一言", "apiKey", 1, "unknown", "", "https://api-v2.yuafeng.cn/API/yiyan.php", "needs_config", "requires_key", 30, "json"),
                
                # 免费 API
                ("Open-Meteo", "open-meteo", "天气", "免费天气API", "No", 1, "yes", "https://open-meteo.com/en/docs", "https://api.open-meteo.com/v1/forecast", "enabled", "free", 60, "json"),
                ("USGS地震", "usgs", "地震", "全球地震数据", "No", 1, "yes", "https://earthquake.usgs.gov/fdsnws/event/1/", "https://earthquake.usgs.gov/fdsnws/event/1/query", "enabled", "free", 60, "json"),
                ("GDELT", "gdelt", "新闻", "全球新闻搜索", "No", 1, "unknown", "https://blog.gdeltproject.org/gdelt-doc-2-0-api-discovery/", "https://api.gdeltproject.org/api/v2/doc/doc", "enabled", "free", 30, "json"),
                ("一言", "hitokoto", "语录", "随机语录API", "No", 1, "yes", "https://hitokoto.cn/api", "https://v1.hitokoto.cn", "enabled", "free", 60, "json"),
                ("DEV.to", "devto", "技术", "开发者社区API", "No", 1, "yes", "https://developers.forem.com/api", "https://dev.to/api", "enabled", "free", 30, "json"),
                ("Lobsters", "lobsters", "技术", "技术链接分享", "No", 1, "yes", "https://lobste.rs/about", "https://lobste.rs", "enabled", "free", 30, "json"),
                ("arXiv", "arxiv", "学术", "学术论文搜索", "No", 1, "yes", "https://info.arxiv.org/help/api/index.html", "http://export.arxiv.org/api/query", "enabled", "free", 30, "atom"),
                ("Wikipedia", "wikipedia", "知识", "维基百科API", "No", 1, "yes", "https://www.mediawiki.org/wiki/API:Main_page", "https://en.wikipedia.org/api/rest_v1", "enabled", "free", 60, "json"),
                ("Open Library", "openlibrary", "图书", "开放图书馆API", "No", 1, "yes", "https://openlibrary.org/developers/api", "https://openlibrary.org", "enabled", "free", 60, "json"),
                ("GitHub API", "github", "技术", "GitHub公开API", "No", 1, "yes", "https://docs.github.com/en/rest", "https://api.github.com", "enabled", "free", 60, "json"),
                ("JSONPlaceholder", "jsonplaceholder", "测试", "测试用REST API", "No", 1, "yes", "https://jsonplaceholder.typicode.com/", "https://jsonplaceholder.typicode.com", "enabled", "free", 60, "json"),
                
                # 需要 Key 的 API
                ("NewsAPI", "newsapi", "新闻", "全球新闻聚合", "apiKey", 1, "yes", "https://newsapi.org/docs", "https://newsapi.org/v2", "needs_config", "requires_key", 100, "json"),
                ("天行数据", "tianapi", "综合", "国内数据服务", "apiKey", 1, "unknown", "https://www.tianapi.com/apiview", "https://apis.tianapi.com", "needs_config", "requires_key", 30, "json"),
                ("聚合数据", "juhe", "综合", "国内数据服务", "apiKey", 1, "unknown", "https://www.juhe.cn/docs", "https://apis.juhe.cn", "needs_config", "requires_key", 30, "json"),
            ]
            for api in apis:
                conn.execute(
                    "INSERT INTO api_catalog(name, provider, category, description, auth_type, https, cors, docs_url, base_url, status, risk_tags, default_rate_limit, output_type) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
