from __future__ import annotations


DAILY_QUOTES = [
    {"content": "费曼学习法：能用自己的话讲清楚，才是真懂。", "author": "Richard Feynman", "style": "learning", "lesson": "学习新知识时，先尝试向一个外行解释。", "action": "选一条今天看到的新闻，用 3 句话讲给自己听。"},
    {"content": "复利来自长期坚持的小改进。", "author": "", "style": "learning", "lesson": "每天进步 1%，长期会形成明显差距。", "action": "今天把一个重复动作优化 1 分钟。"},
    {"content": "先定义问题，再寻找答案。", "author": "", "style": "thinking", "lesson": "很多低效来自解错问题。", "action": "把当前最烦的事改写成一个可执行问题。"},
    {"content": "二八法则：少数关键动作决定大部分结果。", "author": "Vilfredo Pareto", "style": "thinking", "lesson": "优先找高影响事项。", "action": "列 3 件事，圈出最能推动结果的 1 件。"},
    {"content": "沉没成本不该参与今天的判断。", "author": "", "style": "decision", "lesson": "已经付出的成本无法收回，继续投入要看未来收益。", "action": "检查一个拖延项目：继续做的理由是否仍然成立。"},
    {"content": "机会成本是选择背后的真实价格。", "author": "", "style": "decision", "lesson": "选择 A 同时意味着放弃 B。", "action": "今天做决定前写下你放弃了什么。"},
    {"content": "表达前先确认对方要答案、共情，还是建议。", "author": "", "style": "communication", "lesson": "沟通失败常来自回应类型错位。", "action": "回复别人前先问一句：你想听建议还是先吐槽？"},
    {"content": "具体反馈比笼统夸奖更有价值。", "author": "", "style": "communication", "lesson": "反馈指向具体行为，别人才能复用。", "action": "今天夸人时指出一个具体细节。"},
    {"content": "番茄钟的核心是降低启动阻力。", "author": "Francesco Cirillo", "style": "productivity", "lesson": "25 分钟只是工具，真正目标是进入状态。", "action": "开一个 15 分钟小番茄，只处理一个任务。"},
    {"content": "任务拆小之后，大脑更愿意开始。", "author": "", "style": "productivity", "lesson": "模糊任务会增加心理阻力。", "action": "把一个大任务拆成第一步动作。"},
    {"content": "确认偏误会让人只看见支持自己的证据。", "author": "", "style": "cognitive", "lesson": "重要判断要主动寻找反例。", "action": "给自己的一个观点找 1 条反方证据。"},
    {"content": "可得性偏差会放大刚看到的信息。", "author": "", "style": "cognitive", "lesson": "热搜很近，真相可能很远。", "action": "看到热点时，先查一个原始来源。"},
    {"content": "优秀的提问会缩短一半沟通成本。", "author": "", "style": "learning", "lesson": "好问题包含背景、目标、尝试过的方法。", "action": "今天提问时带上：我想要、我试过、卡在。"},
    {"content": "阅读新闻时区分事实、观点、推测。", "author": "", "style": "media", "lesson": "事实可核验，观点需辨别立场，推测需要等待证据。", "action": "打开一篇新闻，标出一句事实和一句观点。"},
    {"content": "安全感的一部分来自可预期的流程。", "author": "", "style": "life", "lesson": "稳定流程能降低日常焦虑。", "action": "给明早安排一个固定开始动作。"},
    {"content": "复盘只问三件事：发生了什么、为什么、下次怎么做。", "author": "", "style": "productivity", "lesson": "复盘面向改进，而非自责。", "action": "用 3 行写完今天一次小复盘。"},
    {"content": "延迟满足的关键是把奖励放在进度之后。", "author": "", "style": "life", "lesson": "即时反馈能帮助长期坚持。", "action": "完成一个小任务后再刷 10 分钟信息流。"},
    {"content": "系统比目标更稳定。", "author": "James Clear", "style": "productivity", "lesson": "目标定义方向，系统决定重复发生的行为。", "action": "为一个目标设置固定触发时间。"},
    {"content": "检索式学习比重复阅读更能巩固记忆。", "author": "", "style": "learning", "lesson": "主动回忆会迫使大脑重建知识。", "action": "读完一段内容后合上页面，写出 3 个关键词。"},
    {"content": "间隔重复适合长期记忆。", "author": "", "style": "learning", "lesson": "把复习分散到不同时间，比集中刷一遍更稳。", "action": "把今天学到的一点安排到明天再看一次。"},
    {"content": "用例子校验理解。", "author": "", "style": "learning", "lesson": "抽象概念需要具体案例落地。", "action": "给今天看到的一个概念补一个生活例子。"},
    {"content": "第一性原理是拆到不可再拆的事实。", "author": "", "style": "thinking", "lesson": "很多判断混入了习惯、类比和情绪。", "action": "把一个结论拆成事实、假设、推论三列。"},
    {"content": "奥卡姆剃刀：优先选择更少假设的解释。", "author": "William of Ockham", "style": "thinking", "lesson": "复杂解释容易藏住未经验证的前提。", "action": "给一个问题写两个解释，选择假设更少的那个先验证。"},
    {"content": "逆向思考：先问怎样会失败。", "author": "", "style": "thinking", "lesson": "提前识别失败路径能降低决策风险。", "action": "给当前计划列 3 个最可能失败的原因。"},
    {"content": "可逆决定要快，不可逆决定要慢。", "author": "", "style": "decision", "lesson": "决策速度应匹配试错成本。", "action": "把今天的一个决定标记为可逆或不可逆。"},
    {"content": "满意解常常优于完美解。", "author": "Herbert Simon", "style": "decision", "lesson": "多数日常选择追求足够好会更高效。", "action": "给一个选择设定最低可接受标准。"},
    {"content": "预设退出条件能减少纠缠。", "author": "", "style": "decision", "lesson": "先定义停止信号，能避免情绪性加码。", "action": "给一个尝试写下：什么情况就停止。"},
    {"content": "复述对方观点，是沟通的降噪器。", "author": "", "style": "communication", "lesson": "先确认理解，再表达立场。", "action": "下一次争论前先说：我的理解是……对吗？"},
    {"content": "请求要包含背景、动作和截止时间。", "author": "", "style": "communication", "lesson": "清晰请求能减少来回沟通。", "action": "把一个请求改成：因为……请你……在……前。"},
    {"content": "难沟通先写草稿，情绪会被结构稀释。", "author": "", "style": "communication", "lesson": "书面化能让表达更稳定。", "action": "发重要消息前先写 3 行草稿。"},
    {"content": "两分钟规则能处理启动困难。", "author": "David Allen", "style": "productivity", "lesson": "能两分钟完成的事，立即处理能减少心理负担。", "action": "现在完成一件两分钟小事。"},
    {"content": "批处理能减少切换成本。", "author": "", "style": "productivity", "lesson": "同类任务集中处理比穿插处理更省力。", "action": "把今天 3 个零碎任务合并到一个时间段。"},
    {"content": "默认选项塑造行为。", "author": "", "style": "productivity", "lesson": "环境设置比意志力更可靠。", "action": "把一个干扰源移出默认视线。"},
    {"content": "幸存者偏差会让成功故事看起来太简单。", "author": "", "style": "cognitive", "lesson": "你看到的样本可能已经被筛选过。", "action": "看到成功经验时，问一句失败样本在哪里。"},
    {"content": "锚定效应会影响后续估计。", "author": "", "style": "cognitive", "lesson": "第一个数字或说法会悄悄变成参照物。", "action": "做估算前先独立写一个范围。"},
    {"content": "损失厌恶会放大失去的痛感。", "author": "", "style": "cognitive", "lesson": "人们对损失更敏感，容易因此保守。", "action": "判断一件事时分开写收益和损失。"},
    {"content": "信息源越单一，判断越脆弱。", "author": "", "style": "media", "lesson": "同一信息最好有不同立场来源交叉验证。", "action": "给一条重要新闻找第二来源。"},
    {"content": "标题负责吸引点击，正文负责提供证据。", "author": "", "style": "media", "lesson": "只看标题容易被情绪牵引。", "action": "看到强刺激标题时，先读原文第一段。"},
    {"content": "区分报道、评论和广告。", "author": "", "style": "media", "lesson": "不同文本类型的可信标准不同。", "action": "打开一篇文章，判断它主要是哪一种类型。"},
    {"content": "睡前降低输入强度，第二天更容易启动。", "author": "", "style": "life", "lesson": "高刺激信息会挤压恢复质量。", "action": "睡前 20 分钟只做低刺激整理。"},
    {"content": "稳定生活靠固定锚点。", "author": "", "style": "life", "lesson": "固定动作能让一天有可预期的起点。", "action": "给明天早上设置一个 5 分钟固定动作。"},
    {"content": "关系维护靠小而稳定的回应。", "author": "", "style": "life", "lesson": "低成本高频反馈比偶尔大动作更稳。", "action": "给一个重要的人发一句具体关心。"},
]

STYLE_LABELS = {
    "learning": "学习方法",
    "thinking": "思维模型",
    "decision": "决策能力",
    "communication": "沟通表达",
    "productivity": "效率工具",
    "cognitive": "认知偏差",
    "media": "信息素养",
    "life": "生活策略",
}


class DailyQuoteService:
    def __init__(self, repo):
        self.repo = repo

    def seed_quotes(self) -> None:
        with self.repo.db.connect() as conn:
            # 迁移旧版风格到 8 个核心风格
            style_migration = {
                "literature": "thinking",
                "emotion": "life",
                "poem": "thinking",
                "humor": "life",
                "philosophy": "thinking",
                "inspire": "thinking",
                "romance": "life",
                "play": "life",
                "funfact": "cognitive",
                "calm": "life",
            }
            for old_style, new_style in style_migration.items():
                conn.execute("UPDATE daily_quotes SET style=? WHERE style=?", (new_style, old_style))
            
            for q in DAILY_QUOTES:
                row = conn.execute("SELECT id FROM daily_quotes WHERE content=?", (q["content"],)).fetchone()
                values = (q.get("author", ""), q.get("style", "learning"), q.get("lesson", ""), q.get("action", ""), q["content"])
                if row:
                    conn.execute("UPDATE daily_quotes SET author=?, style=?, lesson=?, action=? WHERE content=?", values)
                else:
                    conn.execute(
                        "INSERT INTO daily_quotes(content, author, source, style, lesson, action) VALUES(?,?,?,?,?,?)",
                        (q["content"], q.get("author", ""), "local", q.get("style", "learning"), q.get("lesson", ""), q.get("action", "")),
                    )

    def get_quote(self, style: str | None = None) -> dict:
        with self.repo.db.connect() as conn:
            if style:
                row = conn.execute(
                    """SELECT * FROM daily_quotes WHERE style = ? AND (lesson <> '' OR action <> '')
                    ORDER BY shown_count ASC, RANDOM() LIMIT 1""",
                    (style,),
                ).fetchone()
            else:
                row = conn.execute(
                    """SELECT * FROM daily_quotes WHERE lesson <> '' OR action <> ''
                    ORDER BY shown_count ASC, RANDOM() LIMIT 1"""
                ).fetchone()
            if row:
                q = dict(row)
                conn.execute(
                    "UPDATE daily_quotes SET shown_count=shown_count+1, last_shown_at=CURRENT_TIMESTAMP WHERE id=?",
                    (q["id"],),
                )
                return q
        return {"content": "先定义问题，再寻找答案。", "author": "", "style": "thinking", "source": "fallback", "lesson": "问题定义决定解决效率。", "action": "把当前问题写成一句话。"}

    def get_home_quote(self) -> dict:
        q = self.get_quote()
        q["style_label"] = STYLE_LABELS.get(q.get("style", ""), "学习卡片")
        return q

    def list_styles(self) -> list[dict]:
        with self.repo.db.connect() as conn:
            rows = conn.execute(
                """SELECT style, COUNT(*) AS c FROM daily_quotes
                WHERE lesson <> '' OR action <> '' GROUP BY style"""
            ).fetchall()
        counts = {row["style"]: row["c"] for row in rows}
        return [{"key": k, "label": v, "count": counts.get(k, 0)} for k, v in STYLE_LABELS.items()]

    def add_quote(self, content: str, author: str = "", style: str = "learning", lesson: str = "", action: str = "") -> int:
        with self.repo.db.connect() as conn:
            conn.execute(
                "INSERT INTO daily_quotes(content, author, source, style, lesson, action) VALUES(?,?,?,?,?,?)",
                (content, author, "user", style, lesson, action),
            )
            return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
