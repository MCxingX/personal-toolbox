from __future__ import annotations

import json
import time
import requests

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class QuoteConnector(BaseConnector):
    HITOKOTO = "https://v1.hitokoto.cn"

    def fetch_hitokoto(self, c: str = "d") -> FetchResult:
        try:
            code, data, ms = self._get_json(self.HITOKOTO, {"c": c, "encode": "json"})
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            return FetchResult(True, [{
                "content": data.get("hitokoto", ""),
                "author": data.get("from_who", ""),
                "source": "hitokoto",
                "style": "philosophy",
            }], response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class RssNewsConnector(BaseConnector):
    def fetch_rss(self, url: str, source_name: str = "rss") -> FetchResult:
        try:
            import feedparser
            code, text, ms = self._get_text(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            feed = feedparser.parse(text)
            results = []
            for entry in feed.entries[:30]:
                results.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:500],
                    "url": entry.get("link", ""),
                    "source_name": source_name,
                    "source_url": url,
                    "published_at": entry.get("published", entry.get("updated", "")),
                    "category": "news",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
