from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class SourceConfig:
    id: int
    name: str
    type: str
    category: str
    url: str
    enabled: bool
    rate_limit_per_minute: int
    auth_type: str
    auth_config: dict
    parse_rules: dict
    last_success_at: str | None
    last_error: str | None


class SourceManager:
    def __init__(self, repo):
        self.repo = repo

    def list_sources(self, category: str | None = None) -> list[dict]:
        with self.repo.db.connect() as conn:
            sql = "SELECT * FROM source_configs"
            params: list = []
            if category:
                sql += " WHERE category = ?"
                params.append(category)
            sql += " ORDER BY name"
            return [dict(row) for row in conn.execute(sql, params)]

    def create_source(self, name: str, type_: str, category: str, url: str, auth_type: str = "none", auth_config: dict | None = None) -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO source_configs(name, type, category, url, auth_type, auth_config) VALUES(?,?,?,?,?,?)",
                (name, type_, category, url, auth_type, json.dumps(auth_config or {})),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def update_source(self, source_id: int, **kwargs) -> None:
        allowed = {"name", "type", "category", "url", "enabled", "rate_limit_per_minute", "auth_type", "auth_config", "parse_rules", "last_success_at", "last_error"}
        with self.repo.db.connect() as conn:
            for k, v in kwargs.items():
                if k not in allowed:
                    raise ValueError(f"Invalid source field: {k}")
                if k == "auth_config":
                    v = json.dumps(v)
                conn.execute(f"UPDATE source_configs SET {k} = ? WHERE id = ?", (v, source_id))

    def toggle_source(self, source_id: int, enabled: bool) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("UPDATE source_configs SET enabled = ? WHERE id = ?", (int(enabled), source_id))

    def test_source(self, source_id: int) -> dict:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM source_configs WHERE id = ?", (source_id,)).fetchone()
            if not row:
                return {"ok": False, "error": "Source not found"}
            src = dict(row)
        return {"ok": True, "source": src["name"], "url": src["url"], "type": src["type"]}

    def get_auth_config(self, source_id: int) -> dict:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT auth_config FROM source_configs WHERE id = ?", (source_id,)).fetchone()
            if not row:
                return {}
            try:
                return json.loads(row["auth_config"])
            except Exception:
                return {}
