from __future__ import annotations

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class WeatherConnector(BaseConnector):
    OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

    def fetch_forecast(self, lat: float = 39.9, lon: float = 116.4, days: int = 7) -> FetchResult:
        try:
            code, data, ms = self._get_json(self.OPEN_METEO, {
                "latitude": lat, "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum",
                "hourly": "temperature_2m,weathercode",
                "forecast_days": days,
                "timezone": "auto",
            })
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            daily = data.get("daily", {})
            results = []
            dates = daily.get("time", [])
            for i, d in enumerate(dates):
                results.append({
                    "date": d,
                    "temp_high": daily.get("temperature_2m_max", [None])[i],
                    "temp_low": daily.get("temperature_2m_min", [None])[i],
                    "weathercode": daily.get("weathercode", [0])[i],
                    "precipitation": daily.get("precipitation_sum", [0])[i],
                    "lat": lat, "lon": lon,
                    "source": "open-meteo",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class WttrConnector(BaseConnector):
    """wttr.in 免费天气服务，无需 key，支持中文城市名."""

    BASE = "https://wttr.in"
    CODE_MAP = {
        113: "晴", 116: "多云", 119: "阴", 122: "阴", 143: "雾",
        176: "小阵雨", 179: "小阵雪", 182: "雨夹雪", 185: "冻雨",
        200: "雷阵雨", 227: "吹雪", 230: "暴风雪", 248: "雾", 260: "冻雾",
        263: "小阵雨", 266: "小雨", 281: "冻雨", 284: "冻雨",
        293: "小雨", 296: "小雨", 299: "中雨", 302: "中雨", 305: "大雨", 308: "大雨",
        311: "冻雨", 314: "冻雨", 317: "雨夹雪", 320: "中雪", 323: "小雪", 326: "小雪",
        329: "中雪", 332: "中雪", 335: "大雪", 338: "大雪", 350: "冰粒", 353: "小阵雨",
        356: "中阵雨", 359: "大阵雨", 362: "小阵雪", 365: "中阵雪", 368: "小阵雪",
        371: "中阵雪", 374: "冰粒", 377: "冰粒", 386: "雷阵雨", 389: "雷暴",
        392: "雷阵雪", 395: "雷暴雪",
    }

    def fetch_weather(self, city: str = "北京") -> FetchResult:
        try:
            code, data, ms = self._get_json(f"{self.BASE}/{city}", {"format": "j1"})
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            hourly = data.get("hourly", [])
            for idx, day in enumerate(data.get("weather", [])):
                wcode = 0
                desc = ""
                humidity = ""
                wind_speed = ""
                feels_like = ""
                uv_index = ""
                if len(hourly) > 4:
                    h = hourly[4]
                    wcode = int(h.get("weatherCode", 0))
                    zh_list = h.get("lang_zh", [])
                    desc = zh_list[0].get("value", "") if zh_list else ""
                    humidity = h.get("humidity", "")
                    wind_speed = h.get("windspeedKmph", "")
                    feels_like = h.get("FeelsLikeC", "")
                    uv_index = h.get("uvIndex", "")
                if not desc:
                    desc = self.CODE_MAP.get(wcode, "")
                results.append({
                    "date": day.get("date", ""),
                    "temp_high": int(day.get("maxtempC", 0)),
                    "temp_low": int(day.get("mintempC", 0)),
                    "weathercode": wcode,
                    "description": desc,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "feels_like": feels_like,
                    "uv_index": uv_index,
                    "lat": float(data.get("nearest_area", [{}])[0].get("latitude", 0)),
                    "lon": float(data.get("nearest_area", [{}])[0].get("longitude", 0)),
                    "source": "wttr.in",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class CeicRssConnector(BaseConnector):
    """中国地震台网 RSS 实时地震速报."""

    CEIC_RSS = "http://news.ceic.ac.cn/rss"

    def fetch_recent(self, limit: int = 50) -> FetchResult:
        try:
            import feedparser
            code, text, ms = self._get_text(self.CEIC_RSS)
            if code != 200:
                return FetchResult(False, [], f"HTTP {code}", ms)
            feed = feedparser.parse(text)
            results = []
            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                results.append({
                    "event_id": f"ceic-{entry.get('id', entry.get('link', ''))}",
                    "magnitude": self._extract_mag(title),
                    "place": title,
                    "event_time": entry.get("published", entry.get("updated", "")),
                    "longitude": 0, "latitude": 0, "depth_km": 0,
                    "detail_url": entry.get("link", ""),
                    "source": "ceic",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))

    def _extract_mag(self, title: str) -> float:
        import re
        m = re.search(r"(\d+\.?\d*)\s*[级M]", title)
        return float(m.group(1)) if m else 0


class EarthquakeConnector(BaseConnector):
    USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def fetch_recent(self, min_magnitude: float = 4.0, limit: int = 50) -> FetchResult:
        try:
            code, data, ms = self._get_json(self.USGS_URL, {
                "format": "geojson", "minmagnitude": min_magnitude,
                "limit": limit, "orderby": "time",
            })
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            results = []
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                geom = feat.get("geometry", {}).get("coordinates", [0, 0, 0])
                from datetime import datetime, timezone
                t = props.get("time", 0)
                dt = datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat()
                results.append({
                    "event_id": feat.get("id", ""),
                    "magnitude": props.get("mag", 0),
                    "place": props.get("place", ""),
                    "event_time": dt,
                    "longitude": geom[0] if len(geom) > 0 else 0,
                    "latitude": geom[1] if len(geom) > 1 else 0,
                    "depth_km": geom[2] if len(geom) > 2 else 0,
                    "detail_url": props.get("url", ""),
                    "source": "usgs",
                })
            return FetchResult(True, results, response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
