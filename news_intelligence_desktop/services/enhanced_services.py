from __future__ import annotations

import json
import shutil
import csv
import io
from datetime import datetime
from pathlib import Path


class SearchService:
    def __init__(self, repo):
        self.repo = repo

    def search(self, query: str, limit: int = 50) -> list[dict]:
        with self.repo.db.connect() as conn:
            try:
                rows = conn.execute(
                    "SELECT s.item_type, s.item_id, s.title, snippet(search_index, 3, '[', ']', '...', 8) AS snippet FROM search_index s WHERE search_index MATCH ? ORDER BY rank LIMIT ?",
                    (query, limit),
                ).fetchall()
                return [dict(row) for row in rows]
            except Exception:
                return []

    def rebuild_index(self) -> int:
        count = 0
        with self.repo.db.connect() as conn:
            conn.execute("DELETE FROM search_index")
            for row in conn.execute("SELECT id, title, summary, content, category, source_name FROM articles"):
                conn.execute(
                    "INSERT INTO search_index(item_type, item_id, title, body, tags, source) VALUES('article',?,?,?,?,?)",
                    (row["id"], row["title"], f"{row['summary']}\n{row['content']}", row["category"], row["source_name"]),
                )
                count += 1
        return count


class ExportService:
    def __init__(self, repo):
        self.repo = repo

    def export_article(self, article_id: int, output_path: Path, fmt: str = "markdown") -> Path:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
            if not row:
                raise ValueError(f"Article {article_id} not found")
            art = dict(row)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            output_path.write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
        elif fmt == "html":
            html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{art['title']}</title></head>
<body><h1>{art['title']}</h1><p>{art['summary']}</p><p>来源: <a href="{art['url']}">{art['source_name']}</a></p>
<p>采集时间: {art['collected_at']}</p></body></html>"""
            output_path.write_text(html, encoding="utf-8")
        elif fmt == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["title", "summary", "source_name", "url", "category", "published_at", "credibility_score"])
            writer.writerow([art["title"], art["summary"], art["source_name"], art["url"], art["category"], art.get("published_at", ""), art["credibility_score"]])
            output_path.write_text(buf.getvalue(), encoding="utf-8")
        else:
            output_path.write_text(f"# {art['title']}\n\n{art['summary']}\n\n来源: {art['source_name']}\n链接: {art['url']}\n采集时间: {art['collected_at']}\n", encoding="utf-8")

        with self.repo.db.connect() as conn:
            conn.execute("INSERT INTO export_jobs(item_type, item_id, format, output_path, status) VALUES('article',?,?,?,?)",
                         (article_id, fmt, str(output_path), "success"))
        return output_path

    def export_report(self, brief_type: str, brief_date: str, output_path: Path, fmt: str = "markdown") -> Path:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM daily_briefs WHERE brief_type=? AND brief_date=?", (brief_type, brief_date)).fetchone()
            if not row:
                raise ValueError(f"Brief {brief_type} {brief_date} not found")
            brief = dict(row)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "html":
            output_path.write_text(f"<html><body><pre>{brief['body']}</pre></body></html>", encoding="utf-8")
        elif fmt == "json":
            output_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            output_path.write_text(brief["body"], encoding="utf-8")
        return output_path


class BackupService:
    def __init__(self, repo):
        self.repo = repo

    def create_backup(self, backup_path: Path) -> Path:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.repo.db.path, backup_path)
        with self.repo.db.connect() as conn:
            conn.execute("INSERT INTO backup_records(backup_path, status) VALUES(?, 'success')", (str(backup_path),))
        return backup_path

    def list_backups(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM backup_records ORDER BY created_at DESC LIMIT 20")]

    def restore_backup(self, backup_path: Path) -> bool:
        if not backup_path.exists():
            return False
        shutil.copy2(backup_path, self.repo.db.path)
        return True


class CredibilityService:
    FACTORS = {
        "source_tier": {"official": 0.3, "media": 0.2, "aggregator": 0.1, "unknown": 0.0},
        "multi_source": {True: 0.2, False: 0.0},
        "title_quality": {"normal": 0.1, "clickbait": -0.1},
    }

    def __init__(self, repo):
        self.repo = repo

    def explain(self, item_type: str, item_id: int) -> dict:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM credibility_explanations WHERE item_type=? AND item_id=?", (item_type, item_id)).fetchone()
            if row:
                return dict(row)
        return {"score": 0.5, "explanation": "待评估", "factors": "{}"}

    def update_score(self, item_type: str, item_id: int, score: float, explanation: str, factors: dict | None = None) -> None:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO credibility_explanations(item_type, item_id, score, explanation, factors) VALUES(?,?,?,?,?)",
                (item_type, item_id, score, explanation, json.dumps(factors or {})),
            )


class SourceHealthService:
    def __init__(self, repo):
        self.repo = repo

    def get_health(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            return [
                dict(row)
                for row in conn.execute("""
                    SELECT s.id, s.name, s.type, s.category, s.url,
                           COALESCE(h.success_count, 0) AS success_count,
                           COALESCE(h.failure_count, 0) AS failure_count,
                           COALESCE(h.avg_response_ms, 0) AS avg_response_ms,
                           h.last_success_at, h.last_error,
                           COALESCE(h.paused, 0) AS paused
                    FROM source_configs s LEFT JOIN source_health_metrics h ON h.source_id = s.id ORDER BY s.name
                """)
            ]

    def record_success(self, source_id: int, response_ms: float) -> None:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM source_health_metrics WHERE source_id=?", (source_id,)).fetchone()
            if not row:
                conn.execute("INSERT INTO source_health_metrics(source_id, success_count, avg_response_ms, last_success_at) VALUES(?,?,?,CURRENT_TIMESTAMP)", (source_id, 1, response_ms))
            else:
                cnt = row["success_count"] + 1
                avg = ((row["avg_response_ms"] * row["success_count"]) + response_ms) / cnt
                conn.execute("UPDATE source_health_metrics SET success_count=?, avg_response_ms=?, last_success_at=CURRENT_TIMESTAMP, paused=0 WHERE source_id=?", (cnt, avg, source_id))

    def record_failure(self, source_id: int, error: str) -> None:
        with self.repo.db.connect() as conn:
            conn.execute("""
                INSERT INTO source_health_metrics(source_id, failure_count, last_error, paused) VALUES(?,?,?,0)
                ON CONFLICT(source_id) DO UPDATE SET failure_count=failure_count+1, last_error=excluded.last_error,
                paused=CASE WHEN failure_count+1>=3 THEN 1 ELSE paused END
            """, (source_id, 1, error))
