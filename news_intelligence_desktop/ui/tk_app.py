"""Tkinter GUI - Windows 兼容版本，不需要安装 PySide6."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.services.app_service import AppService


class App(tk.Tk):
    """主应用窗口."""

    def __init__(self, app_service: AppService):
        super().__init__()
        self.app = app_service
        self.title("News Intelligence Desktop - 个人每日信息中枢")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        # 配色
        self.bg_color = "#f5f5f5"
        self.sidebar_color = "#2c3e50"
        self.btn_color = "#3498db"
        self.btn_hover = "#2980b9"
        self.accent_color = "#27ae60"
        self.text_color = "#2c3e50"

        self.configure(bg=self.bg_color)

        self._create_sidebar()
        self._create_content_area()
        self._create_statusbar()

        # 默认显示首页
        self._show_home()

    def _create_sidebar(self):
        """创建左侧导航栏."""
        sidebar = tk.Frame(self, bg=self.sidebar_color, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # 标题
        tk.Label(
            sidebar, text="News Intelligence",
            bg=self.sidebar_color, fg="white",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(pady=(20, 5))

        tk.Label(
            sidebar, text="个人每日信息中枢",
            bg=self.sidebar_color, fg="#bdc3c7",
            font=("Microsoft YaHei", 9)
        ).pack(pady=(0, 20))

        # 导航按钮
        buttons = [
            ("首页总览", self._show_home),
            ("天气预报", self._show_weather),
            ("地震动态", self._show_earthquake),
            ("新闻资讯", self._show_news),
            ("每日语录", self._show_quote),
            ("技术变化", self._show_tech),
            ("API 工具箱", self._show_toolbox),
            ("搜索", self._show_search),
            ("个人中心", self._show_personal),
            ("来源管理", self._show_sources),
        ]

        for text, cmd in buttons:
            btn = tk.Button(
                sidebar, text=text, command=cmd,
                bg=self.sidebar_color, fg="white",
                activebackground="#34495e", activeforeground="white",
                relief=tk.FLAT, anchor=tk.W, padx=20, pady=8,
                font=("Microsoft YaHei", 10), cursor="hand2"
            )
            btn.pack(fill=tk.X, padx=10, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#34495e"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.sidebar_color))

        # 一键采集按钮
        tk.Frame(sidebar, bg=self.sidebar_color, height=20).pack()
        self.collect_btn = tk.Button(
            sidebar, text="一键采集数据", command=self._start_collect,
            bg=self.accent_color, fg="white",
            activebackground="#229954", activeforeground="white",
            relief=tk.FLAT, padx=20, pady=12,
            font=("Microsoft YaHei", 11, "bold"), cursor="hand2"
        )
        self.collect_btn.pack(fill=tk.X, padx=10, pady=10)
        self.collect_btn.bind("<Enter>", lambda e: self.collect_btn.configure(bg="#229954"))
        self.collect_btn.bind("<Leave>", lambda e: self.collect_btn.configure(bg=self.accent_color))

    def _create_content_area(self):
        """创建右侧内容区域."""
        self.content = tk.Frame(self, bg=self.bg_color)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_statusbar(self):
        """创建底部状态栏."""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            bg="#ecf0f1", fg="#7f8c8d", anchor=tk.W, padx=10, pady=5,
            font=("Microsoft YaHei", 9)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _clear_content(self):
        """清空内容区域."""
        for widget in self.content.winfo_children():
            widget.destroy()

    def _set_status(self, text: str):
        """设置状态栏文字."""
        self.status_var.set(text)

    # ========== 首页 ==========

    def _show_home(self):
        self._clear_content()
        self._set_status("首页总览")

        # 标题
        tk.Label(
            self.content, text="个人每日信息中枢",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 滚动区域
        canvas = tk.Canvas(self.content, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.bg_color)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 获取数据
        dash = self.app.home_dashboard()

        # 卡片网格
        row, col = 0, 0
        for card in dash.get("cards", []):
            frame = tk.LabelFrame(
                scroll_frame, text=card["name"],
                bg="white", fg=self.text_color,
                font=("Microsoft YaHei", 11, "bold"),
                relief=tk.GROOVE, padx=15, pady=10
            )
            frame.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)

            # 摘要
            tk.Label(
                frame, text=card.get("summary", ""),
                bg="white", fg="#666", wraplength=350, justify=tk.LEFT,
                font=("Microsoft YaHei", 9)
            ).pack(anchor=tk.W)

            # 条目
            for item in card.get("items", [])[:3]:
                tk.Label(
                    frame, text=f"  {item['title']}",
                    bg="white", fg=self.text_color, wraplength=350, justify=tk.LEFT,
                    font=("Microsoft YaHei", 9)
                ).pack(anchor=tk.W, pady=2)

            # 语录
            if card.get("quote"):
                q = card["quote"]
                tk.Label(
                    frame, text=f"{q.get('style_label', '')}: {q['content']}",
                    bg="white", fg=self.accent_color, wraplength=350, justify=tk.LEFT,
                    font=("Microsoft YaHei", 9, "italic")
                ).pack(anchor=tk.W, pady=5)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.columnconfigure(1, weight=1)

        # 刷新按钮
        btn_frame = tk.Frame(self.content, bg=self.bg_color)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="刷新首页", command=self._show_home,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack()

    # ========== 天气 ==========

    def _show_weather(self):
        self._clear_content()
        self._set_status("天气预报")

        tk.Label(
            self.content, text="天气预报",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 表格
        columns = ("日期", "高温", "低温", "天气")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 加载数据
        with self.app.repo.db.connect() as conn:
            forecasts = [dict(r) for r in conn.execute("SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7")]
        for f in forecasts:
            tree.insert("", tk.END, values=(
                f.get("forecast_date", ""),
                f"{f.get('temp_high', '--')}°C",
                f"{f.get('temp_low', '--')}°C",
                f.get("description", "")
            ))

        tk.Button(
            self.content, text="刷新天气", command=self._show_weather,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(pady=10)

    # ========== 地震 ==========

    def _show_earthquake(self):
        self._clear_content()
        self._set_status("地震动态")

        tk.Label(
            self.content, text="地震动态",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        columns = ("震级", "位置", "时间", "来源")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        with self.app.repo.db.connect() as conn:
            events = [dict(r) for r in conn.execute("SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 20")]
        for e in events:
            tree.insert("", tk.END, values=(
                f"M{e.get('magnitude', 0)}",
                e.get("place", ""),
                e.get("event_time", "")[:16],
                e.get("source", "")
            ))

        tk.Button(
            self.content, text="刷新地震数据", command=self._show_earthquake,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(pady=10)

    # ========== 新闻 ==========

    def _show_news(self):
        self._clear_content()
        self._set_status("新闻资讯")

        tk.Label(
            self.content, text="新闻资讯",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 筛选
        filter_frame = tk.Frame(self.content, bg=self.bg_color)
        filter_frame.pack(fill=tk.X, padx=20)

        tk.Label(filter_frame, text="分类:", bg=self.bg_color, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.news_category = tk.StringVar(value="全部")
        combo = ttk.Combobox(filter_frame, textvariable=self.news_category, values=["全部", "新闻", "技术", "政策", "热点", "本地"], state="readonly", width=10)
        combo.pack(side=tk.LEFT, padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_news())

        # 表格
        columns = ("ID", "标题", "来源", "分类", "时间")
        self.news_tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            self.news_tree.heading(col, text=col)
            w = 50 if col == "ID" else 300 if col == "标题" else 100
            self.news_tree.column(col, width=w, anchor=tk.CENTER)
        self.news_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.news_tree.bind("<Double-1>", self._show_article_detail)

        self._refresh_news()

        btn_frame = tk.Frame(self.content, bg=self.bg_color)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="刷新列表", command=self._refresh_news,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="查看详情", command=lambda: self._show_article_detail(None),
            bg=self.accent_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

    def _refresh_news(self):
        for item in self.news_tree.get_children():
            self.news_tree.delete(item)
        cat_map = {"全部": None, "新闻": "news", "技术": "tech", "政策": "policy", "热点": "hot", "本地": "local"}
        cat = cat_map.get(self.news_category.get())
        articles = self.app.repo.list_articles(category=cat, limit=50)
        for a in articles:
            self.news_tree.insert("", tk.END, values=(
                a.get("id", ""), a.get("title", ""), a.get("source_name", ""),
                a.get("category", ""), a.get("collected_at", "")[:16]
            ))

    def _show_article_detail(self, event):
        selection = self.news_tree.selection()
        if not selection:
            return
        item = self.news_tree.item(selection[0])
        aid = int(item["values"][0])
        article = self.app.repo.get_article(aid)
        if not article:
            return

        # 弹窗显示详情
        detail = tk.Toplevel(self)
        detail.title(article.get("title", "文章详情"))
        detail.geometry("600x400")

        text = scrolledtext.ScrolledText(detail, wrap=tk.WORD, font=("Microsoft YaHei", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content = f"标题: {article.get('title', '')}\n\n"
        content += f"来源: {article.get('source_name', '')}\n"
        content += f"分类: {article.get('category', '')}\n"
        content += f"链接: {article.get('url', '')}\n"
        content += f"采集时间: {article.get('collected_at', '')}\n\n"
        content += f"摘要:\n{article.get('summary', '无')}\n\n"
        if article.get("content"):
            content += f"内容:\n{article['content'][:1000]}"

        text.insert(tk.END, content)
        text.configure(state=tk.DISABLED)

        # 操作按钮
        btn_frame = tk.Frame(detail)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="收藏", command=lambda: self._mark_article(aid, "favorite", detail),
                  bg="#f39c12", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="标记已读", command=lambda: self._mark_article(aid, "read", detail),
                  bg="#27ae60", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)

    def _mark_article(self, aid, state, window=None):
        self.app.personal.set_reading_state("article", aid, state)
        self._set_status(f"已标记文章 {aid} 为 {state}")
        if window:
            window.destroy()

    # ========== 语录 ==========

    def _show_quote(self):
        self._clear_content()
        self._set_status("每日语录")

        tk.Label(
            self.content, text="每日语录",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 语录显示框
        quote_frame = tk.Frame(self.content, bg="white", relief=tk.GROOVE, padx=30, pady=30)
        quote_frame.pack(pady=20, padx=50, fill=tk.X)

        self.quote_label = tk.Label(
            quote_frame, text="", bg="white", fg=self.text_color,
            font=("Microsoft YaHei", 14), wraplength=500, justify=tk.CENTER
        )
        self.quote_label.pack()

        self.author_label = tk.Label(
            quote_frame, text="", bg="white", fg="#999",
            font=("Microsoft YaHei", 10)
        )
        self.author_label.pack(pady=(10, 0))

        # 风格选择
        style_frame = tk.Frame(self.content, bg=self.bg_color)
        style_frame.pack(pady=20)

        tk.Label(style_frame, text="选择风格:", bg=self.bg_color, font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        self.quote_style = tk.StringVar(value="随机")
        ttk.Combobox(
            style_frame, textvariable=self.quote_style,
            values=["随机", "开心一点", "别委屈", "加油鼓励", "冷静理性", "幽默段子", "技术人专属", "哲理"],
            state="readonly", width=12
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            style_frame, text="换一条", command=self._refresh_quote,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT)

        self._refresh_quote()

    def _refresh_quote(self):
        style_map = {"随机": None, "开心一点": "happy", "别委屈": "comfort", "加油鼓励": "encourage",
                    "冷静理性": "calm", "幽默段子": "humor", "技术人专属": "tech", "哲理": "philosophy"}
        style = style_map.get(self.quote_style.get())
        q = self.app.quote_service.get_quote(style)
        self.quote_label.configure(text=f"\u300c{q.get('content', '')}\u300d")
        author = q.get("author", "")
        self.author_label.configure(text=f"\u2014\u2014 {author}" if author else "")

    # ========== 技术变化 ==========

    def _show_tech(self):
        self._clear_content()
        self._set_status("技术变化")

        tk.Label(
            self.content, text="技术变化追踪",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        columns = ("类型", "标题", "来源", "时间")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        changes = self.app.tech_service.list_changes(limit=30)
        for c in changes:
            tree.insert("", tk.END, values=(
                c.get("change_type", ""), c.get("title", ""),
                c.get("source_name", ""), c.get("published_at", "")[:16]
            ))

        btn_frame = tk.Frame(self.content, bg=self.bg_color)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="检测技术变化", command=lambda: self._detect_tech(tree),
            bg=self.accent_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="刷新列表", command=self._show_tech,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

    def _detect_tech(self, tree):
        count = self.app.tech_service.detect_and_store()
        messagebox.showinfo("检测完成", f"检测到 {count} 个技术变化")
        self._show_tech()

    # ========== API 工具箱 ==========

    def _show_toolbox(self):
        self._clear_content()
        self._set_status("API 工具箱")

        tk.Label(
            self.content, text="API 工具箱",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        columns = ("ID", "名称", "提供商", "分类", "状态")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        apis = self.app.api_service.list_apis()
        for a in apis:
            tree.insert("", tk.END, values=(
                a.get("id", ""), a.get("name", ""), a.get("provider", ""),
                a.get("category", ""), a.get("status", "")
            ))

        tk.Label(
            self.content, text=f"共 {len(apis)} 个 API",
            bg=self.bg_color, fg="#666", font=("Microsoft YaHei", 9)
        ).pack()

    # ========== 搜索 ==========

    def _show_search(self):
        self._clear_content()
        self._set_status("搜索")

        tk.Label(
            self.content, text="搜索",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 搜索框
        search_frame = tk.Frame(self.content, bg=self.bg_color)
        search_frame.pack(fill=tk.X, padx=20)

        self.search_entry = tk.Entry(search_frame, font=("Microsoft YaHei", 11), width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        tk.Button(
            search_frame, text="搜索", command=self._do_search,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(side=tk.LEFT)

        # 结果
        columns = ("类型", "标题", "摘要")
        self.search_tree = ttk.Treeview(self.content, columns=columns, show="headings", height=12)
        for col in columns:
            self.search_tree.heading(col, text=col)
            w = 80 if col == "类型" else 250 if col == "标题" else 400
            self.search_tree.column(col, width=w, anchor=tk.CENTER)
        self.search_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Button(
            self.content, text="重建搜索索引", command=self._rebuild_index,
            bg="#f39c12", fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(pady=10)

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        results = self.app.search(query)
        for r in results:
            self.search_tree.insert("", tk.END, values=(
                r.get("item_type", ""), r.get("title", ""), r.get("snippet", "")[:80]
            ))
        self._set_status(f"搜索完成: {len(results)} 条结果")

    def _rebuild_index(self):
        count = self.app.search_service.rebuild_index()
        messagebox.showinfo("重建完成", f"已重建 {count} 条索引")

    # ========== 个人中心 ==========

    def _show_personal(self):
        self._clear_content()
        self._set_status("个人中心")

        tk.Label(
            self.content, text="个人中心",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        # 统计
        favorites = self.app.personal.list_collection("favorite")
        read_later = self.app.personal.list_collection("read_later")
        watchlist = self.app.personal.list_watchlist()

        stats_frame = tk.Frame(self.content, bg=self.bg_color)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        for text, count in [("收藏", len(favorites)), ("稍后看", len(read_later)), ("关注", len(watchlist))]:
            frame = tk.Frame(stats_frame, bg="white", relief=tk.GROOVE, padx=20, pady=10)
            frame.pack(side=tk.LEFT, padx=10)
            tk.Label(frame, text=text, bg="white", font=("Microsoft YaHei", 10)).pack()
            tk.Label(frame, text=str(count), bg="white", fg=self.btn_color, font=("Microsoft YaHei", 16, "bold")).pack()

        # 隐私模式
        self.privacy_var = tk.BooleanVar(value=self.app.personal.privacy_enabled())
        tk.Checkbutton(
            self.content, text="隐私模式", variable=self.privacy_var,
            command=self._toggle_privacy, bg=self.bg_color, font=("Microsoft YaHei", 10)
        ).pack(anchor=tk.W, padx=20, pady=10)

        # 收藏列表
        tk.Label(self.content, text="最近收藏:", bg=self.bg_color, font=("Microsoft YaHei", 11, "bold")).pack(anchor=tk.W, padx=20)

        columns = ("ID", "标题", "来源")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100 if col == "ID" else 300 if col == "标题" else 150, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for a in favorites[:20]:
            tree.insert("", tk.END, values=(a.get("id", ""), a.get("title", ""), a.get("source_name", "")))

        tk.Button(
            self.content, text="刷新", command=self._show_personal,
            bg=self.btn_color, fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("Microsoft YaHei", 10), cursor="hand2"
        ).pack(pady=10)

    def _toggle_privacy(self):
        enabled = self.privacy_var.get()
        self.app.personal.set_privacy_mode(enabled)
        self._set_status(f"隐私模式已{'开启' if enabled else '关闭'}")

    # ========== 来源管理 ==========

    def _show_sources(self):
        self._clear_content()
        self._set_status("来源管理")

        tk.Label(
            self.content, text="来源管理",
            bg=self.bg_color, fg=self.text_color,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20, anchor=tk.W, padx=20)

        columns = ("ID", "名称", "类型", "分类", "状态")
        tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        sources = self.app.source_mgr.list_sources()
        health = self.app.source_health.get_health()
        health_map = {h["id"]: h for h in health}

        for s in sources:
            h = health_map.get(s["id"], {})
            status = "正常" if s.get("enabled") else "禁用"
            if h.get("paused"):
                status = "已暂停"
            elif h.get("failure_count", 0) > 0:
                status = f"失败{h['failure_count']}次"
            tree.insert("", tk.END, values=(
                s.get("id", ""), s.get("name", ""), s.get("type", ""),
                s.get("category", ""), status
            ))

        tk.Label(
            self.content, text=f"共 {len(sources)} 个数据源",
            bg=self.bg_color, fg="#666", font=("Microsoft YaHei", 9)
        ).pack()

    # ========== 数据采集 ==========

    def _start_collect(self):
        self.collect_btn.configure(state=tk.DISABLED, text="采集中...")
        self._set_status("正在采集数据...")

        def do_collect():
            try:
                result = self.app.collect_all()
                self.after(0, lambda: self._on_collect_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_collect_error(str(e)))

        threading.Thread(target=do_collect, daemon=True).start()

    def _on_collect_done(self, result):
        self.collect_btn.configure(state=tk.NORMAL, text="一键采集数据")
        msg = f"采集完成: 天气{result.get('weather',0)} 地震{result.get('earthquake',0)} 新闻{result.get('news',0)} 热点{result.get('hot',0)} 技术{result.get('tech',0)}"
        self._set_status(msg)
        if result.get("errors"):
            messagebox.showwarning("采集警告", f"部分采集失败:\n" + "\n".join(result["errors"]))

    def _on_collect_error(self, error):
        self.collect_btn.configure(state=tk.NORMAL, text="一键采集数据")
        self._set_status("采集失败")
        messagebox.showerror("采集错误", error)


def run_gui(data_dir: Path | None = None) -> int:
    """启动图形界面."""
    settings = AppSettings.load(data_dir)
    app_service = AppService(settings)
    app_service.initialize()

    app = App(app_service)
    app.mainloop()
    return 0
