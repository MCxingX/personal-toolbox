from __future__ import annotations

import json
import time
import requests

from news_intelligence_desktop.connectors import BaseConnector, FetchResult


class TianapiConnector(BaseConnector):
    BASE = "https://apis.tianapi.com"

    def __init__(self, apikey: str = "", timeout: int = 15):
        super().__init__(timeout)
        self.apikey = apikey

    def fetch(self, endpoint: str, params: dict | None = None) -> FetchResult:
        if not self.apikey:
            return FetchResult(False, [], "API key not configured")
        try:
            p = {"key": self.apikey}
            if params:
                p.update(params)
            code, data, ms = self._get_json(f"{self.BASE}/{endpoint}/index", p)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            result_data = data.get("result", {})
            if isinstance(result_data, dict) and "list" in result_data:
                return FetchResult(True, result_data["list"], response_ms=ms)
            return FetchResult(True, [result_data] if result_data else [], response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))


class JuheConnector(BaseConnector):
    BASE = "https://apis.juhe.cn"

    def __init__(self, apikey: str = "", timeout: int = 15):
        super().__init__(timeout)
        self.apikey = apikey

    def fetch(self, endpoint: str, params: dict | None = None) -> FetchResult:
        if not self.apikey:
            return FetchResult(False, [], "API key not configured")
        try:
            p = {"key": self.apikey}
            if params:
                p.update(params)
            code, data, ms = self._get_json(f"{self.BASE}/{endpoint}", p)
            if code != 200 or not data:
                return FetchResult(False, [], f"HTTP {code}", ms)
            return FetchResult(True, data if isinstance(data, list) else [data], response_ms=ms)
        except Exception as e:
            return FetchResult(False, [], str(e))
