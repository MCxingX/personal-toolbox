from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class KeywordScore:
    keyword: str
    score: float
    count: int


@dataclass
class SentimentSummary:
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    unknown: int = 0

    @property
    def total(self) -> int:
        return self.positive + self.neutral + self.negative + self.unknown

    def to_dict(self) -> dict:
        return {"positive": self.positive, "neutral": self.neutral, "negative": self.negative, "unknown": self.unknown, "total": self.total}


POSITIVE_WORDS = {"好", "棒", "优秀", "成功", "增长", "突破", "利好", "上涨", "创新", "发布", "升级", "支持", "开源", "免费", "最佳"}
NEGATIVE_WORDS = {"坏", "差", "失败", "下跌", "亏损", "漏洞", "泄露", "攻击", "风险", "事故", "死亡", "下跌", "暴跌", "危机", "警告"}

CATEGORY_KEYWORDS = {
    "tech": ["AI", "GitHub", "Python", "JavaScript", "React", "Vue", "Docker", "Kubernetes", "Rust", "Go", "开源", "框架", "模型", "API", "SDK", "Release", "Changelog"],
    "security": ["CVE", "漏洞", "泄露", "安全", "攻击", "防护", "恶意", "勒索", "钓鱼", "供应链"],
    "finance": ["股票", "基金", "黄金", "利率", "GDP", "通胀", "汇率", "央行", "财报", "营收"],
    "policy": ["政策", "法规", "通知", "意见", "条例", "国务院", "部委", "发布", "实施"],
    "entertainment": ["明星", "电影", "综艺", "票房", "热搜", "八卦", "离婚", "结婚"],
    "accident": ["事故", "车祸", "火灾", "爆炸", "地震", "洪水", "台风", "救援"],
}


def extract_keywords(texts: list[str], top_n: int = 20) -> list[KeywordScore]:
    import jieba
    from collections import Counter
    words: list[str] = []
    for text in texts:
        words.extend([w for w in jieba.cut(text) if len(w) >= 2])
    counter = Counter(words)
    return [KeywordScore(kw, count / len(words) if words else 0, count) for kw, count in counter.most_common(top_n)]


def analyze_sentiment(texts: list[str]) -> SentimentSummary:
    summary = SentimentSummary()
    for text in texts:
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        if pos > neg:
            summary.positive += 1
        elif neg > pos:
            summary.negative += 1
        elif pos == 0 and neg == 0:
            summary.neutral += 1
        else:
            summary.neutral += 1
    return summary


def classify_channel(title: str, summary: str = "") -> list[str]:
    text = f"{title} {summary}".lower()
    tags: list[str] = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            tags.append(cat)
    return tags or ["general"]


def detect_tech_change(title: str, summary: str = "") -> dict | None:
    text = f"{title} {summary}".upper()
    change_types = []
    if any(kw in text for kw in ["RELEASE", "VERSION", "V1.", "V2.", "V3.", "V4.", "V5.", "发布", "版本"]):
        change_types.append("release")
    if any(kw in text for kw in ["CVE-", "漏洞", "VULNERABILITY"]):
        change_types.append("cve")
    if any(kw in text for kw in ["BREAKING", "DEPRECATION", "弃用", "不兼容"]):
        change_types.append("breaking")
    if any(kw in text for kw in ["OPEN SOURCE", "开源", "GITHUB"]):
        change_types.append("opensource")
    if any(kw in text for kw in ["AI", "LLM", "GPT", "MODEL", "模型"]):
        change_types.append("ai")
    if not change_types:
        return None
    return {"change_types": change_types, "importance": min(1.0, len(change_types) * 0.3)}
