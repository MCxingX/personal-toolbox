from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from news_intelligence_desktop.storage.repository import Repository, ArticleInput

logger = logging.getLogger(__name__)


class Collector:
    def __init__(self, repo: Repository):
        self.repo = repo

    def collect_all(self) -> dict:
        results = {"weather": 0, "earthquake": 0, "news": 0, "hot": 0, "tech": 0, "errors": []}
        
        try:
            results["weather"] = self._collect_weather()
        except Exception as e:
            results["errors"].append(f"weather: {e}")
        
        try:
            results["earthquake"] = self._collect_earthquake()
        except Exception as e:
            results["errors"].append(f"earthquake: {e}")
        
        try:
            results["news"] = self._collect_news()
        except Exception as e:
            results["errors"].append(f"news: {e}")
        
        try:
            results["hot"] = self._collect_hot()
        except Exception as e:
            results["errors"].append(f"hot: {e}")
        
        try:
            results["tech"] = self._collect_tech()
        except Exception as e:
            results["errors"].append(f"tech: {e}")
        
        return results

    def _collect_weather(self) -> int:
        from news_intelligence_desktop.connectors.weather_earthquake import WeatherConnector
        conn = WeatherConnector()
        result = conn.fetch_forecast()
        if result.ok:
            self.repo.record_source_success(1, result.response_ms)
            for item in result.data:
                with self.repo.db.connect() as db:
                    db.execute(
                        "INSERT OR REPLACE INTO weather_forecasts(location_name, latitude, longitude, forecast_date, temp_high, temp_low, description, source) VALUES(?,?,?,?,?,?,?,?)",
                        ("默认", item.get("lat"), item.get("lon"), item["date"], item.get("temp_high"), item.get("temp_low"), f"天气码{item.get('weathercode')}", "open-meteo"),
                    )
        else:
            self.repo.record_source_failure(1, result.error)
        return len(result.data)

    def _collect_earthquake(self) -> int:
        from news_intelligence_desktop.connectors.weather_earthquake import EarthquakeConnector
        conn = EarthquakeConnector()
        result = conn.fetch_recent()
        if result.ok:
            self.repo.record_source_success(2, result.response_ms)
            for item in result.data:
                with self.repo.db.connect() as db:
                    db.execute(
                        "INSERT OR IGNORE INTO earthquake_events(event_id, magnitude, latitude, longitude, depth_km, place, event_time, source, detail_url) VALUES(?,?,?,?,?,?,?,?,?)",
                        (item["event_id"], item["magnitude"], item["latitude"], item["longitude"], item["depth_km"], item["place"], item["event_time"], item["source"], item.get("detail_url", "")),
                    )
        else:
            self.repo.record_source_failure(2, result.error)
        return len(result.data)

    def _collect_news(self) -> int:
        from news_intelligence_desktop.connectors.news_rss import RssConnector
        from news_intelligence_desktop.connectors.extra_sources import MultiRssConnector
        
        rss = RssConnector()
        multi_rss = MultiRssConnector()
        total = 0
        
        # Basic feeds
        feeds = [
            ("https://36kr.com/feed", "36氪", "tech"),
            ("https://www.huxiu.com/rss/0.xml", "虎嗅", "tech"),
        ]
        
        for url, name, category in feeds:
            result = rss.fetch_feed(url, name)
            if result.ok:
                for item in result.data:
                    self.repo.add_article(ArticleInput(
                        title=item["title"], summary=item.get("summary", ""),
                        source_name=item.get("source_name", name), source_url=url,
                        url=item["url"], category=item.get("category", category),
                        published_at=item.get("published_at"),
                    ))
                total += len(result.data)
            else:
                logger.warning("RSS %s failed: %s", name, result.error)
        
        # Additional feeds from MultiRssConnector
        additional_feeds = ["bbc_zh", "hackernews", "sspai", "v2ex"]
        for feed_key in additional_feeds:
            result = multi_rss.fetch_feed(feed_key)
            if result.ok:
                for item in result.data[:15]:  # Limit per feed
                    self.repo.add_article(ArticleInput(
                        title=item["title"], summary=item.get("summary", ""),
                        source_name=item.get("source_name", feed_key), source_url=item.get("source_url", ""),
                        url=item["url"], category=item.get("category", "news"),
                        published_at=item.get("published_at"), language=item.get("language", "en"),
                    ))
                total += len(result.data[:15])
            else:
                logger.warning("RSS %s failed: %s", feed_key, result.error)
        
        return total

    def _collect_hot(self) -> int:
        from news_intelligence_desktop.connectors.news_rss import VvhanConnector
        conn = VvhanConnector()
        total = 0
        
        for type_ in ["hot", "weibo"]:
            result = conn.fetch_hot(type_)
            if result.ok:
                for item in result.data[:15]:
                    self.repo.add_article(ArticleInput(
                        title=item.get("title", ""), summary=item.get("summary", ""),
                        source_name=item.get("source_name", f"韩小韩-{type_}"),
                        source_url=item.get("source_url", ""), url=item.get("url", ""),
                        category="hot", importance_score=0.7,
                    ))
                total += len(result.data[:15])
        
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
