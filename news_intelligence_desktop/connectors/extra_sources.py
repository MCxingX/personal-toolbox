from __future__ import annotations

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class MultiRssConnector(BaseConnector):
    """Connector for multiple RSS feeds with built-in feed list."""
    
    FEEDS = {
        # 中文新闻源
        "36kr": ("https://36kr.com/feed", "36氪", "tech"),
        "huxiu": ("https://www.huxiu.com/rss/0.xml", "虎嗅", "tech"),
        "zhihu_hot": ("https://www.zhihu.com/rss", "知乎", "hot"),
        "v2ex": ("https://www.v2ex.com/index.xml", "V2EX", "tech"),
        "sspai": ("https://sspai.com/feed", "少数派", "tech"),
        "guokr": ("http://www.guokr.com/rss/", "果壳", "science"),
        "douban": ("https://www.douban.com/feed", "豆瓣", "culture"),
        
        # 国际新闻源
        "bbc_zh": ("https://feeds.bbci.co.uk/zhongwen/simp/rss.xml", "BBC中文", "news"),
        "nyt_zh": ("https://cn.nytimes.com/rss/", "纽约时报中文", "news"),
        "reuters": ("https://www.reutersagency.com/feed/", "路透社", "news"),
        "techcrunch": ("https://techcrunch.com/feed/", "TechCrunch", "tech"),
        "theverge": ("https://www.theverge.com/rss/index.xml", "The Verge", "tech"),
        "arstechnica": ("https://feeds.arstechnica.com/arstechnica/index", "Ars Technica", "tech"),
        "hackernews": ("https://hnrss.org/frontpage", "Hacker News", "tech"),
        "github_trending": ("https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml", "GitHub Trending", "tech"),
        
        # 安全资讯
        "freebuf": ("https://www.freebuf.com/feed", "FreeBuf", "security"),
        "securityweek": ("https://www.securityweek.com/feed", "SecurityWeek", "security"),
        
        # 开发者社区
        "devto": ("https://dev.to/feed", "DEV.to", "tech"),
        "medium_programming": ("https://medium.com/feed/tag/programming", "Medium Programming", "tech"),
        "css_tricks": ("https://css-tricks.com/feed/", "CSS-Tricks", "tech"),
        "smashing": ("https://www.smashingmagazine.com/feed/", "Smashing Magazine", "tech"),
        
        # 设计资源
        "dribbble": ("https://dribbble.com/shots/popular.rss", "Dribbble", "design"),
        "behance": ("https://www.behance.net/feeds/projects", "Behance", "design"),
    }
    
    def fetch_feed(self, feed_key: str) -> FetchResult:
        """Fetch a built-in feed by key."""
        if feed_key not in self.FEEDS:
            return FetchResult(False, [], f"Unknown feed: {feed_key}")
        url, name, category = self.FEEDS[feed_key]
        return self.fetch_url(url, name, category)
    
    def fetch_url(self, url: str, source_name: str = "rss", category: str = "news") -> FetchResult:
        """Fetch any RSS feed URL."""
        try:
            import feedparser
            code, text, ms = self._get_text(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            feed = feedparser.parse(text)
            results = []
            for entry in feed.entries[:50]:
                pub = entry.get("published", entry.get("updated", ""))
                summary = entry.get("summary", entry.get("description", ""))
                # Clean HTML from summary
                if summary and "<" in summary:
                    try:
                        from bs4 import BeautifulSoup
                        summary = BeautifulSoup(summary, "html.parser").get_text()[:500]
                    except Exception:
                        summary = summary[:500]
                results.append({
                    "title": entry.get("title", ""),
                    "summary": summary[:500],
                    "url": entry.get("link", ""),
                    "source_name": source_name,
                    "source_url": url,
                    "published_at": pub,
                    "category": category,
                    "language": self._detect_language(entry.get("title", "") + summary),
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
    
    def list_available_feeds(self) -> list[dict]:
        """List all available built-in feeds."""
        return [
            {"key": key, "url": url, "name": name, "category": cat}
            for key, (url, name, cat) in self.FEEDS.items()
        ]
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character ranges."""
        if not text:
            return "en"
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return "zh" if chinese_chars > len(text) * 0.1 else "en"


class NewsApiConnector(BaseConnector):
    """Connector for NewsAPI.org (free tier: 100 requests/day)."""
    
    BASE = "https://newsapi.org/v2"
    
    def __init__(self, apikey: str = "", timeout: int = 15):
        super().__init__(timeout)
        self.apikey = apikey
    
    def top_headlines(self, country: str = "us", category: str = "", page_size: int = 20) -> FetchResult:
        if not self.apikey:
            return FetchResult(False, [], "API key not configured")
        try:
            params = {"country": country, "pageSize": page_size, "apiKey": self.apikey}
            if category:
                params["category"] = category
            code, data, ms = self._get_json(f"{self.BASE}/top-headlines", params)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for art in data.get("articles", []):
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("description", "")[:500],
                    "url": art.get("url", ""),
                    "source_name": art.get("source", {}).get("name", "NewsAPI"),
                    "source_url": self.BASE,
                    "published_at": art.get("publishedAt", ""),
                    "category": category or "news",
                    "language": country,
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
    
    def everything(self, query: str, language: str = "en", page_size: int = 20) -> FetchResult:
        if not self.apikey:
            return FetchResult(False, [], "API key not configured")
        try:
            params = {"q": query, "language": language, "pageSize": page_size, "apiKey": self.apikey}
            code, data, ms = self._get_json(f"{self.BASE}/everything", params)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for art in data.get("articles", []):
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("description", "")[:500],
                    "url": art.get("url", ""),
                    "source_name": art.get("source", {}).get("name", "NewsAPI"),
                    "source_url": self.BASE,
                    "published_at": art.get("publishedAt", ""),
                    "category": "news",
                    "language": language,
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class DevToConnector(BaseConnector):
    """Connector for DEV.to public API (no key required)."""
    
    BASE = "https://dev.to/api"
    
    def fetch_articles(self, tag: str = "", top: int = 20) -> FetchResult:
        try:
            params = {"top": top}
            if tag:
                params["tag"] = tag
            code, data, ms = self._get_json(f"{self.BASE}/articles", params)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for art in data:
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("description", "")[:500],
                    "url": art.get("url", ""),
                    "source_name": "DEV.to",
                    "source_url": self.BASE,
                    "published_at": art.get("published_at", ""),
                    "category": "tech",
                    "tags": ",".join(art.get("tag_list", [])),
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class LobstersConnector(BaseConnector):
    """Connector for Lobsters (Hacker News alternative)."""
    
    BASE = "https://lobste.rs"
    
    def fetch_hot(self, limit: int = 25) -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/hottest.json")
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for item in data[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "summary": item.get("description", "")[:500],
                    "url": item.get("url", item.get("comments_url", "")),
                    "source_name": "Lobsters",
                    "source_url": self.BASE,
                    "published_at": item.get("created_at", ""),
                    "category": "tech",
                    "tags": ",".join(item.get("tags", [])),
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class RedditConnector(BaseConnector):
    """Connector for Reddit public JSON API (no key required)."""
    
    BASE = "https://www.reddit.com"
    
    def fetch_subreddit(self, subreddit: str, sort: str = "hot", limit: int = 25) -> FetchResult:
        try:
            headers = {"User-Agent": "NewsIntelligenceDesktop/0.2"}
            code, data, ms = self._get_json(f"{self.BASE}/r/{subreddit}/{sort}.json?limit={limit}", headers=headers)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                results.append({
                    "title": post.get("title", ""),
                    "summary": post.get("selftext", "")[:500],
                    "url": post.get("url", ""),
                    "source_name": f"r/{subreddit}",
                    "source_url": f"{self.BASE}/r/{subreddit}",
                    "published_at": "",
                    "category": "hot",
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class ArxivConnector(BaseConnector):
    """Connector for arXiv API (no key required)."""
    
    BASE = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, max_results: int = 20) -> FetchResult:
        try:
            import feedparser
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            code, text, ms = self._get_text(self.BASE, params=params)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            feed = feedparser.parse(text)
            results = []
            for entry in feed.entries:
                authors = [a.get("name", "") for a in entry.get("authors", [])]
                results.append({
                    "title": entry.get("title", "").replace("\n", " ").strip(),
                    "summary": entry.get("summary", "")[:500],
                    "url": entry.get("link", ""),
                    "source_name": "arXiv",
                    "source_url": self.BASE,
                    "published_at": entry.get("published", ""),
                    "category": "tech",
                    "tags": ",".join(authors[:3]),
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class WikipediaConnector(BaseConnector):
    """Connector for Wikipedia API (no key required)."""
    
    BASE = "https://en.wikipedia.org/api/rest_v1"
    
    def fetch_featured(self, date_str: str = "") -> FetchResult:
        try:
            if not date_str:
                from datetime import date
                date_str = date.today().isoformat()
            code, data, ms = self._get_json(f"{self.BASE}/feed/featured/{date_str}")
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for art in data.get("mostread", {}).get("articles", [])[:20]:
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("extract", "")[:500],
                    "url": f"https://en.wikipedia.org/wiki/{art.get('title', '').replace(' ', '_')}",
                    "source_name": "Wikipedia",
                    "source_url": self.BASE,
                    "published_at": date_str,
                    "category": "knowledge",
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class OpenLibraryConnector(BaseConnector):
    """Connector for Open Library API (no key required)."""
    
    BASE = "https://openlibrary.org"
    
    def trending(self, limit: int = 20) -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/trending/daily.json")
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for item in data.get("works", [])[:limit]:
                authors = [a.get("name", "") for a in item.get("authors", [])]
                results.append({
                    "title": item.get("title", ""),
                    "summary": f"作者: {', '.join(authors)}" if authors else "",
                    "url": f"{self.BASE}{item.get('key', '')}",
                    "source_name": "Open Library",
                    "source_url": self.BASE,
                    "published_at": "",
                    "category": "books",
                    "language": "en",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
