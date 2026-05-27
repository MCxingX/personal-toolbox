from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
DEFAULT_HEADERS = {"User-Agent": "NewsIntelligenceDesktop/0.1"}


@dataclass
class FetchResult:
    ok: bool
    data: list[dict]
    error: str = ""
    response_ms: float = 0


class BaseConnector:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def _get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> tuple[int, dict | list | None, float]:
        hdrs = {**DEFAULT_HEADERS, **(headers or {})}
        start = time.monotonic()
        resp = requests.get(url, params=params, headers=hdrs, timeout=self.timeout)
        elapsed = (time.monotonic() - start) * 1000
        try:
            data = resp.json()
        except Exception:
            data = None
        return resp.status_code, data, elapsed

    def _get_text(self, url: str, headers: dict | None = None) -> tuple[int, str, float]:
        hdrs = {**DEFAULT_HEADERS, **(headers or {})}
        start = time.monotonic()
        resp = requests.get(url, headers=hdrs, timeout=self.timeout)
        elapsed = (time.monotonic() - start) * 1000
        return resp.status_code, resp.text, elapsed
