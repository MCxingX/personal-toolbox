from __future__ import annotations

import json
import time
import requests


class GenericApiCaller:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def call(self, base_url: str, params: dict | None = None, method: str = "GET", headers: dict | None = None) -> dict:
        start = time.monotonic()
        try:
            if method.upper() == "GET":
                resp = requests.get(base_url, params=params, headers=headers or {}, timeout=self.timeout)
            else:
                resp = requests.post(base_url, data=params, headers=headers or {}, timeout=self.timeout)
            elapsed = (time.monotonic() - start) * 1000
            try:
                data = resp.json()
            except Exception:
                data = resp.text[:2000]
            return {
                "ok": resp.status_code < 400,
                "status_code": resp.status_code,
                "data": data,
                "response_time_ms": elapsed,
                "response_size": len(resp.content),
            }
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return {"ok": False, "status_code": 0, "data": None, "error": str(e), "response_time_ms": elapsed, "response_size": 0}
