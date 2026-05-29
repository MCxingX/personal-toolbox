"""Tophub.today 每日早晚报抓取器 - 网页抓取方式."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from news_intelligence_desktop.storage.repository import Repository

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

_URL = "https://tophub.today/daily"


def _is_chinese(text: str) -> bool:
    """判断文本是否主要是中文."""
    if not text:
        return False
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return False
    return chinese_chars / total_chars >= 0.3


def fetch_tophub_daily(zh_only: bool = True) -> list[dict[str, Any]]:
    """抓取 tophub.today/daily 页面，返回每日早晚报数据.

    Args:
        zh_only: 是否只保留中文内容，默认 True
    """
    items: list[dict[str, Any]] = []
    try:
        resp = requests.get(_URL, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 找到所有新闻条目
        for item_div in soup.select(".kt-t__item"):
            # 提取来源名称
            source_el = item_div.select_one(".kt-t__item-header strong")
            source = source_el.get_text(strip=True) if source_el else "未知"

            # 提取每条新闻
            for link in item_div.select("a.kt-t__item-text"):
                title = link.get_text(strip=True)
                url = link.get("href", "")
                if not title:
                    continue
                # 中文过滤
                if zh_only and not _is_chinese(title):
                    continue
                items.append({
                    "title": title,
                    "url": url,
                    "source": source,
                    "category": _categorize(title, source),
                    "fetched_at": datetime.now().isoformat(),
                })

        logger.info("tophub.today 抓取完成: %d 条 (zh_only=%s)", len(items), zh_only)
    except Exception as e:
        logger.warning("tophub.today 抓取失败: %s", e)

    return items


def _categorize(title: str, source: str) -> str:
    """根据标题和来源推断分类."""
    text = f"{title} {source}".lower()

    # 财经类
    finance_kw = ["股", "基金", "投资", "金融", "银行", "证券", "期货", "债券",
                   "港股", "a股", "美股", "央行", "gdp", "cpi", "利率", "汇率",
                   "财经", "财联社", "华尔街", "经济", "上市", "融资", "市值"]
    if any(kw in text for kw in finance_kw):
        return "finance"

    # 科技类
    tech_kw = ["ai", "芯片", "算法", "模型", "技术", "开发", "编程", "开源",
               "互联网", "科技", "数码", "手机", "电脑", "软件", "硬件",
               "人工智能", "大模型", "gpu", "半导体", "5g", "量子"]
    if any(kw in text for kw in tech_kw):
        return "tech"

    # 安全类
    sec_kw = ["安全", "漏洞", "黑客", "攻击", "数据泄露", "隐私", "网络犯罪",
              "勒索", "钓鱼", "恶意软件", "安全漏洞"]
    if any(kw in text for kw in sec_kw):
        return "security"

    # 政策类
    policy_kw = ["政策", "法规", "监管", "政府", "国务院", "两会", "部委",
                 "条例", "意见", "办法", "规定", "法律"]
    if any(kw in text for kw in policy_kw):
        return "policy"

    # 军事类
    military_kw = ["军事", "国防", "军队", "武器", "导弹", "战机", "航母",
                   "军演", "冲突", "战争", "国防"]
    if any(kw in text for kw in military_kw):
        return "military"

    # 科学类
    science_kw = ["科学", "研究", "发现", "实验", "论文", "宇宙", "航天",
                  "卫星", "火箭", "空间站", "月球", "火星"]
    if any(kw in text for kw in science_kw):
        return "science"

    return "news"


def save_tophub_daily(repo: Repository, items: list[dict[str, Any]]) -> int:
    """保存抓取结果到数据库."""
    from news_intelligence_desktop.storage.repository import ArticleInput

    saved = 0
    for item in items:
        article = ArticleInput(
            title=item["title"],
            summary=item["title"],
            source_name=f"tophub-{item['source']}",
            source_url=item.get("url", ""),
            url=item.get("url", ""),
            category=item["category"],
            published_at=item["fetched_at"],
            importance_score=0.7,
            language="zh",
        )
        if repo.add_article(article):
            saved += 1
    return saved
