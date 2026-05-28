from __future__ import annotations

import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime


IMPORTANT_KEYWORDS = {
    "死亡", "失踪", "爆炸", "事故", "地震", "台风", "暴雨", "洪水", "火灾", "坠亡",
    "政策", "发布", "调整", "监管", "央行", "财政", "税", "补贴", "降息", "涨价",
    "战争", "冲突", "制裁", "停火", "选举", "外交", "美国", "俄罗斯", "以色列",
    "股市", "美股", "A股", "新能源", "房价", "就业", "AI", "芯片", "安全漏洞",
}


def normalize_text(value: str | None, limit: int = 500) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", "", str(value))
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_news_time(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    now = datetime.now()
    if raw in {"刚刚", "刚刚发布"}:
        return now
    if "分钟前" in raw:
        minutes = _first_int(raw) or 0
        return now - timedelta(minutes=minutes)
    if "小时前" in raw:
        hours = _first_int(raw) or 0
        return now - timedelta(hours=hours)
    if "昨天" in raw:
        hm = re.search(r"(\d{1,2}:\d{2})", raw)
        base = now - timedelta(days=1)
        if hm:
            hour, minute = [int(x) for x in hm.group(1).split(":")]
            return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return base.replace(hour=0, minute=0, second=0, microsecond=0)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            pass
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        return None


def is_recent_news(value: str | None, days: int = 2) -> bool:
    dt = parse_news_time(value)
    if not dt:
        return True
    return dt >= datetime.now() - timedelta(days=days)


def format_news_time(value: str | None) -> str:
    dt = parse_news_time(value)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(value or "")[:16]


def enrich_summary(title: str, summary: str, source: str = "") -> str:
    title = normalize_text(title, 180)
    summary = normalize_text(summary, 420)
    base = summary or title
    facts = _extract_key_facts(base)
    if facts:
        return f"看点：{facts}。{base}"[:520]
    if summary:
        return summary
    return f"看点：{title}。建议打开原文确认细节。"[:520]


def importance_score(title: str, summary: str, category: str = "news", source: str = "") -> float:
    text = f"{title} {summary} {source}"
    score = 0.45
    score += min(0.35, sum(0.035 for kw in IMPORTANT_KEYWORDS if kw.lower() in text.lower()))
    if category in {"policy", "finance", "military", "security", "accident", "earthquake"}:
        score += 0.12
    if any(src in source for src in ("新华社", "央视", "财联社", "界面", "腾讯新闻", "中国新闻网", "澎湃", "财新")):
        score += 0.08
    if re.search(r"\d", text):
        score += 0.05
    return max(0.1, min(score, 0.98))


def news_digest_line(article: dict) -> str:
    title = article.get("title", "")
    summary = normalize_text(article.get("summary", ""), 180)
    source = article.get("source_name", "")
    when = format_news_time(article.get("published_at") or article.get("collected_at"))
    core = summary.replace("看点：", "") if summary else "建议打开原文确认细节。"
    return f"- {title}\n  来源：{source}｜时间：{when}\n  重点：{core[:180]}"


def _extract_key_facts(text: str) -> str:
    candidates = re.findall(r"[^。！？；;]{0,28}(?:\d+(?:\.\d+)?%?|[一二三四五六七八九十百千万亿]+)[^。！？；;]{0,36}", text)
    if candidates:
        return normalize_text(candidates[0], 90)
    for kw in IMPORTANT_KEYWORDS:
        idx = text.find(kw)
        if idx >= 0:
            return normalize_text(text[max(0, idx - 24):idx + 60], 90)
    return ""


def _first_int(value: str) -> int | None:
    m = re.search(r"\d+", value)
    return int(m.group(0)) if m else None
