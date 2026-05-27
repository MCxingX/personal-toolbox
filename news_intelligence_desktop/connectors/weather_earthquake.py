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
