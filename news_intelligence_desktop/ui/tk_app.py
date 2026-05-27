"""Tkinter GUI - 完整版，符合国内使用习惯."""
from __future__ import annotations

import sys
import threading
import json
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.services.app_service import AppService


# 国内常用城市坐标
CITIES = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "南京": (32.0603, 118.7969),
    "重庆": (29.4316, 106.9123),
    "西安": (34.3416, 108.9398),
    "天津": (39.3434, 117.3616),
    "长沙": (28.2282, 112.9388),
    "郑州": (34.7466, 113.6253),
    "苏州": (31.2990, 120.5853),
    "厦门": (24.4798, 118.0894),
}

# 天气代码描述
WEATHER_CODES = {
    0: "晴", 1: "大部晴朗", 2: "局部多云", 3: "多云",
    45: "雾", 48: "雾凇", 51: "小毛毛雨", 53: "中毛毛雨",
    55: "大毛毛雨", 61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪", 80: "阵雨",
    81: "中阵雨", 82: "大阵雨", 95: "雷暴", 96: "雷暴+小冰雹",
    99: "雷暴+大冰雹",
}


class App(tk.Tk):
    """主应用窗口."""

    def __init__(self, app_service: AppService):
        super().__init__()
        self.app = app_service
        self.title("News Intelligence Desktop - 个人每日信息中枢")
        self.geometry("1280x860")
        self.minsize(1100, 700)

        # 配色方案 - 国内风格
        self.colors = {
            "bg": "#f0f2f5",
            "sidebar": "#1a1a2e",
            "sidebar_btn": "#16213e",
            "sidebar_hover": "#0f3460",
            "sidebar_active": "#e94560",
            "primary": "#1890ff",
            "primary_hover": "#096dd9",
            "success": "#52c41a",
            "warning": "#faad14",
            "danger": "#ff4d4f",
            "text": "#262626",
            "text_secondary": "#8c8c8c",
            "border": "#d9d9d9",
            "card_bg": "#ffffff",
            "tag_bg": "#f5f5f5",
        }

        self.configure(bg=self.colors["bg"])

        # 当前选中的城市
        self.current_city = tk.StringVar(value="北京")

        self._create_sidebar()
        self._create_content_area()
        self._create_statusbar()

        # 默认显示首页
        self._show_home()

    def _create_sidebar(self):
        """创建左侧导航栏."""
        sidebar = tk.Frame(self, bg=self.colors["sidebar"], width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo 区域
        logo_frame = tk.Frame(sidebar, bg=self.colors["sidebar"])
        logo_frame.pack(fill=tk.X, pady=(25, 20))

        tk.Label(
            logo_frame, text="资讯中枢",
            bg=self.colors["sidebar"], fg="white",
            font=("微软雅黑", 18, "bold")
        ).pack()

        tk.Label(
            logo_frame, text="News Intelligence",
            bg=self.colors["sidebar"], fg="#8c8c8c",
            font=("微软雅黑", 9)
        ).pack(pady=(2, 0))

        # 分隔线
        tk.Frame(sidebar, bg="#333", height=1).pack(fill=tk.X, padx=20, pady=10)

        # 导航按钮
        buttons = [
            ("首页总览", "home", self._show_home),
            ("天气预报", "weather", self._show_weather),
            ("地震动态", "earthquake", self._show_earthquake),
            ("新闻资讯", "news", self._show_news),
            ("每日语录", "quote", self._show_quote),
            ("技术变化", "tech", self._show_tech),
            ("API 工具箱", "api", self._show_toolbox),
            ("搜索", "search", self._show_search),
            ("个人中心", "user", self._show_personal),
            ("来源管理", "source", self._show_sources),
        ]

        self.nav_buttons = {}
        for text, key, cmd in buttons:
            btn = tk.Button(
                sidebar, text=f"  {text}", command=cmd,
                bg=self.colors["sidebar"], fg="#bfbfbf",
                activebackground=self.colors["sidebar_hover"],
                activeforeground="white",
                relief=tk.FLAT, anchor=tk.W, padx=25, pady=10,
                font=("微软雅黑", 11), cursor="hand2",
                bd=0
            )
            btn.pack(fill=tk.X, padx=8, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.colors["sidebar_hover"], fg="white"))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.configure(
                bg=self.colors["sidebar_active"] if k == self._current_page else self.colors["sidebar"],
                fg="white" if k == self._current_page else "#bfbfbf"
            ))
            self.nav_buttons[key] = btn

        self._current_page = "home"
        self.nav_buttons["home"].configure(bg=self.colors["sidebar_active"], fg="white")

        # 底部按钮
        tk.Frame(sidebar, bg=self.colors["sidebar"]).pack(fill=tk.BOTH, expand=True)

        # 一键采集按钮
        self.collect_btn = tk.Button(
            sidebar, text="一键采集数据", command=self._start_collect,
            bg=self.colors["success"], fg="white",
            activebackground="#389e0d", activeforeground="white",
            relief=tk.FLAT, padx=20, pady=14,
            font=("微软雅黑", 12, "bold"), cursor="hand2",
            bd=0
        )
        self.collect_btn.pack(fill=tk.X, padx=15, pady=15)
        self.collect_btn.bind("<Enter>", lambda e: self.collect_btn.configure(bg="#389e0d"))
        self.collect_btn.bind("<Leave>", lambda e: self.collect_btn.configure(bg=self.colors["success"]))

    def _switch_page(self, key: str):
        """切换页面并更新导航按钮样式."""
        # 重置所有按钮
        for k, btn in self.nav_buttons.items():
            btn.configure(bg=self.colors["sidebar"], fg="#bfbfbf")
        # 高亮当前按钮
        self.nav_buttons[key].configure(bg=self.colors["sidebar_active"], fg="white")
        self._current_page = key

    def _create_content_area(self):
        """创建右侧内容区域."""
        self.content = tk.Frame(self, bg=self.colors["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_statusbar(self):
        """创建底部状态栏."""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            bg="#fafafa", fg=self.colors["text_secondary"],
            anchor=tk.W, padx=15, pady=8,
            font=("微软雅黑", 9), relief=tk.FLAT
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _clear_content(self):
        """清空内容区域."""
        for widget in self.content.winfo_children():
            widget.destroy()

    def _set_status(self, text: str):
        """设置状态栏文字."""
        self.status_var.set(text)

    def _create_card(self, parent, title="", row=0, col=0, colspan=1):
        """创建卡片组件."""
        card = tk.LabelFrame(
            parent, text=f" {title} " if title else "",
            bg=self.colors["card_bg"], fg=self.colors["text"],
            font=("微软雅黑", 11, "bold"),
            relief=tk.FLAT, bd=1,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=15, pady=12
        )
        card.grid(row=row, column=col, columnspan=colspan, padx=8, pady=8, sticky=tk.NSEW)
        return card

    def _create_button(self, parent, text, command, style="primary"):
        """创建按钮."""
        color_map = {
            "primary": (self.colors["primary"], self.colors["primary_hover"]),
            "success": (self.colors["success"], "#389e0d"),
            "warning": (self.colors["warning"], "#d48806"),
            "danger": (self.colors["danger"], "#cf1322"),
            "default": ("#f5f5f5", "#e8e8e8"),
        }
        bg, hover_bg = color_map.get(style, color_map["primary"])
        fg = "white" if style != "default" else self.colors["text"]

        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
            relief=tk.FLAT, padx=15, pady=8,
            font=("微软雅黑", 10), cursor="hand2", bd=0
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    # ========== 首页 ==========

    def _show_home(self):
        self._clear_content()
        self._switch_page("home")
        self._set_status("首页总览")

        # 标题区域
        header = tk.Frame(self.content, bg=self.colors["primary"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="个人每日信息中枢",
            bg=self.colors["primary"], fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 内容区域
        main_frame = tk.Frame(self.content, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 获取数据
        dash = self.app.home_dashboard()

        # 卡片
        for i, card_data in enumerate(dash.get("cards", [])):
            row, col = divmod(i, 2)
            card = self._create_card(main_frame, card_data["name"], row, col)

            # 摘要
            tk.Label(
                card, text=card_data.get("summary", ""),
                bg=self.colors["card_bg"], fg=self.colors["text_secondary"],
                wraplength=400, justify=tk.LEFT, font=("微软雅黑", 9)
            ).pack(anchor=tk.W, pady=(0, 8))

            # 条目
            for item in card_data.get("items", [])[:3]:
                item_frame = tk.Frame(card, bg=self.colors["card_bg"])
                item_frame.pack(fill=tk.X, pady=2)
                tk.Label(
                    item_frame, text="•", bg=self.colors["card_bg"],
                    fg=self.colors["primary"], font=("微软雅黑", 10, "bold")
                ).pack(side=tk.LEFT, padx=(0, 5))
                tk.Label(
                    item_frame, text=item["title"][:50],
                    bg=self.colors["card_bg"], fg=self.colors["text"],
                    wraplength=380, justify=tk.LEFT, font=("微软雅黑", 9),
                    anchor=tk.W
                ).pack(side=tk.LEFT, fill=tk.X)

            # 语录
            if card_data.get("quote"):
                q = card_data["quote"]
                quote_text = f"{q.get('style_label', '')}: {q['content']}"
                tk.Label(
                    card, text=quote_text,
                    bg=self.colors["card_bg"], fg=self.colors["success"],
                    wraplength=400, justify=tk.LEFT, font=("微软雅黑", 9, "italic")
                ).pack(anchor=tk.W, pady=(8, 0))

    # ========== 天气预报 ==========

    def _show_weather(self):
        self._clear_content()
        self._switch_page("weather")
        self._set_status("天气预报")

        # 标题
        header = tk.Frame(self.content, bg="#1890ff", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="天气预报",
            bg="#1890ff", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 城市选择
        select_frame = tk.Frame(self.content, bg=self.colors["bg"])
        select_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            select_frame, text="选择城市:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT, padx=(0, 10))

        city_combo = ttk.Combobox(
            select_frame, textvariable=self.current_city,
            values=list(CITIES.keys()), state="readonly", width=15,
            font=("微软雅黑", 10)
        )
        city_combo.pack(side=tk.LEFT)
        city_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_weather())

        self._create_button(select_frame, "刷新天气", self._refresh_weather, "primary").pack(side=tk.LEFT, padx=15)

        # 天气卡片区域
        self.weather_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.weather_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._refresh_weather()

    def _refresh_weather(self):
        """刷新天气数据."""
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        city = self.current_city.get()
        lat, lon = CITIES.get(city, (39.9042, 116.4074))

        # 从数据库获取天气
        with self.app.repo.db.connect() as conn:
            forecasts = [dict(r) for r in conn.execute(
                "SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7"
            )]

        if not forecasts:
            tk.Label(
                self.weather_frame,
                text="暂无天气数据，请先点击「一键采集数据」",
                bg=self.colors["bg"], fg=self.colors["text_secondary"],
                font=("微软雅黑", 12)
            ).pack(pady=50)
            return

        # 显示天气卡片
        for i, f in enumerate(forecasts):
            card = tk.Frame(
                self.weather_frame, bg="white",
                relief=tk.FLAT, bd=1,
                highlightbackground=self.colors["border"],
                highlightthickness=1
            )
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # 日期
            date_text = f.get("forecast_date", "")[5:]  # MM-DD
            tk.Label(
                card, text=date_text, bg="white",
                fg=self.colors["text"], font=("微软雅黑", 11, "bold")
            ).pack(pady=(10, 5))

            # 天气图标（用文字代替）
            weather_code = f.get("weathercode", 0)
            weather_desc = WEATHER_CODES.get(weather_code, f"代码{weather_code}")
            tk.Label(
                card, text=weather_desc, bg="white",
                fg=self.colors["primary"], font=("微软雅黑", 14)
            ).pack(pady=5)

            # 温度
            temp_high = f.get("temp_high", "--")
            temp_low = f.get("temp_low", "--")
            tk.Label(
                card, text=f"{temp_high}°C", bg="white",
                fg=self.colors["danger"], font=("微软雅黑", 13, "bold")
            ).pack()
            tk.Label(
                card, text=f"{temp_low}°C", bg="white",
                fg=self.colors["primary"], font=("微软雅黑", 11)
            ).pack(pady=(0, 10))

            # 城市
            tk.Label(
                card, text=city, bg="white",
                fg=self.colors["text_secondary"], font=("微软雅黑", 9)
            ).pack(pady=(0, 10))

    # ========== 地震动态 ==========

    def _show_earthquake(self):
        self._clear_content()
        self._switch_page("earthquake")
        self._set_status("地震动态")

        # 标题
        header = tk.Frame(self.content, bg="#722ed1", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="地震动态",
            bg="#722ed1", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 筛选按钮
        filter_frame = tk.Frame(self.content, bg=self.colors["bg"])
        filter_frame.pack(fill=tk.X, padx=20, pady=15)

        self.earthquake_filter = tk.StringVar(value="all")

        for text, value in [("全部", "all"), ("国内", "china"), ("国外", "foreign")]:
            rb = tk.Radiobutton(
                filter_frame, text=text, variable=self.earthquake_filter,
                value=value, command=self._refresh_earthquake,
                bg=self.colors["bg"], fg=self.colors["text"],
                selectcolor=self.colors["primary"],
                font=("微软雅黑", 10), cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=10)

        self._create_button(filter_frame, "刷新", self._refresh_earthquake, "primary").pack(side=tk.LEFT, padx=15)

        # 表格
        table_frame = tk.Frame(self.content, bg=self.colors["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("震级", "位置", "深度(km)", "时间", "来源")
        self.eq_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        for col in columns:
            self.eq_tree.heading(col, text=col)
            w = 80 if col in ("震级", "深度(km)", "来源") else 250 if col == "位置" else 150
            self.eq_tree.column(col, width=w, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.eq_tree.yview)
        self.eq_tree.configure(yscrollcommand=scrollbar.set)
        self.eq_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_earthquake()

    def _refresh_earthquake(self):
        """刷新地震数据."""
        for item in self.eq_tree.get_children():
            self.eq_tree.delete(item)

        with self.app.repo.db.connect() as conn:
            events = [dict(r) for r in conn.execute(
                "SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 100"
            )]

        filter_val = self.earthquake_filter.get()
        filtered = []
        for e in events:
            place = e.get("place", "")
            is_china = any(kw in place for kw in ["China", "中国", "新疆", "西藏", "四川", "云南", "青海", "甘肃", "台湾"])
            if filter_val == "china" and not is_china:
                continue
            if filter_val == "foreign" and is_china:
                continue
            filtered.append(e)

        for e in filtered[:30]:
            mag = e.get("magnitude", 0)
            # 根据震级设置标签
            tag = "high" if mag >= 6 else "medium" if mag >= 5 else "low"

            self.eq_tree.insert("", tk.END, values=(
                f"M{mag}",
                e.get("place", ""),
                f"{e.get('depth_km', 0):.1f}",
                e.get("event_time", "")[:16],
                e.get("source", "")
            ), tags=(tag,))

        self.eq_tree.tag_configure("high", foreground="#ff4d4f")
        self.eq_tree.tag_configure("medium", foreground="#faad14")
        self.eq_tree.tag_configure("low", foreground="#52c41a")

    # ========== 新闻资讯 ==========

    def _show_news(self):
        self._clear_content()
        self._switch_page("news")
        self._set_status("新闻资讯")

        # 标题
        header = tk.Frame(self.content, bg="#13c2c2", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="新闻资讯",
            bg="#13c2c2", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 分类标签
        tag_frame = tk.Frame(self.content, bg=self.colors["bg"])
        tag_frame.pack(fill=tk.X, padx=20, pady=10)

        self.news_category = tk.StringVar(value="全部")
        categories = ["全部", "新闻", "技术", "政策", "热点", "本地", "事故", "猎奇"]

        for cat in categories:
            rb = tk.Radiobutton(
                tag_frame, text=cat, variable=self.news_category,
                value=cat, command=self._refresh_news,
                bg=self.colors["bg"], fg=self.colors["text"],
                selectcolor=self.colors["primary"],
                font=("微软雅黑", 10), cursor="hand2",
                indicatoron=0, padx=12, pady=5,
                relief=tk.FLAT, bd=0,
                activebackground=self.colors["primary"],
                activeforeground="white"
            )
            rb.pack(side=tk.LEFT, padx=3)

        # 新闻列表
        self.news_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.news_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 滚动条
        news_canvas = tk.Canvas(self.news_frame, bg=self.colors["bg"], highlightthickness=0)
        news_scrollbar = ttk.Scrollbar(self.news_frame, orient=tk.VERTICAL, command=news_canvas.yview)
        self.news_list_frame = tk.Frame(news_canvas, bg=self.colors["bg"])

        self.news_list_frame.bind("<Configure>", lambda e: news_canvas.configure(scrollregion=news_canvas.bbox("all")))
        news_canvas.create_window((0, 0), window=self.news_list_frame, anchor=tk.NW)
        news_canvas.configure(yscrollcommand=news_scrollbar.set)

        news_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        news_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            news_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        news_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._refresh_news()

    def _refresh_news(self):
        """刷新新闻列表."""
        for widget in self.news_list_frame.winfo_children():
            widget.destroy()

        cat_map = {
            "全部": None, "新闻": "news", "技术": "tech", "政策": "policy",
            "热点": "hot", "本地": "local", "事故": "accident", "猎奇": "oddity"
        }
        cat = cat_map.get(self.news_category.get())
        articles = self.app.repo.list_articles(category=cat, limit=30)

        if not articles:
            tk.Label(
                self.news_list_frame, text="暂无该分类的新闻，请先点击「一键采集数据」",
                bg=self.colors["bg"], fg=self.colors["text_secondary"],
                font=("微软雅黑", 11)
            ).pack(pady=50)
            return

        # 卡片式布局
        for i, a in enumerate(articles):
            card = tk.Frame(
                self.news_list_frame, bg="white",
                relief=tk.FLAT, bd=1,
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=15, pady=12
            )
            card.pack(fill=tk.X, pady=4)

            # 标题行
            title_frame = tk.Frame(card, bg="white")
            title_frame.pack(fill=tk.X)

            # 分类标签
            cat_colors = {
                "news": "#1890ff", "tech": "#722ed1", "policy": "#fa8c16",
                "hot": "#f5222d", "local": "#13c2c2", "accident": "#ff4d4f",
                "oddity": "#eb2f96", "quote": "#52c41a"
            }
            cat = a.get("category", "news")
            cat_label = tk.Label(
                title_frame, text=cat.upper(), bg=cat_colors.get(cat, "#999"),
                fg="white", font=("微软雅黑", 8, "bold"), padx=6, pady=2
            )
            cat_label.pack(side=tk.LEFT, padx=(0, 8))

            # 标题
            title_text = a.get("title", "")[:60]
            tk.Label(
                title_frame, text=title_text, bg="white",
                fg=self.colors["text"], font=("微软雅黑", 11, "bold"),
                anchor=tk.W
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 时间
            time_text = a.get("collected_at", "")[:16]
            tk.Label(
                title_frame, text=time_text, bg="white",
                fg=self.colors["text_secondary"], font=("微软雅黑", 9)
            ).pack(side=tk.RIGHT)

            # 摘要
            summary = a.get("summary", "")[:100]
            if summary:
                tk.Label(
                    card, text=summary, bg="white",
                    fg=self.colors["text_secondary"], font=("微软雅黑", 9),
                    wraplength=700, justify=tk.LEFT, anchor=tk.W
                ).pack(fill=tk.X, pady=(5, 0))

            # 底部信息
            bottom = tk.Frame(card, bg="white")
            bottom.pack(fill=tk.X, pady=(5, 0))

            tk.Label(
                bottom, text=f"来源: {a.get('source_name', '')}", bg="white",
                fg=self.colors["text_secondary"], font=("微软雅黑", 9)
            ).pack(side=tk.LEFT)

            # 操作按钮
            aid = a.get("id", 0)
            self._create_button(bottom, "收藏", lambda x=aid: self._quick_action(x, "favorite"), "default").pack(side=tk.RIGHT, padx=2)
            self._create_button(bottom, "已读", lambda x=aid: self._quick_action(x, "read"), "default").pack(side=tk.RIGHT, padx=2)

    def _quick_action(self, aid, state):
        """快速操作：收藏/已读."""
        self.app.personal.set_reading_state("article", aid, state)
        self._set_status(f"文章 {aid} 已标记为 {state}")

    # ========== 每日语录 ==========

    def _show_quote(self):
        self._clear_content()
        self._switch_page("quote")
        self._set_status("每日语录")

        # 标题
        header = tk.Frame(self.content, bg="#52c41a", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="每日语录",
            bg="#52c41a", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 风格选择
        select_frame = tk.Frame(self.content, bg=self.colors["bg"])
        select_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            select_frame, text="选择风格:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.quote_style = tk.StringVar(value="全部")
        styles = ["全部", "开心一点", "别委屈", "加油鼓励", "冷静理性", "幽默段子", "技术人专属", "哲理"]
        ttk.Combobox(
            select_frame, textvariable=self.quote_style,
            values=styles, state="readonly", width=12,
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT)

        self._create_button(select_frame, "换一批", self._refresh_quotes, "success").pack(side=tk.LEFT, padx=15)

        # 语录列表
        self.quote_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.quote_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._refresh_quotes()

    def _refresh_quotes(self):
        """刷新语录列表."""
        for widget in self.quote_frame.winfo_children():
            widget.destroy()

        style_map = {
            "全部": None, "开心一点": "happy", "别委屈": "comfort",
            "加油鼓励": "encourage", "冷静理性": "calm",
            "幽默段子": "humor", "技术人专属": "tech", "哲理": "philosophy"
        }
        style = style_map.get(self.quote_style.get())

        # 获取多条语录
        quotes = []
        with self.app.repo.db.connect() as conn:
            if style:
                rows = conn.execute("SELECT * FROM daily_quotes WHERE style = ? ORDER BY RANDOM() LIMIT 8", (style,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM daily_quotes ORDER BY RANDOM() LIMIT 8").fetchall()
            quotes = [dict(r) for r in rows]

        if not quotes:
            tk.Label(
                self.quote_frame, text="暂无语录",
                bg=self.colors["bg"], fg=self.colors["text_secondary"],
                font=("微软雅黑", 12)
            ).pack(pady=50)
            return

        # 语录卡片
        for q in quotes:
            card = tk.Frame(
                self.quote_frame, bg="white",
                relief=tk.FLAT, bd=1,
                highlightbackground=self.colors["border"],
                highlightthickness=1,
                padx=20, pady=15
            )
            card.pack(fill=tk.X, pady=5)

            # 语录内容
            tk.Label(
                card, text=f"\u300c{q.get('content', '')}\u300d",
                bg="white", fg=self.colors["text"],
                font=("微软雅黑", 12), wraplength=600, justify=tk.LEFT
            ).pack(anchor=tk.W)

            # 作者和风格
            bottom = tk.Frame(card, bg="white")
            bottom.pack(fill=tk.X, pady=(8, 0))

            author = q.get("author", "")
            if author:
                tk.Label(
                    bottom, text=f"\u2014\u2014 {author}",
                    bg="white", fg=self.colors["text_secondary"],
                    font=("微软雅黑", 10, "italic")
                ).pack(side=tk.LEFT)

            style_label = q.get("style", "")
            if style_label:
                tk.Label(
                    bottom, text=style_label,
                    bg=self.colors["tag_bg"], fg=self.colors["text_secondary"],
                    font=("微软雅黑", 9), padx=8, pady=2
                ).pack(side=tk.RIGHT)

    # ========== 技术变化 ==========

    def _show_tech(self):
        self._clear_content()
        self._switch_page("tech")
        self._set_status("技术变化")

        # 标题
        header = tk.Frame(self.content, bg="#2f54eb", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="技术变化追踪",
            bg="#2f54eb", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 说明
        tk.Label(
            self.content,
            text="自动检测新闻中的技术变化：版本发布、CVE 漏洞、重大更新、开源项目、AI 进展",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 10), wraplength=600
        ).pack(anchor=tk.W, padx=25, pady=(10, 0))

        # 按钮
        btn_frame = tk.Frame(self.content, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        self._create_button(btn_frame, "检测技术变化", self._detect_tech, "primary").pack(side=tk.LEFT, padx=5)
        self._create_button(btn_frame, "刷新列表", self._refresh_tech, "default").pack(side=tk.LEFT, padx=5)

        # 表格
        table_frame = tk.Frame(self.content, bg=self.colors["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("类型", "标题", "来源", "时间", "重要度")
        self.tech_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        for col in columns:
            self.tech_tree.heading(col, text=col)
            w = 100 if col in ("类型", "重要度") else 300 if col == "标题" else 120
            self.tech_tree.column(col, width=w, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tech_tree.yview)
        self.tech_tree.configure(yscrollcommand=scrollbar.set)
        self.tech_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_tech()

    def _detect_tech(self):
        """检测技术变化."""
        count = self.app.tech_service.detect_and_store()
        messagebox.showinfo("检测完成", f"从新闻中检测到 {count} 个技术变化")
        self._refresh_tech()

    def _refresh_tech(self):
        """刷新技术变化列表."""
        for item in self.tech_tree.get_children():
            self.tech_tree.delete(item)

        changes = self.app.tech_service.list_changes(limit=30)
        if not changes:
            # 插入提示
            self.tech_tree.insert("", tk.END, values=("", "暂无数据，请先采集新闻后点击「检测技术变化」", "", "", ""))
            return

        for c in changes:
            change_type = c.get("change_type", "")
            type_labels = {
                "release": "版本发布", "cve": "安全漏洞", "breaking": "重大变更",
                "opensource": "开源项目", "ai": "AI 进展"
            }
            type_text = type_labels.get(change_type, change_type)
            importance = c.get("importance", 0)
            self.tech_tree.insert("", tk.END, values=(
                type_text, c.get("title", ""), c.get("source_name", ""),
                c.get("published_at", "")[:16], f"{importance:.1f}"
            ))

    # ========== API 工具箱 ==========

    def _show_toolbox(self):
        self._clear_content()
        self._switch_page("toolbox")
        self._set_status("API 工具箱")

        # 标题
        header = tk.Frame(self.content, bg="#fa8c16", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="API 工具箱",
            bg="#fa8c16", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 说明
        tk.Label(
            self.content,
            text="管理 API 接口配置。部分 API 需要填写 Key 才能使用，点击「配置」按钮填写。",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 10), wraplength=600
        ).pack(anchor=tk.W, padx=25, pady=(10, 0))

        # API 列表
        list_frame = tk.Frame(self.content, bg=self.colors["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 滚动
        canvas = tk.Canvas(list_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.api_frame = tk.Frame(canvas, bg=self.colors["bg"])

        self.api_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.api_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_toolbox()

    def _refresh_toolbox(self):
        """刷新 API 列表."""
        for widget in self.api_frame.winfo_children():
            widget.destroy()

        apis = self.app.api_service.list_apis()

        # 按提供商分组
        providers = {}
        for a in apis:
            p = a.get("provider", "other")
            providers.setdefault(p, []).append(a)

        for provider, items in providers.items():
            # 提供商标题
            tk.Label(
                self.api_frame, text=f"【{provider}】",
                bg=self.colors["bg"], fg=self.colors["text"],
                font=("微软雅黑", 11, "bold"), anchor=tk.W
            ).pack(fill=tk.X, padx=10, pady=(15, 5))

            for a in items:
                card = tk.Frame(
                    self.api_frame, bg="white",
                    relief=tk.FLAT, bd=1,
                    highlightbackground=self.colors["border"],
                    highlightthickness=1,
                    padx=12, pady=8
                )
                card.pack(fill=tk.X, padx=10, pady=3)

                # 左侧信息
                left = tk.Frame(card, bg="white")
                left.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # 名称和状态
                name_frame = tk.Frame(left, bg="white")
                name_frame.pack(fill=tk.X)

                tk.Label(
                    name_frame, text=a.get("name", ""), bg="white",
                    fg=self.colors["text"], font=("微软雅黑", 10, "bold")
                ).pack(side=tk.LEFT)

                status = a.get("status", "")
                status_color = self.colors["success"] if status == "enabled" else self.colors["warning"] if status == "needs_config" else self.colors["text_secondary"]
                status_text = "可用" if status == "enabled" else "需配置" if status == "needs_config" else "禁用"
                tk.Label(
                    name_frame, text=status_text, bg=status_color,
                    fg="white", font=("微软雅黑", 8), padx=6, pady=1
                ).pack(side=tk.LEFT, padx=8)

                # 描述
                tk.Label(
                    left, text=a.get("description", ""), bg="white",
                    fg=self.colors["text_secondary"], font=("微软雅黑", 9),
                    anchor=tk.W
                ).pack(fill=tk.X)

                # 右侧操作
                right = tk.Frame(card, bg="white")
                right.pack(side=tk.RIGHT)

                if status == "needs_config":
                    self._create_button(
                        right, "配置 Key",
                        lambda x=a: self._config_api_key(x),
                        "warning"
                    ).pack(side=tk.RIGHT, padx=2)

    def _config_api_key(self, api):
        """配置 API Key."""
        dialog = tk.Toplevel(self)
        dialog.title(f"配置 {api.get('name', '')} API Key")
        dialog.geometry("450x250")
        dialog.resizable(False, False)

        tk.Label(
            dialog, text=f"配置 {api.get('name', '')}",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=15)

        tk.Label(
            dialog, text=f"API 地址: {api.get('base_url', '')}",
            font=("微软雅黑", 9), fg="#999"
        ).pack()

        tk.Label(dialog, text="请输入 API Key:", font=("微软雅黑", 10)).pack(pady=(15, 5))

        key_entry = tk.Entry(dialog, width=40, font=("微软雅黑", 11), show="*")
        key_entry.pack(pady=5)

        def save_key():
            key = key_entry.get().strip()
            if not key:
                messagebox.showwarning("提示", "请输入 API Key")
                return
            # 保存到配置
            with self.app.repo.db.connect() as conn:
                conn.execute(
                    "UPDATE api_catalog SET status='enabled' WHERE id=?",
                    (api.get("id"),)
                )
            messagebox.showinfo("成功", "API Key 已保存")
            dialog.destroy()
            self._refresh_toolbox()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        tk.Button(
            btn_frame, text="保存", command=save_key,
            bg=self.colors["primary"], fg="white", relief=tk.FLAT,
            padx=20, pady=8, font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame, text="取消", command=dialog.destroy,
            bg="#f5f5f5", fg=self.colors["text"], relief=tk.FLAT,
            padx=20, pady=8, font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=10)

    # ========== 搜索 ==========

    def _show_search(self):
        self._clear_content()
        self._switch_page("search")
        self._set_status("搜索")

        # 标题
        header = tk.Frame(self.content, bg="#1890ff", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="搜索",
            bg="#1890ff", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 搜索框
        search_frame = tk.Frame(self.content, bg=self.colors["bg"])
        search_frame.pack(fill=tk.X, padx=20, pady=15)

        self.search_entry = tk.Entry(
            search_frame, font=("微软雅黑", 12), width=50,
            relief=tk.FLAT, bd=1,
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=8)
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self._create_button(search_frame, "搜索", self._do_search, "primary").pack(side=tk.LEFT)

        # 搜索示例
        example_frame = tk.Frame(self.content, bg=self.colors["bg"])
        example_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            example_frame, text="搜索示例:",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9)
        ).pack(side=tk.LEFT, padx=(0, 10))

        examples = ["AI", "Python", "漏洞", "政策", "React", "地震"]
        for ex in examples:
            btn = tk.Button(
                example_frame, text=ex, command=lambda x=ex: self._search_example(x),
                bg=self.colors["tag_bg"], fg=self.colors["primary"],
                relief=tk.FLAT, padx=10, pady=3,
                font=("微软雅黑", 9), cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#e6f7ff"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.colors["tag_bg"]))

        # 重建索引按钮
        self._create_button(example_frame, "重建索引", self._rebuild_index, "warning").pack(side=tk.RIGHT)

        # 结果
        result_frame = tk.Frame(self.content, bg=self.colors["bg"])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("类型", "标题", "摘要")
        self.search_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        for col in columns:
            self.search_tree.heading(col, text=col)
            w = 80 if col == "类型" else 250 if col == "标题" else 400
            self.search_tree.column(col, width=w, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.search_result_label = tk.Label(
            self.content, text="输入关键词搜索本地新闻、技术文章、政策等",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 10)
        )
        self.search_result_label.pack(pady=10)

    def _search_example(self, text):
        """点击示例搜索."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
        self._do_search()

    def _do_search(self):
        """执行搜索."""
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

        self.search_result_label.configure(text=f"找到 {len(results)} 条结果")

    def _rebuild_index(self):
        """重建搜索索引."""
        count = self.app.search_service.rebuild_index()
        messagebox.showinfo("重建完成", f"已重建 {count} 条索引")

    # ========== 个人中心 ==========

    def _show_personal(self):
        self._clear_content()
        self._switch_page("personal")
        self._set_status("个人中心")

        # 标题
        header = tk.Frame(self.content, bg="#722ed1", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="个人中心",
            bg="#722ed1", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 统计卡片
        stats_frame = tk.Frame(self.content, bg=self.colors["bg"])
        stats_frame.pack(fill=tk.X, padx=20, pady=15)

        favorites = self.app.personal.list_collection("favorite")
        read_later = self.app.personal.list_collection("read_later")
        watchlist = self.app.personal.list_watchlist()

        stats = [
            ("收藏", len(favorites), "#1890ff"),
            ("稍后看", len(read_later), "#fa8c16"),
            ("关注清单", len(watchlist), "#52c41a"),
        ]

        for text, count, color in stats:
            card = tk.Frame(stats_frame, bg="white", relief=tk.FLAT, bd=1,
                          highlightbackground=self.colors["border"], highlightthickness=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            tk.Label(card, text=text, bg="white", fg=self.colors["text_secondary"],
                    font=("微软雅黑", 10)).pack(pady=(10, 0))
            tk.Label(card, text=str(count), bg="white", fg=color,
                    font=("微软雅黑", 24, "bold")).pack(pady=(0, 10))

        # 隐私模式
        privacy_frame = tk.Frame(self.content, bg=self.colors["bg"])
        privacy_frame.pack(fill=tk.X, padx=20, pady=10)

        self.privacy_var = tk.BooleanVar(value=self.app.personal.privacy_enabled())
        tk.Checkbutton(
            privacy_frame, text="隐私模式（暂停所有网络请求）",
            variable=self.privacy_var, command=self._toggle_privacy,
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 10), cursor="hand2"
        ).pack(anchor=tk.W)

        # 收藏列表
        tk.Label(
            self.content, text="我的收藏:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 12, "bold"), anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(10, 5))

        # 表格
        table_frame = tk.Frame(self.content, bg=self.colors["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("ID", "标题", "来源", "时间")
        fav_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        for col in columns:
            fav_tree.heading(col, text=col)
            w = 50 if col == "ID" else 350 if col == "标题" else 120
            fav_tree.column(col, width=w, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=fav_tree.yview)
        fav_tree.configure(yscrollcommand=scrollbar.set)
        fav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for a in favorites[:20]:
            fav_tree.insert("", tk.END, values=(
                a.get("id", ""), a.get("title", ""), a.get("source_name", ""),
                a.get("collected_at", "")[:16]
            ))

    def _toggle_privacy(self):
        """切换隐私模式."""
        enabled = self.privacy_var.get()
        self.app.personal.set_privacy_mode(enabled)
        self._set_status(f"隐私模式已{'开启' if enabled else '关闭'}")

    # ========== 来源管理 ==========

    def _show_sources(self):
        self._clear_content()
        self._switch_page("sources")
        self._set_status("来源管理")

        # 标题
        header = tk.Frame(self.content, bg="#595959", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="来源管理",
            bg="#595959", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)

        # 来源列表
        table_frame = tk.Frame(self.content, bg=self.colors["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        columns = ("ID", "名称", "类型", "分类", "状态", "失败次数")
        src_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        for col in columns:
            src_tree.heading(col, text=col)
            w = 50 if col == "ID" else 150 if col == "名称" else 80
            src_tree.column(col, width=w, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=src_tree.yview)
        src_tree.configure(yscrollcommand=scrollbar.set)
        src_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        sources = self.app.source_mgr.list_sources()
        health = self.app.source_health.get_health()
        health_map = {h["id"]: h for h in health}

        for s in sources:
            h = health_map.get(s["id"], {})
            status = "正常" if s.get("enabled") else "禁用"
            if h.get("paused"):
                status = "已暂停"
            elif h.get("failure_count", 0) > 0:
                status = f"失败"

            src_tree.insert("", tk.END, values=(
                s.get("id", ""), s.get("name", ""), s.get("type", ""),
                s.get("category", ""), status, h.get("failure_count", 0)
            ))

        tk.Label(
            self.content, text=f"共 {len(sources)} 个数据源",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9)
        ).pack(anchor=tk.W, padx=20, pady=5)

    # ========== 数据采集 ==========

    def _start_collect(self):
        """开始采集."""
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
        """采集完成."""
        self.collect_btn.configure(state=tk.NORMAL, text="一键采集数据")
        msg = (f"采集完成: 天气{result.get('weather',0)} "
               f"地震{result.get('earthquake',0)} "
               f"新闻{result.get('news',0)} "
               f"热点{result.get('hot',0)} "
               f"技术{result.get('tech',0)}")
        self._set_status(msg)
        if result.get("errors"):
            messagebox.showwarning("采集警告", f"部分采集失败:\n" + "\n".join(result["errors"]))
        else:
            messagebox.showinfo("采集完成", msg)

    def _on_collect_error(self, error):
        """采集失败."""
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
