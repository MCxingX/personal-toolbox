"""板块化数据源管理 - 统一管理 RSS、API、热榜等数据源."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceItem:
    """单个数据源."""
    name: str
    source_type: str  # rss, api, hotboard
    url: str
    category: str  # social, news, tech, interest, music_game
    enabled: bool = True
    fetch_interval: int = 30  # 分钟
    last_fetch: str | None = None


@dataclass
class Section:
    """数据板块."""
    key: str
    name: str
    description: str
    enabled: bool = True
    sources: list[SourceItem] = field(default_factory=list)


# ===== 板块定义 =====
SECTIONS: dict[str, Section] = {
    "social": Section(
        key="social",
        name="社交热榜",
        description="微博、知乎、百度、抖音等社交平台热榜",
        sources=[
            SourceItem("微博热搜", "hotboard", "weibo", "social"),
            SourceItem("知乎热榜", "hotboard", "zhihu", "social"),
            SourceItem("百度热搜", "hotboard", "baidu", "social"),
            SourceItem("抖音热榜", "hotboard", "douyin", "social"),
            SourceItem("快手热榜", "hotboard", "kuaishou", "social"),
            SourceItem("头条热榜", "hotboard", "toutiao", "social"),
            SourceItem("腾讯新闻", "hotboard", "qq-news", "social"),
            SourceItem("新浪热搜", "hotboard", "sina", "social"),
            SourceItem("网易新闻", "hotboard", "netease-news", "social"),
            SourceItem("澎湃新闻", "hotboard", "thepaper", "social"),
            SourceItem("虎扑热帖", "hotboard", "hupu", "social"),
            SourceItem("贴吧热帖", "hotboard", "tieba", "social"),
            SourceItem("NGA论坛", "hotboard", "ngabbs", "social"),
            SourceItem("V2EX", "hotboard", "v2ex", "social"),
        ],
    ),
    "news": Section(
        key="news",
        name="新闻资讯",
        description="国内外新闻、政策法规、财经金融",
        sources=[
            SourceItem("中国新闻网", "rss", "https://www.chinanews.com.cn/rss/scroll-news.xml", "news"),
            SourceItem("人民网", "rss", "http://www.people.com.cn/rss/politics.xml", "news"),
            SourceItem("Google News 中文", "rss", "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "news"),
            SourceItem("AI Daily 精选", "rss", "https://yeekal.com/rss/daily.xml", "news"),
            SourceItem("Yahoo Finance", "rss", "https://finance.yahoo.com/news/rssindex", "news"),
            SourceItem("虎嗅", "hotboard", "huxiu", "news"),
            SourceItem("爱范儿", "hotboard", "ifanr", "news"),
            SourceItem("历史上的今天", "hotboard", "history", "news"),
            SourceItem("天气预警", "hotboard", "weatheralarm", "news"),
            SourceItem("地震速报", "hotboard", "earthquake", "news"),
        ],
    ),
    "tech": Section(
        key="tech",
        name="科技社区",
        description="科技资讯、开发者社区、开源项目",
        sources=[
            SourceItem("36氪", "rss", "https://36kr.com/feed", "tech"),
            SourceItem("IT之家", "rss", "https://www.ithome.com/rss/", "tech"),
            SourceItem("开源中国", "rss", "https://www.oschina.net/news/rss", "tech"),
            SourceItem("少数派", "rss", "https://sspai.com/feed", "tech"),
            SourceItem("Hacker News", "rss", "https://hnrss.org/frontpage?count=30", "tech"),
            SourceItem("TechCrunch", "rss", "https://techcrunch.com/feed/", "tech"),
            SourceItem("The Verge", "rss", "https://www.theverge.com/rss/index.xml", "tech"),
            SourceItem("FreeBuf", "rss", "https://www.freebuf.com/feed", "tech"),
            SourceItem("Krebs on Security", "rss", "https://krebsonsecurity.com/feed/", "tech"),
            SourceItem("掘金", "hotboard", "juejin", "tech"),
            SourceItem("CSDN", "hotboard", "csdn", "tech"),
            SourceItem("51CTO", "hotboard", "51cto", "tech"),
            SourceItem("NodeSeek", "hotboard", "nodeseek", "tech"),
            SourceItem("HelloGitHub", "hotboard", "hellogithub", "tech"),
            SourceItem("酷安", "hotboard", "coolapk", "tech"),
            SourceItem("吾爱破解", "hotboard", "52pojie", "tech"),
        ],
    ),
    "interest": Section(
        key="interest",
        name="兴趣圈子",
        description="读书、影视、游戏、科学等兴趣社区",
        sources=[
            SourceItem("Nature", "rss", "https://www.nature.com/nature.rss", "interest"),
            SourceItem("Science Daily", "rss", "https://www.sciencedaily.com/rss/all.xml", "interest"),
            SourceItem("豆瓣电影", "hotboard", "douban-movie", "interest"),
            SourceItem("果壳", "hotboard", "guokr", "interest"),
            SourceItem("微信读书", "hotboard", "weread", "interest"),
            SourceItem("B站", "hotboard", "bilibili", "interest"),
            SourceItem("A站", "hotboard", "acfun", "interest"),
        ],
    ),
    "music_game": Section(
        key="music_game",
        name="音乐游戏",
        description="音乐热歌榜、游戏资讯",
        sources=[
            SourceItem("网易云音乐", "hotboard", "netease-music", "music_game"),
            SourceItem("QQ音乐", "hotboard", "qq-music", "music_game"),
            SourceItem("英雄联盟", "hotboard", "lol", "music_game"),
            SourceItem("原神", "hotboard", "genshin", "music_game"),
            SourceItem("崩坏3", "hotboard", "honkai", "music_game"),
            SourceItem("星穹铁道", "hotboard", "starrail", "music_game"),
        ],
    ),
}


def get_all_sections() -> dict[str, Section]:
    """获取所有板块定义."""
    return SECTIONS


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    return str(value).strip().lower() in {"1", "true", "yes", "on", "启用"}


def is_source_enabled(section_key: str, source_id: str, settings: dict | None = None) -> bool:
    """检查指定板块的指定源是否启用.

    Args:
        section_key: 板块 key (social, news, tech, interest, music_game)
        source_id: 源标识 (如 news_rss, tophub, uapi 等)
        settings: 用户设置字典，为空则默认全部启用
    """
    if not settings:
        return True

    # 检查板块是否启用
    section_enabled = _as_bool(settings.get(f"section_{section_key}", True))
    if not section_enabled:
        return False

    # 检查源是否启用
    return _as_bool(settings.get(f"source_{source_id}", True))


def get_enabled_sections(settings: dict | None = None) -> dict[str, Section]:
    """根据用户设置获取启用的板块."""
    if not settings:
        return SECTIONS

    enabled = {}
    for key, section in SECTIONS.items():
        # 从 settings 读取板块启用状态，默认启用
        section_enabled = _as_bool(settings.get(f"section_{key}", True))
        if section_enabled:
            # 复制板块并过滤启用的源
            enabled_sources = []
            for src in section.sources:
                src_enabled = _as_bool(settings.get(f"source_{key}_{src.name}", True))
                if src_enabled:
                    enabled_sources.append(src)
            enabled[key] = Section(
                key=section.key,
                name=section.name,
                description=section.description,
                enabled=True,
                sources=enabled_sources,
            )
    return enabled


def get_section_summary() -> list[dict]:
    """获取板块摘要（用于 UI 展示）."""
    return [
        {
            "key": key,
            "name": section.name,
            "description": section.description,
            "source_count": len(section.sources),
            "sources": [{"name": s.name, "type": s.source_type} for s in section.sources],
        }
        for key, section in SECTIONS.items()
    ]
