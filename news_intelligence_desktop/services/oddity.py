"""猎奇内容识别 - 关键词词典、可信度评分和标签系统."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from typing import Any


class OddityService:
    """猎奇内容服务 - 识别、分类和评分."""

    # 猎奇关键词词典（按类别）
    ODDITY_KEYWORDS = {
        "oddity": {
            "keywords": ["奇闻", "异闻", "怪事", "未知", "神秘", "外星", "UFO", "灵异", "诡异", "罕见", "离奇", "奇葩", "不可思议", "震惊", "惊呆"],
            "weight": 1.0,
        },
        "accident": {
            "keywords": ["事故", "车祸", "火灾", "爆炸", "地震", "洪水", "台风", "暴雨", "泥石流", "山体滑坡", "空难", "沉船", "矿难", "坍塌"],
            "weight": 0.9,
        },
        "entertainment": {
            "keywords": ["明星", "八卦", "离婚", "结婚", "出轨", "绯闻", "综艺", "选秀", "偶像", "饭圈", "追星", "塌房", "塌方"],
            "weight": 0.7,
        },
        "science": {
            "keywords": ["科技", "AI", "机器人", "太空", "量子", "基因", "克隆", "核能", "暗物质", "黑洞", "外星人", "平行宇宙", "时间旅行"],
            "weight": 0.8,
        },
        "social": {
            "keywords": ["争议", "舆论", "热搜", "骂战", "网暴", "霸凌", "歧视", "维权", "上访", "抗议", "示威", "游行"],
            "weight": 0.8,
        },
        "mystery": {
            "keywords": ["失踪", "悬案", "未解之谜", "密室", "诅咒", "通灵", "超自然", "灵异事件", "鬼", "幽灵", "巫术"],
            "weight": 0.9,
        },
        "extreme": {
            "keywords": ["极端", "变态", "恐怖", "血腥", "暴力", "残忍", "虐杀", "连环杀手", "serial killer"],
            "weight": 1.0,
        },
        "weird_science": {
            "keywords": ["永动机", "水变油", "伪科学", "民科", "地平说", "进化论争议", "疫苗争议"],
            "weight": 0.9,
        },
    }

    # 低可信度来源特征
    LOW_CREDIBILITY_PATTERNS = [
        r"震惊[!！]",
        r"99%的人都不知道",
        r"速看[!！]",
        r"刚刚[!！]",
        r"突发[!！]",
        r"揭秘",
        r"曝光",
        r"内幕",
        r"真相",
        r"不转不是中国人",
        r"必看",
        r"紧急通知",
    ]

    # 夸张标题特征
    EXAGGERATED_PATTERNS = [
        r"[!！]{2,}",
        r"[?？]{2,}",
        r"震惊[部全]",
        r"惊呆[了]",
        r"吓人",
        r"可怕",
        r"恐怖",
        r"太[可恐]怕了",
        r"不[敢看]相信",
        r"万万没想到",
    ]

    # 类别标签
    CATEGORY_LABELS = {
        "oddity": "奇闻异事",
        "accident": "事故灾害",
        "entertainment": "娱乐八卦",
        "science": "科技前沿",
        "social": "社会争议",
        "mystery": "悬疑解密",
        "extreme": "极端事件",
        "weird_science": "伪科学",
        "unknown": "未分类",
    }

    def __init__(self, repo):
        self.repo = repo

    def classify_oddity(self, title: str, summary: str = "") -> dict | None:
        """分类猎奇内容."""
        text = f"{title} {summary}".lower()
        matches = []

        # 匹配关键词
        for category, config in self.ODDITY_KEYWORDS.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    matches.append({
                        "category": category,
                        "keyword": keyword,
                        "weight": config["weight"],
                    })

        if not matches:
            return None

        # 选择最佳匹配（权重最高）
        best = max(matches, key=lambda x: x["weight"])

        # 计算可信度
        credibility = self._calculate_credibility(title, summary)

        # 检测夸张程度
        exaggeration = self._detect_exaggeration(title)

        return {
            "tag": "oddity",
            "category": best["category"],
            "category_label": self.CATEGORY_LABELS.get(best["category"], "其他"),
            "keyword": best["keyword"],
            "credibility": credibility,
            "exaggeration": exaggeration,
            "confidence": min(len(matches) * 0.3, 1.0),
        }

    def _calculate_credibility(self, title: str, summary: str = "") -> float:
        """计算可信度分数 (0-1)."""
        score = 0.5  # 基础分

        # 检查低可信度特征
        text = f"{title} {summary}"
        for pattern in self.LOW_CREDIBILITY_PATTERNS:
            if re.search(pattern, text):
                score -= 0.15

        # 检查夸张标题
        exaggeration = self._detect_exaggeration(title)
        score -= exaggeration * 0.2

        # 检查是否有来源引用
        if re.search(r"(来源|据|报道|消息|记者)", text):
            score += 0.1

        # 检查是否有具体数据
        if re.search(r"\d+%|\d+人|\d+万|\d+亿", text):
            score += 0.05

        # 检查标题长度（过短可能不完整）
        if len(title) < 10:
            score -= 0.1

        return max(0.1, min(1.0, score))

    def _detect_exaggeration(self, title: str) -> float:
        """检测夸张程度 (0-1)."""
        count = 0
        for pattern in self.EXAGGERATED_PATTERNS:
            if re.search(pattern, title):
                count += 1

        # 检查感叹号数量
        exclamation_count = title.count("!") + title.count("！")
        if exclamation_count > 2:
            count += 1

        return min(count * 0.25, 1.0)

    def list_oddities(self, limit: int = 30, category: str = "") -> list[dict]:
        """列出猎奇内容."""
        articles = self.repo.list_articles(limit=200)
        oddities = []

        for art in articles:
            result = self.classify_oddity(art["title"], art.get("summary", ""))
            if result:
                art["oddity_tag"] = result["tag"]
                art["oddity_category"] = result["category"]
                art["oddity_category_label"] = result["category_label"]
                art["oddity_credibility"] = result["credibility"]
                art["oddity_exaggeration"] = result["exaggeration"]
                art["oddity_confidence"] = result["confidence"]

                # 按类别过滤
                if category and result["category"] != category:
                    continue

                oddities.append(art)

        # 按可信度排序（高可信度优先）
        oddities.sort(key=lambda x: x.get("oddity_credibility", 0), reverse=True)

        return oddities[:limit]

    def get_oddity_detail(self, article_id: int) -> dict | None:
        """获取猎奇内容详情."""
        art = self.repo.get_article(article_id)
        if not art:
            return None

        result = self.classify_oddity(art["title"], art.get("summary", ""))
        if result:
            art["oddity_tag"] = result["tag"]
            art["oddity_category"] = result["category"]
            art["oddity_category_label"] = result["category_label"]
            art["oddity_credibility"] = result["credibility"]
            art["oddity_exaggeration"] = result["exaggeration"]
            art["oddity_confidence"] = result["confidence"]
            art["oddity_display_pref"] = self._get_display_preference(result)

        return art

    def _get_display_preference(self, result: dict) -> dict:
        """获取展示偏好建议."""
        credibility = result.get("credibility", 0.5)
        exaggeration = result.get("exaggeration", 0)

        # 根据可信度和夸张程度决定展示方式
        if credibility < 0.3:
            return {"fold": True, "warning": "低可信度内容", "color": "red"}
        elif credibility < 0.5 or exaggeration > 0.7:
            return {"fold": False, "warning": "可能存在夸张", "color": "orange"}
        else:
            return {"fold": False, "warning": "", "color": "green"}

    def get_category_stats(self) -> dict:
        """获取猎奇内容分类统计."""
        articles = self.repo.list_articles(limit=500)
        stats = {cat: 0 for cat in self.CATEGORY_LABELS}

        for art in articles:
            result = self.classify_oddity(art["title"], art.get("summary", ""))
            if result:
                cat = result["category"]
                stats[cat] = stats.get(cat, 0) + 1

        return {
            "total": sum(stats.values()),
            "by_category": {self.CATEGORY_LABELS.get(k, k): v for k, v in stats.items() if v > 0},
        }

    def get_credibility_explanation(self, article_id: int) -> dict:
        """获取可信度解释."""
        art = self.repo.get_article(article_id)
        if not art:
            return {"error": "文章不存在"}

        result = self.classify_oddity(art["title"], art.get("summary", ""))
        if not result:
            return {"error": "非猎奇内容"}

        explanations = []
        credibility = result["credibility"]

        # 解释可信度
        if credibility < 0.3:
            explanations.append("标题使用大量夸张用语，可信度较低")
        elif credibility < 0.5:
            explanations.append("标题可能包含夸张成分")

        if result["exaggeration"] > 0.5:
            explanations.append("检测到夸张标题特征")

        # 检查是否有来源
        text = f"{art['title']} {art.get('summary', '')}"
        if re.search(r"(来源|据|报道|消息|记者)", text):
            explanations.append("内容引用了来源或报道")

        if re.search(r"\d+%|\d+人|\d+万|\d+亿", text):
            explanations.append("内容包含具体数据")

        return {
            "article_id": article_id,
            "credibility": credibility,
            "exaggeration": result["exaggeration"],
            "explanations": explanations,
            "category": result["category_label"],
        }

    def update_display_preference(self, article_id: int, pref: str) -> bool:
        """更新展示偏好设置."""
        # pref: "show", "fold", "hide"
        valid_prefs = ["show", "fold", "hide"]
        if pref not in valid_prefs:
            return False

        # 存储到 user_prefs
        key = f"oddity_pref_{article_id}"
        self.repo.set_pref(key, pref)
        return True
