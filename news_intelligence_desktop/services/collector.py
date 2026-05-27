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
        results = {"weather": 0, "earthquake": 0, "news": 0, "hot": 0, "errors": []}
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
        rss = RssConnector()
        feeds = [
            ("https://36kr.com/feed", "36氪"),
            ("https://www.huxiu.com/rss/0.xml", "虎嗅"),
        ]
        total = 0
        for url, name in feeds:
            result = rss.fetch_feed(url, name)
            if result.ok:
                for item in result.data:
                    self.repo.add_article(ArticleInput(
                        title=item["title"], summary=item.get("summary", ""),
                        source_name=item.get("source_name", name), source_url=url,
                        url=item["url"], category=item.get("category", "news"),
                        published_at=item.get("published_at"),
                    ))
                total += len(result.data)
            else:
                logger.warning("RSS %s failed: %s", name, result.error)
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
