from __future__ import annotations

import json
from datetime import datetime


class PolicyService:
    def __init__(self, repo):
        self.repo = repo

    def add_policy(self, title: str, issuer: str = "", document_no: str = "", published_at: str = "",
                   effective_at: str = "", region: str = "", category: str = "", summary: str = "",
                   source_url: str = "", source_name: str = "") -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                """INSERT INTO policy_items(title, issuer, document_no, published_at, effective_at, region, category, summary, source_url, source_name)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (title, issuer, document_no, published_at, effective_at, region, category, summary, source_url, source_name),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    def list_policies(self, region: str | None = None, category: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM policy_items WHERE 1=1"
        params: list = []
        if region:
            sql += " AND region LIKE ?"
            params.append(f"%{region}%")
        if category:
            sql += " AND category LIKE ?"
            params.append(f"%{category}%")
        sql += " ORDER BY COALESCE(published_at, collected_at) DESC, id DESC LIMIT ?"
        params.append(limit)
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def get_policy(self, policy_id: int) -> dict | None:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM policy_items WHERE id=?", (policy_id,)).fetchone()
            return dict(row) if row else None


class CaptureImportService:
    def __init__(self, repo):
        self.repo = repo

    def import_har(self, file_path: str, batch_name: str = "") -> dict:
        from pathlib import Path
        path = Path(file_path)
        if not path.exists():
            return {"ok": False, "error": "File not found"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data.get("log", {}).get("entries", [])
            count = 0
            with self.repo.db.connect() as conn:
                for entry in entries:
                    req = entry.get("request", {})
                    resp = entry.get("response", {})
                    url = req.get("url", "")
                    method = req.get("method", "GET")
                    status = resp.get("status", 0)
                    mime = resp.get("content", {}).get("mimeType", "")
                    time_ms = entry.get("time", 0)
                    size = resp.get("content", {}).get("size", 0)
                    body = resp.get("content", {}).get("text", "")[:5000]
                    headers = json.dumps(dict(h.get("name", ""): h.get("value", "") for h in req.get("headers", [])), ensure_ascii=False)
                    conn.execute(
                        "INSERT INTO captured_exchanges(import_batch, url, method, status_code, mime_type, response_time_ms, response_size, request_headers, response_body) VALUES(?,?,?,?,?,?,?,?,?)",
                        (batch_name or path.name, url, method, status, mime, time_ms, size, headers, body),
                    )
                    count += 1
            return {"ok": True, "count": count, "batch": batch_name or path.name}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def import_json(self, file_path: str, batch_name: str = "") -> dict:
        from pathlib import Path
        path = Path(file_path)
        if not path.exists():
            return {"ok": False, "error": "File not found"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            count = 0
            with self.repo.db.connect() as conn:
                for item in items:
                    if isinstance(item, dict):
                        url = item.get("url", item.get("link", ""))
                        title = item.get("title", "")
                        summary = item.get("summary", item.get("description", ""))[:500]
                        if url or title:
                            conn.execute(
                                "INSERT INTO import_candidates(candidate_type, title, summary, url, status) VALUES(?,?,?,?,?)",
                                ("json_item", title, summary, url, "pending"),
                            )
                            count += 1
            return {"ok": True, "count": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_exchanges(self, batch: str | None = None, limit: int = 100) -> list[dict]:
        sql = "SELECT * FROM captured_exchanges"
        params: list = []
        if batch:
            sql += " WHERE import_batch = ?"
            params.append(batch)
        sql += " ORDER BY collected_at DESC LIMIT ?"
        params.append(limit)
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def list_candidates(self, status: str | None = None) -> list[dict]:
        sql = "SELECT * FROM import_candidates"
        params: list = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC"
        with self.repo.db.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def confirm_candidate(self, candidate_id: int) -> int:
        with self.repo.db.connect() as conn:
            row = conn.execute("SELECT * FROM import_candidates WHERE id=?", (candidate_id,)).fetchone()
            if not row:
                return 0
            conn.execute("UPDATE import_candidates SET status='confirmed' WHERE id=?", (candidate_id,))
            return candidate_id


class RegionService:
    REGIONS = {
        "national": "全国",
        "beijing": "北京", "shanghai": "上海", "guangdong": "广东", "shenzhen": "深圳",
        "hangzhou": "杭州", "chengdu": "成都", "wuhan": "武汉", "nanjing": "南京",
    }

    def __init__(self, repo):
        self.repo = repo

    def list_regions(self) -> list[dict]:
        return [{"key": k, "label": v} for k, v in self.REGIONS.items()]

    def detect_region(self, text: str) -> list[str]:
        regions = []
        for key, label in self.REGIONS.items():
            if label in text or key in text.lower():
                regions.append(key)
        return regions
