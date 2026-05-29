from __future__ import annotations

import re
from datetime import date


def _is_chinese(text: str) -> bool:
    """判断文本是否主要是中文."""
    if not text:
        return False
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return False
    return chinese_chars / total_chars >= 0.3


class HomeDashboardService:
    def __init__(self, repo, quote_service=None, tech_service=None):
        self.repo = repo
        self.quote_service = quote_service
        self.tech_service = tech_service

    def generate(self) -> dict:
        # 分别从各分类获取数据
        tech_articles = self.repo.list_articles(category="tech", limit=30)
        news_articles = self.repo.list_articles(category="news", limit=30)
        policy_articles = self.repo.list_articles(category="policy", limit=20)
        finance_articles = self.repo.list_articles(category="finance", limit=15)
        security_articles = self.repo.list_articles(category="security", limit=15)
        science_articles = self.repo.list_articles(category="science", limit=15)

        # 全局中文过滤
        tech_zh = [a for a in tech_articles if _is_chinese(a.get("title", ""))]
        news_zh = [a for a in news_articles if _is_chinese(a.get("title", ""))]
        policy_zh = [a for a in policy_articles if _is_chinese(a.get("title", ""))]
        finance_zh = [a for a in finance_articles if _is_chinese(a.get("title", ""))]
        security_zh = [a for a in security_articles if _is_chinese(a.get("title", ""))]
        science_zh = [a for a in science_articles if _is_chinese(a.get("title", ""))]

        # 今日早晚报（中文优先）
        daily_articles = self._get_daily_report(zh_only=True)

        # 地震数据
        earthquake_items = self._get_earthquakes()

        # 天气详情
        weather_info = self._get_weather_detail()

        quote = self.quote_service.get_home_quote() if self.quote_service else {"content": "今天也要加油！", "style_label": "每日语录"}
        tech_changes = self.tech_service.list_changes(limit=5) if self.tech_service else []

        cards = [
            {"name": "今日早晚报", "summary": f"全网中文热点 {len(daily_articles)} 条", "count": len(daily_articles), "items": daily_articles[:10]},
            {"name": "国内新闻", "summary": self._first_title(news_zh, "暂无国内新闻"), "count": len(news_zh), "items": news_zh[:8]},
            {"name": "技术动态", "summary": self._first_title(tech_zh, "暂无技术动态"), "count": len(tech_zh), "items": tech_zh[:8]},
            {"name": "政策法规", "summary": self._first_title(policy_zh, "暂无政策变化"), "count": len(policy_zh), "items": policy_zh[:8]},
            {"name": "财经金融", "summary": self._first_title(finance_zh, "暂无财经信息"), "count": len(finance_zh), "items": finance_zh[:8]},
            {"name": "安全资讯", "summary": self._first_title(security_zh, "暂无安全资讯"), "count": len(security_zh), "items": security_zh[:8]},
            {"name": "科技前沿", "summary": self._first_title(science_zh, "暂无科技资讯"), "count": len(science_zh), "items": science_zh[:8]},
            {"name": "地震速报", "summary": self._earthquake_summary(earthquake_items), "count": len(earthquake_items), "items": earthquake_items[:5]},
            {"name": "天气详情", "summary": weather_info.get("summary", "暂无天气数据"), "count": weather_info.get("count", 0), "items": weather_info.get("items", []), "weather_detail": weather_info},
            {"name": "每日语录", "summary": quote.get("content", ""), "count": 1, "items": [], "quote": quote},
        ]

        return {
            "title": f"{date.today().isoformat()} 个人每日信息中枢",
            "date": date.today().isoformat(),
            "privacy_mode": self.repo.privacy_mode_enabled(),
            "cards": cards,
            "special_tabs": self.repo.list_special_tabs(),
            "tech_changes": tech_changes,
        }

    def _get_daily_report(self, zh_only: bool = True) -> list[dict]:
        """获取今日早晚报数据（来源：tophub + uapi 热榜）."""
        all_articles = self.repo.list_articles(limit=1000)
        daily = [a for a in all_articles if (
            a.get("source_name", "").startswith("tophub-") or
            a.get("source_name", "").startswith("uapi-")
        )]
        if zh_only:
            daily = [a for a in daily if _is_chinese(a.get("title", ""))]
        daily.sort(key=lambda x: x.get("collected_at", ""), reverse=True)
        return daily

    def _get_earthquakes(self) -> list[dict]:
        """获取地震数据."""
        with self.repo.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 10"
            ).fetchall()
            items = []
            for row in rows:
                r = dict(row)
                mag = r.get("magnitude", 0)
                place = r.get("place", "")
                time_str = r.get("event_time", "")[:16].replace("T", " ")
                items.append({
                    "title": f"M{mag} {place}",
                    "summary": f"震级 {mag} | {place} | {time_str}",
                    "source_name": r.get("source", "usgs"),
                    "url": r.get("detail_url", ""),
                    "category": "earthquake",
                    "collected_at": r.get("collected_at", ""),
                })
            return items

    def _earthquake_summary(self, items: list[dict]) -> str:
        if items:
            return items[0]["summary"]
        return "暂无地震数据"

    def _get_weather_detail(self) -> dict:
        """获取详细天气信息."""
        with self.repo.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM weather_forecasts ORDER BY collected_at DESC LIMIT 12"
            ).fetchall()
            if not rows:
                return {"summary": "暂无天气数据", "count": 0, "items": []}

            items = []
            for row in rows:
                r = dict(row)
                loc = r.get("location_name", "")
                desc = r.get("description", "")
                high = r.get("temp_high", "")
                low = r.get("temp_low", "")
                humidity = r.get("humidity", "")
                wind = r.get("wind_speed", "")
                feels = r.get("feels_like", "")
                uv = r.get("uv_index", "")
                date_str = r.get("forecast_date", "")

                detail_parts = [f"{loc} {date_str}"]
                if desc:
                    detail_parts.append(desc)
                if high and low:
                    detail_parts.append(f"{low}~{high}°C")
                if feels:
                    detail_parts.append(f"体感{feels}°C")
                if humidity:
                    detail_parts.append(f"湿度{humidity}%")
                if wind:
                    detail_parts.append(f"风速{wind}km/h")
                if uv:
                    detail_parts.append(f"UV{uv}")

                items.append({
                    "title": f"{loc} {date_str}",
                    "summary": " | ".join(detail_parts),
                    "source_name": r.get("source", ""),
                    "category": "weather",
                    "collected_at": r.get("collected_at", ""),
                })

            # 最新一条作为摘要
            latest = dict(rows[0])
            summary_parts = [
                latest.get("location_name", ""),
                latest.get("forecast_date", ""),
                latest.get("description", ""),
            ]
            if latest.get("temp_low") and latest.get("temp_high"):
                summary_parts.append(f"{latest['temp_low']}~{latest['temp_high']}°C")
            if latest.get("feels_like"):
                summary_parts.append(f"体感{latest['feels_like']}°C")
            if latest.get("humidity"):
                summary_parts.append(f"湿度{latest['humidity']}%")

            return {
                "summary": " ".join(filter(None, summary_parts)),
                "count": len(items),
                "items": items[:6],
            }

    def _first_title(self, items: list[dict], fallback: str) -> str:
        return items[0]["title"] if items else fallback
