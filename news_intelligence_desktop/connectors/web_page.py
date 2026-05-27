from __future__ import annotations

import json
import time
import requests

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class WebPageConnector(BaseConnector):
    def fetch_page(self, url: str) -> FetchResult:
        try:
            code, text, ms = self._get_text(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            title = soup.title.string if soup.title else ""
            results = [{"title": title or url, "summary": "", "url": url, "source_name": "web", "source_url": url, "category": "web"}]
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_with_rules(self, url: str, rules: dict) -> FetchResult:
        try:
            code, text, ms = self._get_text(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            results = []
            title_sel = rules.get("title_selector", "h1, h2, h3")
            link_sel = rules.get("link_selector", "a[href]")
            summary_sel = rules.get("summary_selector", "p")

            links = soup.select(link_sel)[:30]
            for link in links:
                href = link.get("href", "")
                title_text = link.get_text(strip=True)
                if not title_text or not href:
                    continue
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                results.append({
                    "title": title_text,
                    "summary": "",
                    "url": href,
                    "source_name": "web",
                    "source_url": url,
                    "category": "web",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
