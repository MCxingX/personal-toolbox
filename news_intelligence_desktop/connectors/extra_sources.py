from __future__ import annotations

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class MultiRssConnector(BaseConnector):
    """Connector for multiple RSS feeds with built-in feed list."""
    
    FEEDS = {
        # 国内综合新闻（已验证可用 2026-05）
        "thepaper": ("https://www.thepaper.cn/rss_newsDetail.jsp", "澎湃新闻", "news"),
        "chinanews": ("https://www.chinanews.com.cn/rss/scroll-news.xml", "中国新闻网", "news"),
        "caixin": ("https://www.caixin.com/rss/", "财新", "news"),
        "sina_cn": ("http://rss.sina.com.cn/news/china/focus15.xml", "新浪国内", "news"),
        "ifeng_news": ("http://news.ifeng.com/rss/news.xml", "凤凰资讯", "news"),
        "qq_news": ("http://www.qq.com/rss/", "腾讯新闻", "news"),
        "zaobao": ("https://www.zaobao.com/rss", "联合早报", "news"),
        "huanqiu_cn": ("https://rss.huanqiu.com/rss/china.xml", "环球时报", "news"),
        "chinadaily": ("http://www.chinadaily.com.cn/rss/china_rss.xml", "中国日报", "news"),
        "gzdaily": ("http://www.gzdaily.com/rss/gzb.xml", "广州日报", "news"),
        "eeo": ("http://www.eeo.com.cn/rss/rss.xml", "经济观察报", "news"),
        "people": ("http://www.people.com.cn/rss/politics.xml", "人民网", "policy"),
        # 科技
        "36kr": ("https://36kr.com/feed", "36氪", "tech"),
        "ithome": ("https://www.ithome.com/rss/", "IT之家", "tech"),
        "oschina": ("https://www.oschina.net/news/rss", "开源中国", "tech"),
        "infoq_cn": ("https://www.infoq.cn/feed", "InfoQ中文", "tech"),
        "ifeng_tech": ("http://tech.ifeng.com/rss/tech.xml", "凤凰科技", "tech"),
        "huanqiu_tech": ("https://rss.huanqiu.com/rss/tech.xml", "环球网科技", "tech"),
        "sspai": ("https://sspai.com/feed", "少数派", "tech"),
        # 安全
        "freebuf": ("https://www.freebuf.com/feed", "FreeBuf", "security"),
        # 财经
        "huanqiu_finance": ("https://rss.huanqiu.com/rss/finance.xml", "环球网财经", "finance"),
        # 军事
        "ifeng_mil": ("http://mil.ifeng.com/rss/mil.xml", "凤凰军事", "military"),
        "huanqiu_mil": ("https://rss.huanqiu.com/rss/mil.xml", "环球网军事", "military"),
        # 国际技术源
        "devto": ("https://dev.to/feed", "DEV.to", "tech"),
        "techcrunch": ("https://techcrunch.com/feed/", "TechCrunch", "tech"),
        "theverge": ("https://www.theverge.com/rss/index.xml", "The Verge", "tech"),
        "arstechnica": ("https://feeds.arstechnica.com/arstechnica/index", "Ars Technica", "tech"),
        "github_trending": ("https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml", "GitHub Trending", "tech"),
        "securityweek": ("https://www.securityweek.com/feed", "SecurityWeek", "security"),
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


class BaiduNewsConnector(BaseConnector):
    """百度新闻关键词搜索，无需 API Key."""

    BASE = "https://www.baidu.com/s"

    def search(self, keyword: str, limit: int = 20) -> FetchResult:
        try:
            from urllib.parse import quote
            url = f"{self.BASE}?wd={quote(keyword)}&tn=news&rtt=4&bsst=1&cl=2&medium=0"
            code, text, ms = self._get_text(url, headers={"User-Agent": "Mozilla/5.0 NewsIntelligenceDesktop/0.1"})
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = self._parse_news_html(text, keyword, limit)
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def _parse_news_html(self, html: str, keyword: str, limit: int) -> list[dict]:
        import re
        results = []
        blocks = re.split(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>', html)
        for block in blocks[1:limit+1]:
            title_m = re.search(r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.S)
            if not title_m:
                continue
            link = title_m.group(1)
            title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
            summary_m = re.search(r'<span[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</span>', block, re.S)
            summary = re.sub(r'<[^>]+>', '', summary_m.group(1)).strip()[:300] if summary_m else ""
            source_m = re.search(r'<span[^>]*class="[^"]*c-color-gray[^"]*"[^>]*>(.*?)</span>', block)
            source = re.sub(r'<[^>]+>', '', source_m.group(1)).strip() if source_m else "百度新闻"
            time_m = re.search(r'<span[^>]*class="[^"]*c-color-gray2[^"]*"[^>]*>(.*?)</span>', block)
            pub_time = re.sub(r'<[^>]+>', '', time_m.group(1)).strip() if time_m else ""
            if title:
                results.append({
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "source_name": source,
                    "source_url": "https://news.baidu.com",
                    "published_at": pub_time,
                    "category": "news",
                    "language": "zh",
                })
        return results
