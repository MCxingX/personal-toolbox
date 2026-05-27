from __future__ import annotations

import json
from datetime import datetime


class OddityService:
    ODDITY_KEYWORDS = ["奇闻", "异闻", "怪事", "未知", "神秘", "外星", "UFO", "灵异", "诡异", "罕见", "极端", "异常", "特殊", "离奇"]
    ODDITY_CATEGORIES = {
        "oddity": "奇闻异事",
        "entertainment": "娱乐八卦",
        "accident": "事故灾害",
        "science": "特殊科技",
        "social": "社会争议",
    }

    def __init__(self, repo):
        self.repo = repo

    def classify_oddity(self, title: str, summary: str = "") -> dict | None:
        text = f"{title} {summary}".lower()
        for kw in self.ODDITY_KEYWORDS:
            if kw in text:
                return {"tag": "oddity", "keyword": kw, "category": self._detect_category(text)}
        return None

    def _detect_category(self, text: str) -> str:
        if any(w in text for w in ["事故", "车祸", "火灾", "爆炸", "地震"]):
            return "accident"
        if any(w in text for w in ["明星", "八卦", "离婚", "结婚", "综艺"]):
            return "entertainment"
        if any(w in text for w in ["科技", "AI", "机器人", "太空"]):
            return "science"
        if any(w in text for w in ["争议", "舆论", "热搜", "骂战"]):
            return "social"
        return "oddity"

    def list_oddities(self, limit: int = 30) -> list[dict]:
        articles = self.repo.list_articles(limit=100)
        oddities = []
        for art in articles:
            result = self.classify_oddity(art["title"], art.get("summary", ""))
            if result:
                art["oddity_tag"] = result["tag"]
                art["oddity_category"] = result["category"]
                art["oddity_category_label"] = self.ODDITY_CATEGORIES.get(result["category"], "其他")
                oddities.append(art)
        return oddities[:limit]

    def get_oddity_detail(self, article_id: int) -> dict | None:
        art = self.repo.get_article(article_id)
        if not art:
            return None
        result = self.classify_oddity(art["title"], art.get("summary", ""))
        if result:
            art["oddity_tag"] = result["tag"]
            art["oddity_category"] = result["category"]
        return art
