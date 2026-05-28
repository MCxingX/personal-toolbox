from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


class PersonalService:
    def __init__(self, repo):
        self.repo = repo

    def set_reading_state(self, item_type: str, item_id: int, state: str) -> None:
        allowed = {"unread", "read", "read_later", "favorite", "ignored"}
        if state not in allowed:
            raise ValueError(f"Invalid state: {state}")
        with self.repo.db.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO reading_states(item_type, item_id, state, updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP)", (item_type, item_id, state))
            if state in {"favorite", "read_later"}:
                conn.execute("INSERT OR IGNORE INTO collections(item_type, item_id, collection_type) VALUES(?,?,?)", (item_type, item_id, state))

    def get_reading_state(self, item_type: str, item_id: int) -> str:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT state FROM reading_states WHERE item_type=? AND item_id=?", (item_type, item_id)).fetchone()
            return row["state"] if row else "unread"

    def list_collection(self, collection_type: str) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT a.*, c.collection_type, c.note FROM collections c JOIN articles a ON a.id=c.item_id WHERE c.item_type='article' AND c.collection_type=? ORDER BY c.created_at DESC",
                (collection_type,),
            )]

    def add_special_favorite(self, name: str, entry_url: str, match_mode: str = "domain", match_path: str = "") -> int:
        parsed = urlparse(entry_url)
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO special_favorite_sources(name, entry_url, match_domain, match_path, match_mode, tab_order) VALUES(?,?,?,?,?,COALESCE((SELECT MAX(tab_order)+1 FROM special_favorite_sources),0))",
                (name, entry_url, parsed.netloc.lower(), match_path or parsed.path, match_mode),
            )
            fid = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            self._refresh_matches(conn, fid)
            return fid

    def list_special_tabs(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM special_favorite_sources WHERE enabled=1 ORDER BY tab_order, id")]

    def special_tab_articles(self, favorite_id: int) -> list[dict]:
        with self.repo.db.connect() as conn:
            self._refresh_matches(conn, favorite_id)
            return [dict(row) for row in conn.execute(
                "SELECT a.* FROM special_favorite_matches m JOIN articles a ON a.id=m.article_id WHERE m.favorite_id=? ORDER BY COALESCE(a.published_at, a.collected_at) DESC",
                (favorite_id,),
            )]

    def delete_special_favorite(self, favorite_id: int) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("DELETE FROM special_favorite_sources WHERE id=?", (favorite_id,))

    def _refresh_matches(self, conn, fid: int) -> None:
        fav = conn.execute("SELECT * FROM special_favorite_sources WHERE id=?", (fid,)).fetchone()
        if not fav:
            return
        for row in conn.execute("SELECT id, url, source_url FROM articles"):
            if self._matches(row["url"], fav) or self._matches(row["source_url"], fav):
                conn.execute("INSERT OR IGNORE INTO special_favorite_matches(favorite_id, article_id) VALUES(?,?)", (fid, row["id"]))

    def _matches(self, url: str, fav) -> bool:
        from urllib.parse import urlparse as up
        p = up(url)
        domain = p.netloc.lower()
        path = p.path or ""
        mode = fav["match_mode"]
        if mode == "exact":
            return url.rstrip("/") == fav["entry_url"].rstrip("/")
        if mode == "path_prefix":
            return domain == fav["match_domain"] and path.startswith(fav["match_path"])
        if mode == "custom_contains":
            return fav["match_path"] in url
        return domain == fav["match_domain"]

    def add_watchlist(self, name: str, item_type: str, keywords: list[str], priority: int = 5) -> int:
        with self.repo.db.connect() as conn:
            conn.execute("INSERT INTO watchlist_items(name, type, keywords, priority) VALUES(?,?,?,?)", (name, item_type, json.dumps(keywords, ensure_ascii=False), priority))
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def list_watchlist(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM watchlist_items ORDER BY priority DESC, id")]

    def watchlist_matches(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            items = [dict(row) for row in conn.execute("SELECT * FROM watchlist_items WHERE enabled=1")]
            articles = [dict(row) for row in conn.execute("SELECT * FROM articles")]
        matches = []
        for item in items:
            kws = json.loads(item["keywords"])
            for art in articles:
                hay = f"{art['title']} {art['summary']} {art['content']}".lower()
                if any(k.lower() in hay for k in kws):
                    matches.append({"watchlist": item, "article": art})
        return matches

    def set_privacy_mode(self, enabled: bool) -> None:
        with self.repo.db.connect() as conn:
            if enabled:
                states = {str(r["id"]): r["enabled"] for r in conn.execute("SELECT id, enabled FROM source_configs")}
                conn.execute("UPDATE source_configs SET enabled=0")
                conn.execute("INSERT OR REPLACE INTO privacy_mode_state(id,enabled,previous_source_state,updated_at) VALUES(1,1,?,CURRENT_TIMESTAMP)", (json.dumps(states),))
            else:
                row = conn.execute("SELECT previous_source_state FROM privacy_mode_state WHERE id=1").fetchone()
                states = json.loads(row["previous_source_state"] if row else "{}")
                for sid, st in states.items():
                    conn.execute("UPDATE source_configs SET enabled=? WHERE id=?", (int(st), int(sid)))
                conn.execute("UPDATE privacy_mode_state SET enabled=0, updated_at=CURRENT_TIMESTAMP WHERE id=1")

    def privacy_enabled(self) -> bool:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT enabled FROM privacy_mode_state WHERE id=1").fetchone()
            return bool(row and row["enabled"])

    def enqueue_offline_task(self, task_type: str, payload: dict) -> int:
        with self.repo.db.connect() as conn:
            conn.execute("INSERT INTO sync_queue(task_type, payload) VALUES(?,?)", (task_type, json.dumps(payload, ensure_ascii=False)))
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def pending_tasks(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM sync_queue WHERE status='pending' ORDER BY id")]
