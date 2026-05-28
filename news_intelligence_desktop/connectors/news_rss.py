from __future__ import annotations

from news_intelligence_desktop.connectors import BaseConnector, FetchResult
from news_intelligence_desktop.services.news_quality import normalize_text


class RssConnector(BaseConnector):
    def fetch_feed(self, url: str, source_name: str = "rss", default_category: str = "news") -> FetchResult:
        try:
            import feedparser
            code, text, ms = self._get_text(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            feed = feedparser.parse(text)
            results = []
            for entry in feed.entries[:50]:
                pub = entry.get("published", entry.get("updated", ""))
                # 优先使用 RSS 自带的分类标签，如果没有则使用传入的 default_category
                rss_cats = entry.get("tags", [])
                cat = default_category
                if rss_cats:
                    # 取第一个标签的 term 作为分类
                    for t in rss_cats:
                        term = t.get("term", "").lower()
                        if term:
                            # 映射常见 RSS 分类到内部分类
                            if term in ("tech", "technology", "it", "dev", "code", "programming"):
                                cat = "tech"
                            elif term in ("politics", "policy", "law", "government"):
                                cat = "policy"
                            elif term in ("finance", "business", "economy", "money"):
                                cat = "finance"
                            elif term in ("military", "defense"):
                                cat = "military"
                            elif term in ("security", "hack", "bug"):
                                cat = "security"
                            elif term in ("science",):
                                cat = "science"
                            elif term in ("news",):
                                cat = "news"
                            break
                results.append({
                    "title": normalize_text(entry.get("title", ""), 180),
                    "summary": normalize_text(entry.get("summary", entry.get("description", "")), 500),
                    "url": entry.get("link", ""),
                    "source_name": source_name,
                    "source_url": url,
                    "published_at": pub,
                    "category": cat,
                    "language": "zh",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class VvhanConnector(BaseConnector):
    BASE = "https://api.vvhan.com/api"

    def fetch_hot(self, type_: str = "hot") -> FetchResult:
        url = f"{self.BASE}/hotlist/{type_}"
        try:
            code, data, ms = self._get_json(url)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for item in (data.get("data") or [])[:30]:
                results.append({
                    "title": item.get("title", item.get("name", "")),
                    "summary": item.get("desc", item.get("hot", "")),
                    "url": item.get("url", item.get("link", "")),
                    "source_name": f"韩小韩-{type_}",
                    "source_url": url,
                    "category": "hot",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_weather(self, city: str = "南宁") -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/weather", {"city": city})
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            result = {
                "city": city,
                "temp_high": int(data.get("high", 0)),
                "temp_low": int(data.get("low", 0)),
                "weathercode": 0,
                "description": data.get("type", ""),
                "source": "vvhan",
            }
            return FetchResult(True, [result], response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_joke(self) -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/joke/randJoke")
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for item in (data.get("data") or [])[:5]:
                results.append({
                    "content": item.get("content", item.get("joke", "")),
                    "source": "vvhan",
                    "style": "humor",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class GdeltConnector(BaseConnector):
    BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search(self, query: str, max_records: int = 20) -> FetchResult:
        try:
            code, data, ms = self._get_json(self.BASE, {
                "query": query, "mode": "ArtList", "maxrecords": max_records, "format": "json",
            })
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for art in data.get("articles", []):
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("seendate", "") + " " + (art.get("socialimage", "") or ""),
                    "url": art.get("url", ""),
                    "source_name": art.get("domain", "gdelt"),
                    "source_url": self.BASE,
                    "published_at": art.get("seendate", ""),
                    "category": "news",
                    "language": art.get("language", "en"),
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class YuafengConnector(BaseConnector):
    BASE = "https://api-v2.yuafeng.cn"

    def fetch_today_hot(self, apikey: str, action: str = "zhihu_hot", page: int = 1) -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/API/jinri_hot.php", {
                "apikey": apikey, "action": action, "page": page,
            })
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            items = data.get("data", []) if isinstance(data, dict) else []
            for item in items[:30]:
                results.append({
                    "title": item.get("title", ""),
                    "summary": item.get("desc", item.get("hot", "")),
                    "url": item.get("url", item.get("link", "")),
                    "source_name": f"枫雨-{action}",
                    "source_url": f"{self.BASE}/API/jinri_hot.php",
                    "category": "hot",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def review_text(self, apikey: str, text: str) -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/API/aiwenben.php", {
                "apikey": apikey, "text": text,
            })
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            return FetchResult(True, [data] if isinstance(data, dict) else [], response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
