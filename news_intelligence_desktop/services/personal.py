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

    def get_collection_stats(self) -> dict:
        """获取收藏统计."""
        with self.repo.db.connect() as conn:
            favorites = conn.execute("SELECT COUNT(*) as c FROM collections WHERE collection_type='favorite'").fetchone()["c"]
            read_later = conn.execute("SELECT COUNT(*) as c FROM collections WHERE collection_type='read_later'").fetchone()["c"]
            special = conn.execute("SELECT COUNT(*) as c FROM special_favorite_sources WHERE enabled=1").fetchone()["c"]
            watchlist = conn.execute("SELECT COUNT(*) as c FROM watchlist_items WHERE enabled=1").fetchone()["c"]

            # 阅读状态统计
            read_count = conn.execute("SELECT COUNT(*) as c FROM reading_states WHERE state='read'").fetchone()["c"]
            unread_count = conn.execute("SELECT COUNT(*) as c FROM articles").fetchone()["c"] - read_count

            return {
                "favorites": favorites,
                "read_later": read_later,
                "special_tabs": special,
                "watchlist": watchlist,
                "read": read_count,
                "unread": unread_count,
            }

    def get_reading_history(self, limit: int = 50) -> list[dict]:
        """获取阅读历史."""
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute(
                """SELECT a.*, rs.state, rs.updated_at as read_at
                FROM reading_states rs
                JOIN articles a ON a.id = rs.item_id
                WHERE rs.item_type = 'article'
                ORDER BY rs.updated_at DESC
                LIMIT ?""",
                (limit,),
            )]

    def remove_from_collection(self, item_type: str, item_id: int, collection_type: str) -> bool:
        """从收藏中移除."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM collections WHERE item_type=? AND item_id=? AND collection_type=?",
                (item_type, item_id, collection_type),
            )
            # 同时更新阅读状态
            if collection_type == "favorite":
                conn.execute(
                    "UPDATE reading_states SET state='read' WHERE item_type=? AND item_id=?",
                    (item_type, item_id),
                )
            elif collection_type == "read_later":
                conn.execute(
                    "UPDATE reading_states SET state='read' WHERE item_type=? AND item_id=?",
                    (item_type, item_id),
                )
            return cursor.rowcount > 0

    def add_note_to_collection(self, item_type: str, item_id: int, collection_type: str, note: str) -> bool:
        """添加收藏备注."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE collections SET note=? WHERE item_type=? AND item_id=? AND collection_type=?",
                (note, item_type, item_id, collection_type),
            )
            return cursor.rowcount > 0

    def update_watchlist(self, watchlist_id: int, **kwargs) -> bool:
        """更新关注清单."""
        allowed = {"name", "type", "keywords", "exclude_words", "priority", "enabled", "note"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        if "keywords" in updates and isinstance(updates["keywords"], list):
            updates["keywords"] = json.dumps(updates["keywords"], ensure_ascii=False)
        if "exclude_words" in updates and isinstance(updates["exclude_words"], list):
            updates["exclude_words"] = json.dumps(updates["exclude_words"], ensure_ascii=False)
        if "enabled" in updates:
            updates["enabled"] = 1 if updates["enabled"] else 0

        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [watchlist_id]

        with self.repo.db.connect() as conn:
            cursor = conn.execute(f"UPDATE watchlist_items SET {set_clause} WHERE id=?", values)
            return cursor.rowcount > 0

    def delete_watchlist(self, watchlist_id: int) -> bool:
        """删除关注项."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute("DELETE FROM watchlist_items WHERE id=?", (watchlist_id,))
            return cursor.rowcount > 0

    def generate_daily_brief(self, brief_type: str = "morning") -> dict:
        """生成每日简报."""
        from datetime import date
        today = date.today().isoformat()

        with self.repo.db.connect() as conn:
            # 检查是否已生成
            existing = conn.execute(
                "SELECT * FROM daily_briefs WHERE brief_type=? AND brief_date=?",
                (brief_type, today),
            ).fetchone()

            if existing:
                return dict(existing)

            # 获取今日文章
            articles = [dict(row) for row in conn.execute(
                """SELECT * FROM articles
                WHERE date(collected_at) = ?
                ORDER BY importance_score DESC, collected_at DESC
                LIMIT 20""",
                (today,),
            )]

            if not articles:
                # 获取最新文章
                articles = [dict(row) for row in conn.execute(
                    """SELECT * FROM articles
                    ORDER BY collected_at DESC
                    LIMIT 10"""
                )]

            # 生成简报
            if brief_type == "morning":
                title = f"早报 - {today}"
                body = self._generate_morning_brief(articles, today)
            else:
                title = f"晚报 - {today}"
                body = self._generate_evening_brief(articles, today)

            # 保存简报
            conn.execute(
                "INSERT INTO daily_briefs(brief_type, brief_date, title, body) VALUES(?,?,?,?)",
                (brief_type, today, title, body),
            )

            return {
                "brief_type": brief_type,
                "brief_date": today,
                "title": title,
                "body": body,
            }

    def _generate_morning_brief(self, articles: list[dict], today: str) -> str:
        """生成早报内容."""
        lines = [f"# 早报 - {today}", ""]

        # 按分类分组
        by_category = {}
        for art in articles:
            cat = art.get("category", "其他")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(art)

        category_names = {
            "news": "新闻",
            "tech": "科技",
            "hot": "热点",
            "policy": "政策",
            "finance": "财经",
            "security": "安全",
        }

        for cat, items in by_category.items():
            cat_name = category_names.get(cat, cat)
            lines.append(f"## {cat_name}")
            for item in items[:3]:
                lines.append(f"- {item['title']}")
                if item.get("summary"):
                    lines.append(f"  {item['summary'][:100]}")
            lines.append("")

        lines.append("---")
        lines.append(f"共 {len(articles)} 条资讯")

        return "\n".join(lines)

    def _generate_evening_brief(self, articles: list[dict], today: str) -> str:
        """生成晚报内容."""
        lines = [f"# 晚报 - {today}", ""]

        # 重要文章
        important = [a for a in articles if a.get("importance_score", 0) >= 0.7]
        if important:
            lines.append("## 重要资讯")
            for item in important[:5]:
                lines.append(f"- {item['title']}")
                if item.get("summary"):
                    lines.append(f"  {item['summary'][:100]}")
            lines.append("")

        # 其他文章
        others = [a for a in articles if a.get("importance_score", 0) < 0.7]
        if others:
            lines.append("## 其他资讯")
            for item in others[:5]:
                lines.append(f"- {item['title']}")
            lines.append("")

        lines.append("---")
        lines.append(f"共 {len(articles)} 条资讯")

        return "\n".join(lines)

    def list_daily_briefs(self, brief_type: str = "", limit: int = 10) -> list[dict]:
        """列出每日简报."""
        with self.repo.db.connect() as conn:
            if brief_type:
                return [dict(row) for row in conn.execute(
                    "SELECT * FROM daily_briefs WHERE brief_type=? ORDER BY brief_date DESC LIMIT ?",
                    (brief_type, limit),
                )]
            else:
                return [dict(row) for row in conn.execute(
                    "SELECT * FROM daily_briefs ORDER BY brief_date DESC LIMIT ?",
                    (limit,),
                )]
