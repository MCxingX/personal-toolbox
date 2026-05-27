from __future__ import annotations

import json
from datetime import date, datetime


DAILY_QUOTES = [
    {"content": "你已经在认真生活了，今天也可以轻一点。", "author": "", "style": "encourage"},
    {"content": "不必事事完美，能走到这里已经很好了。", "author": "", "style": "comfort"},
    {"content": "今天也是元气满满的一天！", "author": "", "style": "happy"},
    {"content": "代码写不出来的时候，先去喝杯水。", "author": "", "style": "tech"},
    {"content": "人生苦短，我用 Python。", "author": "Tim Peters", "style": "tech"},
    {"content": "Talk is cheap. Show me the code.", "author": "Linus Torvalds", "style": "tech"},
    {"content": "每一个不曾起舞的日子，都是对生命的辜负。", "author": "尼采", "style": "philosophy"},
    {"content": "生活不止眼前的苟且，还有诗和远方。", "author": "高晓松", "style": "encourage"},
    {"content": "今天解决不了的，明天也不一定能解决，但至少今天先休息。", "author": "", "style": "humor"},
    {"content": "不要因为走得太远，而忘记为什么出发。", "author": "", "style": "philosophy"},
    {"content": "先完成，再完美。", "author": "", "style": "encourage"},
    {"content": "没有 bug 的代码是不存在的，包括这段话。", "author": "", "style": "humor"},
    {"content": "坚持不一定成功，但放弃一定很轻松。", "author": "", "style": "humor"},
    {"content": "真正的平静，不是避开车马喧嚣，而是在心中修篱种菊。", "author": "", "style": "calm"},
    {"content": "种一棵树最好的时间是十年前，其次是现在。", "author": "", "style": "encourage"},
]

STYLE_LABELS = {
    "happy": "开心一点",
    "comfort": "别委屈",
    "encourage": "加油鼓励",
    "calm": "冷静理性",
    "humor": "幽默段子",
    "tech": "技术人专属",
    "philosophy": "哲理",
}


class DailyQuoteService:
    def __init__(self, repo):
        self.repo = repo

    def seed_quotes(self) -> None:
        with self.repo.db.connect() as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM daily_quotes").fetchone()["c"]
            if count == 0:
                for q in DAILY_QUOTES:
                    conn.execute(
                        "INSERT INTO daily_quotes(content, author, source, style) VALUES(?,?,?,?)",
                        (q["content"], q.get("author", ""), "local", q.get("style", "encourage")),
                    )

    def get_quote(self, style: str | None = None) -> dict:
        with self.repo.db.connect() as conn:
            if style:
                row = conn.execute("SELECT * FROM daily_quotes WHERE style = ? ORDER BY RANDOM() LIMIT 1", (style,)).fetchone()
            else:
                row = conn.execute("SELECT * FROM daily_quotes ORDER BY RANDOM() LIMIT 1").fetchone()
            if row:
                return dict(row)
        return {"content": "今天也要加油哦！", "author": "", "style": "encourage", "source": "fallback"}

    def get_home_quote(self) -> dict:
        q = self.get_quote()
        q["style_label"] = STYLE_LABELS.get(q.get("style", ""), "每日语录")
        return q

    def list_styles(self) -> list[dict]:
        return [{"key": k, "label": v} for k, v in STYLE_LABELS.items()]

    def add_quote(self, content: str, author: str = "", style: str = "encourage") -> int:
        with self.repo.db.connect() as conn:
            conn.execute("INSERT INTO daily_quotes(content, author, source, style) VALUES(?,?,?,?)", (content, author, "user", style))
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
