"""抓包文件导入 - 支持 HAR、HTML、JSON 格式."""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def datetime_now_iso() -> str:
    return datetime.now().isoformat()

# 敏感字段脱敏规则
SENSITIVE_PATTERNS = [
    (r'(cookie|token|auth|password|secret|key)[^=]*=\s*["\']?([^\s"\';,]+)', r'\1=***'),
    (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***'),
    (r'Basic\s+[A-Za-z0-9+/]+=*', 'Basic ***'),
    (r'\b1[3-9]\d{9}\b', '1**********'),  # 手机号
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***'),  # 邮箱
]

# 新闻相关的内容类型
NEWS_CONTENT_TYPES = [
    "application/json",
    "text/html",
    "text/xml",
    "application/xml",
    "application/rss+xml",
    "application/atom+xml",
]

# 新闻相关的关键词
NEWS_KEYWORDS = [
    "news", "article", "post", "feed", "rss", "atom",
    "headline", "story", "blog", "press", "release",
    "新闻", "资讯", "文章", "头条", "快讯",
]


@dataclass
class CapturedExchange:
    """抓包数据条目."""
    url: str
    method: str = "GET"
    status_code: int = 0
    mime_type: str = ""
    response_time_ms: float = 0
    response_size: int = 0
    request_headers: dict = field(default_factory=dict)
    response_body: str = ""
    collected_at: str = ""


@dataclass
class ImportCandidate:
    """导入候选条目."""
    exchange_id: int = 0
    candidate_type: str = "article"  # article, feed, api
    title: str = ""
    summary: str = ""
    url: str = ""
    status: str = "pending"


class HarParser:
    """HAR 文件解析器."""

    def parse(self, file_path: Path) -> list[CapturedExchange]:
        """解析 HAR 文件."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                har_data = json.load(f)

            entries = har_data.get("log", {}).get("entries", [])
            exchanges = []

            for entry in entries:
                request = entry.get("request", {})
                response = entry.get("response", {})

                url = request.get("url", "")
                method = request.get("method", "GET")
                status = response.get("status", 0)
                mime_type = response.get("content", {}).get("mimeType", "")
                size = response.get("content", {}).get("size", 0)
                time_ms = entry.get("time", 0)

                # 提取响应内容
                content = response.get("content", {})
                text = content.get("text", "")
                encoding = content.get("encoding", "")

                if encoding == "base64" and text:
                    try:
                        import base64
                        text = base64.b64decode(text).decode("utf-8", errors="ignore")
                    except Exception:
                        pass

                # 提取请求头
                headers = {}
                for h in request.get("headers", []):
                    headers[h.get("name", "")] = h.get("value", "")

                exchanges.append(CapturedExchange(
                    url=url,
                    method=method,
                    status_code=status,
                    mime_type=mime_type,
                    response_time_ms=time_ms,
                    response_size=size,
                    request_headers=headers,
                    response_body=text[:5000],  # 限制长度
                    collected_at=entry.get("startedDateTime", ""),
                ))

            return exchanges

        except Exception as e:
            logger.error("HAR 解析失败: %s", e)
            return []


class HtmlParser:
    """HTML 文件解析器."""

    def parse(self, file_path: Path) -> list[CapturedExchange]:
        """解析 HTML 文件，提取链接和内容."""
        try:
            from bs4 import BeautifulSoup

            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

            soup = BeautifulSoup(html, "html.parser")
            exchanges = []

            # 提取所有链接
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                title = link.get_text(strip=True)

                if not href or not title:
                    continue

                # 处理相对路径
                if href.startswith("/"):
                    href = f"file://{href}"

                exchanges.append(CapturedExchange(
                    url=href,
                    method="GET",
                    status_code=200,
                    mime_type="text/html",
                    response_body=title,
                ))

            return exchanges

        except Exception as e:
            logger.error("HTML 解析失败: %s", e)
            return []


class JsonParser:
    """JSON 文件解析器."""

    def parse(self, file_path: Path) -> list[CapturedExchange]:
        """解析 JSON 文件."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            exchanges = []

            # 尝试解析为数组
            if isinstance(data, list):
                for item in data:
                    exchange = self._extract_exchange(item)
                    if exchange:
                        exchanges.append(exchange)
            elif isinstance(data, dict):
                # 尝试找到数据数组
                for key in ["data", "items", "entries", "results", "list"]:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            exchange = self._extract_exchange(item)
                            if exchange:
                                exchanges.append(exchange)
                        break

            return exchanges

        except Exception as e:
            logger.error("JSON 解析失败: %s", e)
            return []

    def _extract_exchange(self, item: dict) -> CapturedExchange | None:
        """从 JSON 对象中提取 exchange."""
        if not isinstance(item, dict):
            return None

        url = item.get("url") or item.get("link") or item.get("href", "")
        if not url:
            return None

        return CapturedExchange(
            url=url,
            method=item.get("method", "GET"),
            status_code=item.get("status_code", 200),
            mime_type=item.get("mime_type", "application/json"),
            response_body=json.dumps(item, ensure_ascii=False)[:5000],
        )


class PacketCaptureImporter:
    """抓包文件导入器."""

    def __init__(self, repo):
        self.repo = repo
        self.har_parser = HarParser()
        self.html_parser = HtmlParser()
        self.json_parser = JsonParser()

    def import_file(self, file_path: Path, batch_name: str = "") -> dict:
        """导入抓包文件."""
        if not file_path.exists():
            return {"success": False, "error": "文件不存在"}

        suffix = file_path.suffix.lower()
        if not batch_name:
            batch_name = f"{file_path.stem}_{int(time.time())}"

        # 根据文件类型解析
        if suffix == ".har":
            exchanges = self.har_parser.parse(file_path)
        elif suffix in [".html", ".htm"]:
            exchanges = self.html_parser.parse(file_path)
        elif suffix == ".json":
            exchanges = self.json_parser.parse(file_path)
        else:
            return {"success": False, "error": f"不支持的文件格式: {suffix}"}

        if not exchanges:
            return {"success": False, "error": "未解析到有效数据"}

        # 保存到数据库
        saved_count = 0
        candidates = []

        for exchange in exchanges:
            # 脱敏处理
            sanitized_headers = self._sanitize_headers(exchange.request_headers)
            sanitized_body = self._sanitize_content(exchange.response_body)

            # 保存 exchange
            exchange_id = self._save_exchange(batch_name, exchange, sanitized_headers, sanitized_body)
            if exchange_id:
                saved_count += 1

                # 识别候选内容
                safe_exchange = CapturedExchange(
                    url=exchange.url,
                    method=exchange.method,
                    status_code=exchange.status_code,
                    mime_type=exchange.mime_type,
                    response_time_ms=exchange.response_time_ms,
                    response_size=exchange.response_size,
                    request_headers={},
                    response_body=sanitized_body,
                    collected_at=exchange.collected_at,
                )
                candidate = self._identify_candidate(safe_exchange, exchange_id)
                if candidate:
                    candidates.append(candidate)

        return {
            "success": True,
            "batch_name": batch_name,
            "total_exchanges": len(exchanges),
            "saved_exchanges": saved_count,
            "candidates": len(candidates),
        }

    def _save_exchange(self, batch: str, exchange: CapturedExchange, headers: str, body: str) -> int | None:
        """保存 exchange 到数据库."""
        try:
            with self.repo.db.connect() as conn:
                cursor = conn.execute(
                    """INSERT INTO captured_exchanges(import_batch, url, method, status_code,
                    mime_type, response_time_ms, response_size, request_headers, response_body, collected_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (
                        batch,
                        exchange.url,
                        exchange.method,
                        exchange.status_code,
                        exchange.mime_type,
                        exchange.response_time_ms,
                        exchange.response_size,
                        headers,
                        body,
                        exchange.collected_at or datetime_now_iso(),
                    ),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error("保存 exchange 失败: %s", e)
            return None

    def _identify_candidate(self, exchange: CapturedExchange, exchange_id: int) -> ImportCandidate | None:
        """识别候选内容."""
        url = exchange.url.lower()
        mime = exchange.mime_type.lower()

        # 检查是否为新闻相关内容
        is_news = False

        # MIME 类型检查
        for ct in NEWS_CONTENT_TYPES:
            if ct in mime:
                is_news = True
                break

        # URL 关键词检查
        for keyword in NEWS_KEYWORDS:
            if keyword in url:
                is_news = True
                break

        if not is_news:
            return None

        # 尝试提取标题
        title = ""
        body = exchange.response_body

        if mime.startswith("application/json"):
            try:
                data = json.loads(body)
                title = self._extract_title_from_json(data)
            except Exception:
                pass
        elif mime.startswith("text/html"):
            title = self._extract_title_from_html(body)

        if not title:
            return None

        # 保存候选
        try:
            with self.repo.db.connect() as conn:
                conn.execute(
                    """INSERT INTO import_candidates(exchange_id, candidate_type, title, summary, url, status)
                    VALUES(?,?,?,?,?,?)""",
                    (exchange_id, "article", title[:200], "", exchange.url, "pending"),
                )
        except Exception:
            pass

        return ImportCandidate(
            exchange_id=exchange_id,
            candidate_type="article",
            title=title,
            url=exchange.url,
        )

    def _extract_title_from_json(self, data: Any) -> str:
        """从 JSON 中提取标题."""
        if isinstance(data, dict):
            for key in ["title", "name", "headline", "subject"]:
                if key in data and isinstance(data[key], str):
                    return data[key]
            # 递归查找
            for value in data.values():
                if isinstance(value, (dict, list)):
                    title = self._extract_title_from_json(value)
                    if title:
                        return title
        elif isinstance(data, list):
            for item in data[:5]:
                title = self._extract_title_from_json(item)
                if title:
                    return title
        return ""

    def _extract_title_from_html(self, html: str) -> str:
        """从 HTML 中提取标题."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            title = soup.find("title")
            if title:
                return title.get_text(strip=True)
            h1 = soup.find("h1")
            if h1:
                return h1.get_text(strip=True)
        except Exception:
            pass
        return ""

    def _sanitize_headers(self, headers: dict) -> str:
        """脱敏请求头."""
        result = {}
        for key, value in headers.items():
            lower_key = key.lower()
            if any(s in lower_key for s in ["cookie", "token", "auth", "password", "secret"]):
                result[key] = "***"
            else:
                result[key] = value
        return json.dumps(result, ensure_ascii=False)

    def _sanitize_content(self, content: str) -> str:
        """脱敏内容."""
        if not content:
            return ""

        result = content
        for pattern, replacement in SENSITIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result[:5000]  # 限制长度

    def list_candidates(self, batch: str = "", status: str = "") -> list[dict]:
        """列出候选内容."""
        with self.repo.db.connect() as conn:
            sql = """
                SELECT ic.*, ce.url as exchange_url, ce.mime_type
                FROM import_candidates ic
                LEFT JOIN captured_exchanges ce ON ic.exchange_id = ce.id
            """
            conditions = []
            params = []

            if batch:
                conditions.append("ce.import_batch = ?")
                params.append(batch)
            if status:
                conditions.append("ic.status = ?")
                params.append(status)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            sql += " ORDER BY ic.created_at DESC LIMIT 100"

            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def confirm_candidate(self, candidate_id: int) -> bool:
        """确认候选内容为正式文章."""
        with self.repo.db.connect() as conn:
            row = conn.execute(
                "SELECT * FROM import_candidates WHERE id=? AND status='pending'",
                (candidate_id,),
            ).fetchone()

            if not row:
                return False

            candidate = dict(row)

            # 获取 exchange 数据
            exchange = conn.execute(
                "SELECT * FROM captured_exchanges WHERE id=?",
                (candidate["exchange_id"],),
            ).fetchone()

            if not exchange:
                return False

            exchange = dict(exchange)

        # 保存为文章，避免在同一个 SQLite 写事务里嵌套打开连接。
        from news_intelligence_desktop.storage.repository import ArticleInput
        article = ArticleInput(
            title=candidate["title"][:200],
            summary=candidate.get("summary", "")[:500],
            source_name=urlparse(exchange["url"]).netloc or "本地抓包导入",
            source_url=exchange["url"],
            url=candidate.get("url") or exchange["url"],
            category="imported",
            language="zh",
        )
        self.repo.add_article(article)

        # 更新状态
        with self.repo.db.connect() as conn:
            conn.execute(
                "UPDATE import_candidates SET status='confirmed' WHERE id=?",
                (candidate_id,),
            )

        return True

    def reject_candidate(self, candidate_id: int) -> bool:
        """拒绝候选内容."""
        with self.repo.db.connect() as conn:
            cursor = conn.execute(
                "UPDATE import_candidates SET status='rejected' WHERE id=?",
                (candidate_id,),
            )
            return cursor.rowcount > 0

    def get_import_stats(self) -> dict:
        """获取导入统计."""
        with self.repo.db.connect() as conn:
            exchanges = conn.execute("SELECT COUNT(*) as c FROM captured_exchanges").fetchone()["c"]
            candidates = conn.execute("SELECT COUNT(*) as c FROM import_candidates").fetchone()["c"]
            pending = conn.execute("SELECT COUNT(*) as c FROM import_candidates WHERE status='pending'").fetchone()["c"]
            confirmed = conn.execute("SELECT COUNT(*) as c FROM import_candidates WHERE status='confirmed'").fetchone()["c"]

            batches = conn.execute(
                "SELECT import_batch, COUNT(*) as c FROM captured_exchanges GROUP BY import_batch ORDER BY MAX(collected_at) DESC LIMIT 10"
            ).fetchall()

            return {
                "total_exchanges": exchanges,
                "total_candidates": candidates,
                "pending": pending,
                "confirmed": confirmed,
                "batches": [{"name": r["import_batch"], "count": r["c"]} for r in batches],
            }
