from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from news_intelligence_desktop.storage.repository import Repository, ArticleInput
from news_intelligence_desktop.config.china_cities import PROVINCE_CITIES
from news_intelligence_desktop.services.news_quality import enrich_summary, importance_score, normalize_text

logger = logging.getLogger(__name__)


DEFAULT_WEATHER_CITIES = {
    **PROVINCE_CITIES["北京市"],
    **PROVINCE_CITIES["上海市"],
    **PROVINCE_CITIES["天津市"],
    **PROVINCE_CITIES["重庆市"],
    **PROVINCE_CITIES["广西壮族自治区"],
    "广州": PROVINCE_CITIES["广东省"]["广州"],
    "深圳": PROVINCE_CITIES["广东省"]["深圳"],
    "杭州": PROVINCE_CITIES["浙江省"]["杭州"],
    "成都": PROVINCE_CITIES["四川省"]["成都"],
    "武汉": PROVINCE_CITIES["湖北省"]["武汉"],
    "南京": PROVINCE_CITIES["江苏省"]["南京"],
}


class Collector:
    def __init__(self, repo: Repository, settings=None):
        self.repo = repo
        self.settings = settings or {}

    def collect_all(self) -> dict:
        results = {"weather": 0, "earthquake": 0, "news": 0, "hot": 0, "tech": 0, "quote": 0, "custom": 0, "errors": []}
        jobs = {
            "weather": self._collect_weather,
            "earthquake": self._collect_earthquake,
            "news": self._collect_news,
            "hot": self._collect_hot,
            "tech": self._collect_tech,
            "quote": self._collect_quotes,
            "custom": self._collect_custom_sources,
        }
        # Limit workers to avoid overwhelming APIs, SQLite writes, and the desktop UI.
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {executor.submit(func): name for name, func in jobs.items()}
            for future in as_completed(future_map):
                name = future_map[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results["errors"].append(f"{name}: {e}")
        return results

    def _collect_weather(self) -> int:
        from news_intelligence_desktop.connectors.weather_earthquake import WeatherConnector, WttrConnector
        wttr = WttrConnector()
        open_meteo = WeatherConnector()
        source_id = self.repo.get_source_id("Open-Meteo") or 1
        total = 0
        errors = []
        for city in DEFAULT_WEATHER_CITIES:
            # 先用 wttr.in，失败再用 Open-Meteo
            result = wttr.fetch_weather(city)
            if not result.ok:
                lat, lon = DEFAULT_WEATHER_CITIES[city]
                result = open_meteo.fetch_forecast(lat=lat, lon=lon)
                src_name = "open-meteo"
            else:
                src_name = "wttr.in"
            if result.ok:
                self.repo.record_source_success(source_id, result.response_ms)
                total += len(result.data)
                with self.repo.db.connect() as db:
                    for item in result.data:
                        db.execute(
                            """INSERT OR REPLACE INTO weather_forecasts(location_name, latitude, longitude, forecast_date, temp_high, temp_low, description, weathercode, source)
                            VALUES(?,?,?,?,?,?,?,?,?)""",
                            (city, item.get("lat", 0), item.get("lon", 0), item.get("date", ""), item.get("temp_high"), item.get("temp_low"), item.get("description", ""), item.get("weathercode", 0), src_name),
                        )
            else:
                errors.append(f"{city}: {result.error}")
        if errors:
            self.repo.record_source_failure(source_id, "; ".join(errors[:3]))
        return total

    def _collect_custom_sources(self) -> int:
        from news_intelligence_desktop.connectors.news_rss import RssConnector
        from news_intelligence_desktop.connectors.generic_api import GenericApiCaller

        built_in_names = {
            "Open-Meteo", "USGS Earthquake", "GitHub Trending", "韩小韩 API", "GDELT",
            "DEV.to", "Lobsters", "CEIC地震台网", "百度新闻",
            "36氪 RSS", "IT之家 RSS", "开源中国 RSS", "InfoQ中文 RSS",
            "FreeBuf RSS", "少数派", "人民网 RSS",
            "澎湃新闻", "中国新闻网", "财新", "新浪国内", "凤凰资讯",
            "腾讯新闻", "联合早报", "环球时报", "中国日报", "广州日报", "经济观察报",
            "凤凰科技", "环球网科技", "环球网财经", "凤凰军事", "环球网军事",
        }
        sources = [s for s in self.repo.source_mgr.list_sources() if s.get("enabled") and s.get("name") not in built_in_names] if hasattr(self.repo, "source_mgr") else []
        if not sources:
            with self.repo.db.connect() as db:
                sources = [dict(r) for r in db.execute("SELECT * FROM source_configs WHERE enabled=1") if r["name"] not in built_in_names]

        total = 0
        rss = RssConnector()
        caller = GenericApiCaller()
        for src in sources:
            if src.get("type") == "rss":
                result = rss.fetch_feed(src["url"], src["name"])
                if result.ok:
                    self.repo.record_source_success(src["id"], result.response_ms)
                    for item in result.data[:30]:
                        title = normalize_text(item.get("title", ""), 180)
                        summary = enrich_summary(title, item.get("summary", ""), src["name"])
                        self.repo.add_article(ArticleInput(
                            title=title, summary=summary, source_name=src["name"],
                            source_url=src["url"], url=item.get("url", ""), category=src.get("category") or "news",
                            published_at=item.get("published_at"), language=item.get("language", "zh"),
                            importance_score=importance_score(title, summary, src.get("category") or "news", src["name"]),
                        ))
                    total += len(result.data[:30])
                else:
                    self.repo.record_source_failure(src["id"], result.error)
            elif src.get("type") == "api":
                data = caller.call(src["url"])
                if data.get("ok"):
                    self.repo.record_source_success(src["id"], data.get("response_time_ms", 0))
                    items = self._extract_article_items(data.get("data"))[:30]
                    for item in items:
                        title = normalize_text(item["title"], 180)
                        summary = enrich_summary(title, item.get("summary", ""), src["name"])
                        self.repo.add_article(ArticleInput(
                            title=title, summary=summary, source_name=src["name"], source_url=src["url"],
                            url=item.get("url") or src["url"], category=src.get("category") or "news", language="zh",
                            importance_score=importance_score(title, summary, src.get("category") or "news", src["name"]),
                        ))
                    total += len(items)
                else:
                    self.repo.record_source_failure(src["id"], data.get("error", "request failed"))
        return total

    def _extract_article_items(self, data) -> list[dict]:
        found = []

        def walk(value):
            if isinstance(value, dict):
                title = value.get("title") or value.get("name") or value.get("text")
                url = value.get("url") or value.get("link") or value.get("href")
                if title and (url or value.get("desc") or value.get("summary")):
                    found.append({"title": str(title), "summary": str(value.get("summary") or value.get("desc") or value.get("description") or "")[:500], "url": str(url or "")})
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)
        unique = []
        seen = set()
        for item in found:
            key = (item["title"], item.get("url", ""))
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    def _collect_earthquake(self) -> int:
        from news_intelligence_desktop.connectors.weather_earthquake import EarthquakeConnector, CeicRssConnector
        total = 0
        # USGS
        usgs = EarthquakeConnector()
        result = usgs.fetch_recent()
        source_id = self.repo.get_source_id("USGS Earthquake") or 2
        if result.ok:
            self.repo.record_source_success(source_id, result.response_ms)
            for item in result.data:
                with self.repo.db.connect() as db:
                    db.execute(
                        "INSERT OR IGNORE INTO earthquake_events(event_id, magnitude, latitude, longitude, depth_km, place, event_time, source, detail_url) VALUES(?,?,?,?,?,?,?,?,?)",
                        (item["event_id"], item["magnitude"], item["latitude"], item["longitude"], item["depth_km"], item["place"], item["event_time"], item["source"], item.get("detail_url", "")),
                    )
            total += len(result.data)
        else:
            self.repo.record_source_failure(source_id, result.error)
        # CEIC
        ceic = CeicRssConnector()
        ceic_result = ceic.fetch_recent()
        ceic_source_id = self.repo.get_source_id("CEIC地震台网") or 3
        if ceic_result.ok:
            self.repo.record_source_success(ceic_source_id, ceic_result.response_ms)
            for item in ceic_result.data:
                with self.repo.db.connect() as db:
                    db.execute(
                        "INSERT OR IGNORE INTO earthquake_events(event_id, magnitude, latitude, longitude, depth_km, place, event_time, source, detail_url) VALUES(?,?,?,?,?,?,?,?,?)",
                        (item["event_id"], item["magnitude"], item["latitude"], item["longitude"], item["depth_km"], item["place"], item["event_time"], item["source"], item.get("detail_url", "")),
                    )
            total += len(ceic_result.data)
        else:
            self.repo.record_source_failure(ceic_source_id, ceic_result.error)
        return total

    def _collect_news(self) -> int:
        from news_intelligence_desktop.connectors.news_rss import RssConnector

        rss = RssConnector()
        total = 0

        # 稳定可用的综合新闻源
        feeds = [
            # === 国内综合新闻 ===
            ("https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网", "news"),
            ("https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "Google News 中文", "news"),
            # === 政策 ===
            ("http://www.people.com.cn/rss/politics.xml", "人民网", "policy"),
            ("https://arstechnica.com/feed/", "Ars Technica", "policy"),
            # === 科技 ===
            ("https://36kr.com/feed", "36氪", "tech"),
            ("https://www.ithome.com/rss/", "IT之家", "tech"),
            ("https://www.oschina.net/news/rss", "开源中国", "tech"),
            ("https://www.infoq.cn/feed", "InfoQ中文", "tech"),
            ("http://tech.ifeng.com/rss/tech.xml", "凤凰科技", "tech"),
            ("https://rss.huanqiu.com/rss/tech.xml", "环球网科技", "tech"),
            ("https://sspai.com/feed", "少数派", "tech"),
            ("https://hnrss.org/frontpage?count=30", "Hacker News", "tech"),
            ("https://techcrunch.com/feed/", "TechCrunch", "tech"),
            ("https://www.theverge.com/rss/index.xml", "The Verge", "tech"),
            # === 安全 ===
            ("https://www.freebuf.com/feed", "FreeBuf", "security"),
            ("https://krebsonsecurity.com/feed/", "Krebs on Security", "security"),
            ("https://www.darkreading.com/rss.xml", "DarkReading", "security"),
            ("https://feeds.feedburner.com/TheHackersNews", "The Hacker News", "security"),
            ("https://www.schneier.com/feed/", "Schneier on Security", "security"),
            # === 财经 ===
            ("https://finance.yahoo.com/news/rssindex", "Yahoo Finance", "finance"),
            # === 军事 ===
            ("https://www.defensenews.com/rss/", "Defense News", "military"),
            # === 科学 ===
            ("https://www.nature.com/nature.rss", "Nature", "science"),
            ("https://export.arxiv.org/rss/cs", "arXiv CS", "science"),
            ("https://www.newscientist.com/feed/news", "New Scientist", "science"),
            ("https://phys.org/rss-feed/science-news/", "PhysOrg", "science"),
            ("https://www.space.com/feeds/all", "Space.com", "science"),
            ("https://www.sciencedaily.com/rss/all.xml", "Science Daily", "science"),
            # === 文化 ===
            ("https://lithub.com/feed/", "Literary Hub", "culture"),
            # === 猎奇/事故/本地 ===
            ("https://www.wired.com/feed/rss", "Wired", "odds"),
            ("https://www.mit.edu/~jmorin/feed/", "MIT Tech Review", "odds"),
        ]

        for url, name, category in feeds:
            result = rss.fetch_feed(url, name, default_category=category)
            if result.ok:
                for item in result.data:
                    title = normalize_text(item.get("title", ""), 180)
                    summary = enrich_summary(title, item.get("summary", ""), item.get("source_name", name))
                    published_at = item.get("published_at")
                    final_cat = item.get("category", category)
                    # 安全/财经/军事优先使用配置的分类，除非 RSS 有明确的标签
                    if category in ("security", "finance", "military", "science", "culture", "odds"):
                        final_cat = category
                    self.repo.add_article(ArticleInput(
                        title=title, summary=summary,
                        source_name=item.get("source_name", name), source_url=url,
                        url=item["url"], category=final_cat,
                        published_at=published_at, language="zh" if "zh" in url else item.get("language", "en"),
                        importance_score=importance_score(title, summary, final_cat, item.get("source_name", name)),
                    ))
                total += len(result.data)
            else:
                logger.warning("RSS %s failed: %s", name, result.error)

        return total

    def _collect_hot(self) -> int:
        from news_intelligence_desktop.connectors.news_rss import VvhanConnector, RssConnector
        from news_intelligence_desktop.services.news_quality import normalize_text

        total = 0
        vvhan = VvhanConnector()

        # 主源：韩小韩热榜（DNS 可能不可用）
        for type_ in ["wbHot", "baiduRD", "douyinHot", "zhihuHot", "bili", "ksHot", "toutiao"]:
            try:
                result = vvhan.fetch_hot(type_)
                if result.ok:
                    for item in result.data[:15]:
                        self.repo.add_article(ArticleInput(
                            title=item.get("title", ""), summary=item.get("summary", ""),
                            source_name=item.get("source_name", f"韩小韩-{type_}"),
                            source_url=item.get("source_url", ""), url=item.get("url", ""),
                            category="hot", importance_score=0.7,
                        ))
                    total += len(result.data[:15])
            except Exception:
                pass

        # 降级 1：从稳定 RSS 源按重要性提取热点
        if total < 10:
            rss = RssConnector()
            hot_feeds = [
                ("https://www.chinanews.com.cn/rss/scroll-news.xml", "中新网", "news"),
                ("https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "Google News 中文", "news"),
                ("https://36kr.com/feed", "36氪", "tech"),
                ("https://www.ithome.com/rss/", "IT之家", "tech"),
                ("http://www.people.com.cn/rss/politics.xml", "人民网", "policy"),
                ("https://www.freebuf.com/feed", "FreeBuf", "security"),
                ("https://www.oschina.net/news/rss", "开源中国", "tech"),
            ]

            hot_keywords = ["重磅", "突发", "热搜", "热议", "曝光", "首次", "重大", "紧急",
                          "最新", "刚刚", "热点", "热搜", "关注", "回应", "质疑", "争议",
                          "破纪录", "创新高", "涨停", "暴跌", "暴涨", "突发新闻",
                          "AI", "芯片", "发布", "升级", "突破", "上线", "下线", "警告",
                          "新规", "调整", "影响", "提醒"]

            articles_buffer = []
            for url, name, default_cat in hot_feeds:
                try:
                    result = rss.fetch_feed(url, name, default_category=default_cat)
                    if result.ok:
                        for item in result.data:
                            title = item.get("title", "")
                            summary = item.get("summary", "")
                            score = 0
                            title_lower = title.lower()
                            for kw in hot_keywords:
                                if kw in title:
                                    score += 3
                                elif kw.lower() in title_lower:
                                    score += 2
                                elif kw in summary:
                                    score += 1
                            if score == 0:
                                score = 1
                            articles_buffer.append({
                                "title": normalize_text(title, 180),
                                "summary": normalize_text(summary, 500),
                                "source_name": item.get("source_name", name),
                                "source_url": url,
                                "url": item.get("url", ""),
                                "score": score,
                            })
                except Exception:
                    pass

            articles_buffer.sort(key=lambda x: x["score"], reverse=True)
            for item in articles_buffer[:30]:
                self.repo.add_article(ArticleInput(
                    title=item["title"], summary=item["summary"],
                    source_name=item["source_name"], source_url=item["source_url"],
                    url=item["url"], category="hot",
                    importance_score=0.5 + min(item["score"] * 0.05, 0.5),
                ))
                total += 1

        # 降级 2：取已入库的重要度最高的新闻作为热点
        if total < 5:
            with self.repo.db.connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM articles WHERE category NOT IN ('hot','quote') "
                    "ORDER BY importance_score DESC, collected_at DESC LIMIT 20"
                ).fetchall()
                existing_titles = set()
                for row in rows:
                    row_dict = dict(row)
                    title = row_dict.get("title", "")
                    if title and title not in existing_titles:
                        existing_titles.add(title)
                        self.repo.add_article(ArticleInput(
                            title=title,
                            summary=row_dict.get("summary", ""),
                            source_name=row_dict.get("source_name", ""),
                            source_url=row_dict.get("source_url", ""),
                            url=row_dict.get("url", ""),
                            category="hot",
                            importance_score=0.5,
                        ))
                        total += 1

        return total

    def _collect_tech(self) -> int:
        from news_intelligence_desktop.connectors.extra_sources import DevToConnector, LobstersConnector, ArxivConnector
        
        total = 0
        
        # DEV.to articles
        devto = DevToConnector()
        result = devto.fetch_articles(top=15)
        if result.ok:
            for item in result.data:
                self.repo.add_article(ArticleInput(
                    title=item["title"], summary=item.get("summary", ""),
                    source_name="DEV.to", source_url=item.get("source_url", ""),
                    url=item["url"], category="tech",
                    published_at=item.get("published_at"), tags=item.get("tags", ""),
                    language=item.get("language", "en"),
                ))
            total += len(result.data)
        
        # Lobsters
        lobsters = LobstersConnector()
        result = lobsters.fetch_hot(limit=10)
        if result.ok:
            for item in result.data:
                self.repo.add_article(ArticleInput(
                    title=item["title"], summary=item.get("summary", ""),
                    source_name="Lobsters", source_url=item.get("source_url", ""),
                    url=item["url"], category="tech",
                    published_at=item.get("published_at"), tags=item.get("tags", ""),
                    language=item.get("language", "en"),
                ))
            total += len(result.data)
        
        return total

    def _collect_quotes(self) -> int:
        from news_intelligence_desktop.connectors.quote_rss import QuoteConnector
        from news_intelligence_desktop.connectors.news_rss import VvhanConnector

        connector = QuoteConnector()
        total = 0

        # 将 hitokoto 分类统一映射到 8 个核心学习风格
        hitokoto_map = [
            ("d", "thinking"), ("i", "thinking"), ("k", "thinking"), ("j", "life"),
            ("c", "learning"), ("e", "cognitive"), ("g", "life"), ("b", "thinking"),
        ]
        for category, style in hitokoto_map:
            result = connector.fetch_hitokoto(category)
            if result.ok:
                with self.repo.db.connect() as db:
                    for item in result.data:
                        content = item.get("content", "").strip()
                        if content and not db.execute("SELECT 1 FROM daily_quotes WHERE content=?", (content,)).fetchone():
                            author = (item.get("source") or item.get("author") or item.get("creator") or "hitokoto").strip()
                            db.execute(
                                "INSERT INTO daily_quotes(content, author, source, style, lesson, action) VALUES(?,?,?,?,?,?)",
                                (content, author, "hitokoto", style, "识别一句话背后的判断或情绪。", "把这句话改写成今天可以执行的一步。"),
                            )
                            total += 1

        # 韩小韩随机笑话
        vvhan = VvhanConnector()
        joke_result = vvhan.fetch_joke()
        if joke_result.ok:
            with self.repo.db.connect() as db:
                for item in joke_result.data:
                    content = item.get("content", "").strip()
                    if content and not db.execute("SELECT 1 FROM daily_quotes WHERE content=?", (content,)).fetchone():
                        db.execute(
                            "INSERT INTO daily_quotes(content, author, source, style, lesson, action) VALUES(?,?,?,?,?,?)",
                            (content, "", "vvhan", "life", "轻松一刻也是生活的一部分。", "把今天的烦恼写下来，然后撕掉它。"),
                        )
                        total += 1
        return total

    def _collect_tophub(self) -> int:
        """采集 TopHubData 热榜数据。

        使用用户配置的 API Key，如果未配置则跳过。
        """
        from news_intelligence_desktop.connectors.tophub import TopHubConnector

        # 从设置获取 API Key
        api_key = self.settings.get("tophub_api_key", "")
        if not api_key:
            return 0

        connector = TopHubConnector(api_key)
        total = 0

        # 获取全部榜单列表
        lists_result = connector.fetch_hot_lists()
        if not lists_result.ok:
            logger.warning("TopHub 获取榜单列表失败: %s", lists_result.error)
            return 0

        # 采集每个榜单的前 30 条
        for lst in lists_result.data[:20]:  # 限制采集 20 个榜单，避免超过 API 限制
            list_id = lst.get("list_id")
            if not list_id:
                continue

            items_result = connector.fetch_list_items(list_id, limit=30)
            if items_result.ok:
                for item in items_result.data:
                    title = normalize_text(item.get("title", ""), 180)
                    summary = normalize_text(item.get("summary", ""), 500)
                    self.repo.add_article(ArticleInput(
                        title=title, summary=summary,
                        source_name=item.get("source_name", "TopHub"),
                        source_url=item.get("source_url", ""),
                        url=item.get("url", ""),
                        category="hot",
                        importance_score=0.6 + (item.get("hot_value", 0) / 10000),
                        published_at=item.get("published_at"),
                    ))
                total += len(items_result.data)
            else:
                logger.warning("TopHub 榜单 %s 采集失败: %s", lst.get("title"), items_result.error)

        return total
