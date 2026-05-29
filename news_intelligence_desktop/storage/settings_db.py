"""应用设置存储 - 管理 API Key 等用户配置."""

from __future__ import annotations

import sqlite3
import logging

logger = logging.getLogger(__name__)


class SettingsDB:
    """应用设置存储."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化设置表."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get(self, key: str, default: str = "") -> str:
        """获取设置值."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        """设置值."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_settings(key, value, updated_at) VALUES(?, ?, CURRENT_TIMESTAMP)",
                (key, value),
            )
            conn.commit()

    def get_all(self) -> dict[str, str]:
        """获取所有设置."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
            return {row["key"]: row["value"] for row in rows}
