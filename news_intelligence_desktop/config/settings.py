from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    data_dir: Path
    db_path: Path
    config_path: Path
    log_dir: Path

    @classmethod
    def load(cls, data_dir: Path | None = None) -> "AppSettings":
        root = data_dir or Path(os.environ.get("NEWS_INTEL_DATA_DIR", Path.home() / ".news_intelligence_desktop"))
        root = root.expanduser().resolve()
        settings = cls(
            data_dir=root,
            db_path=root / "news_intelligence.sqlite3",
            config_path=root / "config.json",
            log_dir=root / "logs",
        )
        settings.ensure_directories()
        settings.ensure_config()
        return settings

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def ensure_config(self) -> None:
        if self.config_path.exists():
            return
        payload = {
            "first_run": True,
            "privacy_mode": False,
            "home_cards": [
                "今日总览",
                "技术变化",
                "重要新闻",
                "政策变化",
                "本地事件",
                "热点吃瓜",
                "天气地震",
                "每日语录",
            ],
        }
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
