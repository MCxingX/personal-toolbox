"""网页来源连接器 - 支持 CSS Selector 和 XPath 解析."""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from news_intelligence_desktop.connectors import BaseConnector, FetchResult

logger = logging.getLogger(__name__)

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 受限页面关键词
RESTRICTED_KEYWORDS = [
    "login", "signin", "signup", "register", "captcha", "verify",
    "auth", "oauth", "sso", "forbidden", "access-denied",
    "登录", "注册", "验证", "授权", "禁止",
]


@dataclass
class ParseRule:
    """网页解析规则."""
    url_pattern: str  # URL 匹配模式（正则）
    title_selector: str = ""  # 标题 CSS Selector
    link_selector: str = "a[href]"  # 链接 CSS Selector
    summary_selector: str = ""  # 摘要 CSS Selector
    content_selector: str = ""  # 正文 CSS Selector
    date_selector: str = ""  # 日期 CSS Selector
    author_selector: str = ""  # 作者 CSS Selector
    item_selector: str = ""  # 列表项 CSS Selector（用于列表页）
    use_xpath: bool = False  # 是否使用 XPath
    encoding: str = ""  # 强制编码
    max_items: int = 30  # 最大条目数
    remove_selectors: list[str] = field(default_factory=list)  # 需要移除的元素


@dataclass
class ParsedItem:
    """解析结果条目."""
    title: str
    url: str
    summary: str = ""
    content: str = ""
    date: str = ""
    author: str = ""
    source_name: str = ""
    category: str = "web"


class WebPageParser:
    """网页解析器 - 支持 CSS Selector 和 XPath."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_page(self, url: str, encoding: str = "") -> tuple[int, str, float]:
        """获取网页内容."""
        try:
            start = time.time()
            resp = self.session.get(url, timeout=15, allow_redirects=True)
            ms = (time.time() - start) * 1000

            if encoding:
                resp.encoding = encoding
            elif resp.encoding and resp.encoding.lower() in ["iso-8859-1", "latin-1"]:
                resp.encoding = resp.apparent_encoding

            return resp.status_code, resp.text, ms
        except Exception as e:
            logger.error("获取网页失败 %s: %s", url, e)
            return 0, "", 0

    def check_restricted(self, html: str, url: str) -> str | None:
        """检查是否为受限页面."""
        if not html:
            return "页面内容为空"

        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text(" ", strip=True).lower()[:5000]
        lower_html = html.lower()
        lower_url = url.lower()

        for keyword in RESTRICTED_KEYWORDS:
            if keyword in lower_url:
                return f"检测到受限关键词: {keyword}"
            if keyword in page_text and len(page_text) < 1200:
                return f"检测到受限关键词: {keyword}"

        # 检查是否为登录页特征
        if re.search(r'<form[^>]*(login|signin|auth)', lower_html):
            return "检测到登录表单"

        # 检查是否为验证码页
        if re.search(r'captcha|recaptcha|hcaptcha', lower_html):
            return "检测到验证码"

        return None

    def parse_with_css(self, html: str, rule: ParseRule, base_url: str) -> list[ParsedItem]:
        """使用 CSS Selector 解析网页."""
        soup = BeautifulSoup(html, "html.parser")

        # 移除不需要的元素
        for sel in rule.remove_selectors:
            for elem in soup.select(sel):
                elem.decompose()

        items = []

        # 列表页解析
        if rule.item_selector:
            elements = soup.select(rule.item_selector)[:rule.max_items]
            for elem in elements:
                item = self._extract_item_from_element(elem, rule, base_url)
                if item and item.title:
                    items.append(item)
        else:
            # 单页解析 - 提取所有链接
            links = soup.select(rule.link_selector)[:rule.max_items]
            for link in links:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if not title or not href:
                    continue
                if href.startswith("/"):
                    href = urljoin(base_url, href)
                elif not href.startswith("http"):
                    continue

                # 尝试获取摘要
                summary = ""
                if rule.summary_selector:
                    parent = link.parent
                    if parent:
                        summary_elem = parent.select_one(rule.summary_selector)
                        if summary_elem:
                            summary = summary_elem.get_text(strip=True)

                items.append(ParsedItem(
                    title=title,
                    url=href,
                    summary=summary,
                    source_name=urlparse(base_url).netloc,
                ))

        return items

    def _extract_item_from_element(self, elem, rule: ParseRule, base_url: str) -> ParsedItem | None:
        """从元素中提取条目."""
        # 提取标题和链接
        title = ""
        url = ""

        if rule.title_selector:
            title_elem = elem.select_one(rule.title_selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                # 尝试从标题元素获取链接
                link = title_elem.find("a")
                if link:
                    url = link.get("href", "")

        # 如果没有标题，尝试从链接获取
        if not title:
            link_elem = elem.select_one("a[href]")
            if link_elem:
                title = link_elem.get_text(strip=True)
                url = link_elem.get("href", "")

        if not title:
            return None

        # 处理相对路径
        if url and url.startswith("/"):
            url = urljoin(base_url, url)

        # 提取摘要
        summary = ""
        if rule.summary_selector:
            summary_elem = elem.select_one(rule.summary_selector)
            if summary_elem:
                summary = summary_elem.get_text(strip=True)

        # 提取日期
        date = ""
        if rule.date_selector:
            date_elem = elem.select_one(rule.date_selector)
            if date_elem:
                date = date_elem.get_text(strip=True)

        # 提取作者
        author = ""
        if rule.author_selector:
            author_elem = elem.select_one(rule.author_selector)
            if author_elem:
                author = author_elem.get_text(strip=True)

        # 提取正文（如果有）
        content = ""
        if rule.content_selector:
            content_elem = elem.select_one(rule.content_selector)
            if content_elem:
                content = content_elem.get_text(strip=True)[:500]

        return ParsedItem(
            title=title,
            url=url or base_url,
            summary=summary,
            content=content,
            date=date,
            author=author,
            source_name=urlparse(base_url).netloc,
        )

    def parse_with_xpath(self, html: str, rule: ParseRule, base_url: str) -> list[ParsedItem]:
        """使用 XPath 解析网页."""
        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html)
        except ImportError:
            logger.warning("lxml 未安装，回退到 CSS Selector")
            return self.parse_with_css(html, rule, base_url)

        items = []
        # XPath 解析逻辑
        if rule.item_selector:
            try:
                elements = tree.xpath(rule.item_selector)[:rule.max_items]
                for elem in elements:
                    item = self._extract_item_from_xpath(elem, rule, base_url)
                    if item and item.title:
                        items.append(item)
            except Exception as e:
                logger.error("XPath 解析失败: %s", e)

        return items

    def _extract_item_from_xpath(self, elem, rule: ParseRule, base_url: str) -> ParsedItem | None:
        """从 XPath 元素中提取条目."""
        title = ""
        url = ""
        summary = ""

        def _first_xpath_text(node, selector: str) -> str:
            values = node.xpath(selector) if selector else []
            if not isinstance(values, list):
                values = [values]
            if not values:
                return ""
            first = values[0]
            return first.text_content().strip() if hasattr(first, "text_content") else str(first).strip()

        def _first_xpath_href(node, selector: str) -> str:
            values = node.xpath(selector) if selector else []
            if not isinstance(values, list):
                values = [values]
            if not values:
                return ""
            first = values[0]
            if hasattr(first, "get"):
                return first.get("href", "")
            return str(first).strip()

        try:
            if rule.title_selector:
                title = _first_xpath_text(elem, rule.title_selector)

            if rule.link_selector:
                href = _first_xpath_href(elem, rule.link_selector)
                if href:
                    url = urljoin(base_url, href) if href.startswith("/") else href

            if rule.summary_selector:
                summary = _first_xpath_text(elem, rule.summary_selector)

        except Exception as e:
            logger.debug("XPath 提取失败: %s", e)

        if not title:
            return None

        return ParsedItem(
            title=title,
            url=url or base_url,
            summary=summary,
            source_name=urlparse(base_url).netloc,
        )

    def auto_extract(self, html: str, url: str) -> list[ParsedItem]:
        """自动提取网页内容（无需配置规则）."""
        soup = BeautifulSoup(html, "html.parser")

        # 移除无用元素
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        items = []

        # 尝试提取文章列表
        # 1. 查找常见的文章容器
        article_selectors = [
            "article", ".article", ".post", ".news-item", ".list-item",
            ".entry", ".card", ".item", "li", ".content-item",
        ]

        for selector in article_selectors:
            articles = soup.select(selector)[:20]
            if len(articles) >= 3:  # 找到足够的文章
                for article in articles:
                    item = self._extract_auto_item(article, url)
                    if item and item.title and len(item.title) > 5:
                        items.append(item)
                if items:
                    break

        # 2. 如果没有找到列表，提取页面中的所有链接
        if not items:
            links = soup.find_all("a", href=True)[:30]
            seen_urls = set()
            for link in links:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                if href.startswith("/"):
                    href = urljoin(url, href)
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                items.append(ParsedItem(
                    title=title,
                    url=href,
                    source_name=urlparse(url).netloc,
                ))

        return items[:20]

    def _extract_auto_item(self, elem, base_url: str) -> ParsedItem | None:
        """自动提取单个条目."""
        # 查找标题
        title = ""
        title_elem = elem.find(["h1", "h2", "h3", "h4", "a"])
        if title_elem:
            title = title_elem.get_text(strip=True)

        # 查找链接
        url = ""
        link = elem.find("a", href=True)
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                url = urljoin(base_url, href)
            elif href.startswith("http"):
                url = href

        # 查找摘要
        summary = ""
        summary_elem = elem.select_one("p, .summary, .excerpt, .description")
        if summary_elem:
            summary = summary_elem.get_text(strip=True)[:200]

        # 查找日期
        date = ""
        date_elem = elem.select_one("time, .date, .time, .published")
        if date_elem:
            date = date_elem.get_text(strip=True)

        if not title:
            return None

        return ParsedItem(
            title=title,
            url=url or base_url,
            summary=summary,
            date=date,
            source_name=urlparse(base_url).netloc,
        )

    def extract_content(self, html: str) -> str:
        """提取正文内容."""
        soup = BeautifulSoup(html, "html.parser")

        # 移除无用元素
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # 尝试找到正文容器
        content_selectors = [
            "article", ".article-content", ".post-content", ".entry-content",
            ".content", ".main-content", "#content", "main",
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                text = content_elem.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    return text[:2000]

        # 回退：提取所有段落
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return text[:2000]


class WebPageConnector(BaseConnector):
    """网页来源连接器 - 支持配置化规则解析."""

    def __init__(self):
        super().__init__()
        self.parser = WebPageParser()

    def fetch_page(self, url: str) -> FetchResult:
        """获取单个网页."""
        try:
            code, html, ms = self.parser.fetch_page(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)

            # 检查受限
            restricted = self.parser.check_restricted(html, url)
            if restricted:
                return FetchResult(False, [], f"受限页面: {restricted}", ms)

            # 自动提取
            items = self.parser.auto_extract(html, url)
            results = [
                {
                    "title": item.title,
                    "summary": item.summary,
                    "url": item.url,
                    "source_name": item.source_name,
                    "source_url": url,
                    "category": "web",
                }
                for item in items
            ]
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_with_rules(self, url: str, rule: ParseRule) -> FetchResult:
        """使用规则解析网页."""
        try:
            code, html, ms = self.parser.fetch_page(url, rule.encoding)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)

            # 检查受限
            restricted = self.parser.check_restricted(html, url)
            if restricted:
                return FetchResult(False, [], f"受限页面: {restricted}", ms)

            # 根据规则解析
            if rule.use_xpath:
                items = self.parser.parse_with_xpath(html, rule, url)
            else:
                items = self.parser.parse_with_css(html, rule, url)

            results = [
                {
                    "title": item.title,
                    "summary": item.summary,
                    "url": item.url,
                    "source_name": item.source_name,
                    "source_url": url,
                    "category": "web",
                    "date": item.date,
                    "author": item.author,
                }
                for item in items
            ]
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def fetch_content(self, url: str) -> FetchResult:
        """获取网页正文内容."""
        try:
            code, html, ms = self.parser.fetch_page(url)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)

            content = self.parser.extract_content(html)
            if not content:
                return FetchResult(False, [], "无法提取正文", ms)

            results = [{"content": content, "url": url}]
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def test_rule(self, url: str, rule: ParseRule) -> dict:
        """测试解析规则."""
        try:
            code, html, ms = self.parser.fetch_page(url, rule.encoding)
            if code != 200:
                return {"success": False, "error": f"HTTP {code}", "ms": ms}

            # 检查受限
            restricted = self.parser.check_restricted(html, url)
            if restricted:
                return {"success": False, "error": f"受限页面: {restricted}", "ms": ms}

            # 解析
            if rule.use_xpath:
                items = self.parser.parse_with_xpath(html, rule, url)
            else:
                items = self.parser.parse_with_css(html, rule, url)

            return {
                "success": True,
                "items": [
                    {"title": item.title, "url": item.url, "summary": item.summary[:100]}
                    for item in items[:5]
                ],
                "total": len(items),
                "ms": ms,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 预定义的常见网站规则
PREDEFINED_RULES: dict[str, ParseRule] = {
    "36kr": ParseRule(
        url_pattern=r"36kr\.com",
        item_selector=".article-item, .flow-item",
        title_selector="a.article-item-title, .title",
        summary_selector=".summary, .description",
        date_selector=".time, .date",
    ),
    "ithome": ParseRule(
        url_pattern=r"ithome\.com",
        item_selector=".news-list li, .list-item",
        title_selector="a.title, h2 a",
        summary_selector=".memo, .summary",
        date_selector=".time, .date",
    ),
    "zhihu": ParseRule(
        url_pattern=r"zhihu\.com",
        item_selector=".ContentItem, .List-item",
        title_selector="h2 a, .ContentItem-title a",
        summary_selector=".RichContent-inner, .excerpt",
    ),
    "weibo": ParseRule(
        url_pattern=r"weibo\.com",
        item_selector=".card-wrap, .WB_feed_type",
        title_selector=".txt, .WB_text",
        date_selector=".from, .time",
    ),
}


def get_predefined_rule(domain: str) -> ParseRule | None:
    """获取预定义规则."""
    for key, rule in PREDEFINED_RULES.items():
        if key in domain:
            return rule
    return None
