"""Tkinter GUI - 完整版，符合国内使用习惯."""
from __future__ import annotations

import sys
import threading
import json
import webbrowser
import random
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.config.china_cities import PROVINCE_CITIES, all_city_names, city_coords, province_for_city
from news_intelligence_desktop.services.app_service import AppService
from news_intelligence_desktop.services.news_quality import format_news_time


CITIES = {city: city_coords(city) for city in all_city_names()}

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

        # 配色方案 - 现代柔和风格
        self.colors = {
            "bg": "#f6f7fb",
            "sidebar": "#111827",
            "sidebar_btn": "#1f2937",
            "sidebar_hover": "#263244",
            "sidebar_active": "#7c3aed",
            "primary": "#4f46e5",
            "primary_hover": "#4338ca",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "secondary": "#06b6d4",
            "text": "#111827",
            "text_secondary": "#6b7280",
            "border": "#e5e7eb",
            "card_bg": "#ffffff",
            "tag_bg": "#eef2ff",
            "soft_shadow": "#e9edf5",
        }

        self.configure(bg=self.colors["bg"])

        # 当前选中的城市
        saved_city = self.app.repo.get_pref("weather_city", "北京")
        self.current_city = tk.StringVar(value=saved_city)
        self.current_province = tk.StringVar(value=province_for_city(saved_city))
        self._current_page = "home"
        self.news_category = tk.StringVar(value="全部")

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
            logo_frame, text="每日信息宇宙",
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

        # 导航按钮。低分辨率屏幕下侧边栏也需要可滚动。
        nav_canvas = tk.Canvas(sidebar, bg=self.colors["sidebar"], highlightthickness=0, bd=0)
        nav_canvas.pack(fill=tk.BOTH, expand=True)
        nav_frame = tk.Frame(nav_canvas, bg=self.colors["sidebar"])
        nav_window = nav_canvas.create_window((0, 0), window=nav_frame, anchor=tk.NW)
        nav_frame.bind("<Configure>", lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.bind("<Configure>", lambda e: nav_canvas.itemconfigure(nav_window, width=e.width))
        nav_canvas.bind("<MouseWheel>", lambda e: nav_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        buttons = [
            ("首页总览", "home", self._show_home),
            ("快读新闻", "news", self._show_news),
            ("晨报晚报", "brief", self._show_briefs),
            ("天气预报", "weather", self._show_weather),
            ("地震动态", "earthquake", self._show_earthquake),
            ("热点报告", "hot", self._show_hot_report),
            ("每日语录", "quote", self._show_quote),
            ("娱乐工具", "fun", self._show_fun_tools),
            ("回复助手", "reply", self._show_reply_assistant),
            ("技术变化", "tech", self._show_tech),
            ("API 工具箱", "api", self._show_toolbox),
            ("关注清单", "watch", self._show_watchlist),
            ("政策追踪", "policy", self._show_policy),
            ("搜索", "search", self._show_search),
            ("个人中心", "user", self._show_personal),
            ("来源管理", "source", self._show_sources),
        ]

        self.nav_buttons = {}
        for text, key, cmd in buttons:
            btn = tk.Button(
                nav_frame, text=f"  {text}", command=cmd,
                bg=self.colors["sidebar"], fg="#bfbfbf",
                activebackground=self.colors["sidebar_hover"],
                activeforeground="white",
                relief=tk.FLAT, anchor=tk.W, padx=25, pady=11,
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

        self.nav_buttons["home"].configure(bg=self.colors["sidebar_active"], fg="white")

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
        area = tk.Frame(self, bg=self.colors["bg"])
        area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.content_canvas = tk.Canvas(area, bg=self.colors["bg"], highlightthickness=0, bd=0)
        self.content_scrollbar = ttk.Scrollbar(area, orient=tk.VERTICAL, command=self.content_canvas.yview)
        self.content = tk.Frame(self.content_canvas, bg=self.colors["bg"])
        self.content_window = self.content_canvas.create_window((0, 0), window=self.content, anchor=tk.NW)
        self.content.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.bind("<Configure>", lambda e: self.content_canvas.itemconfigure(self.content_window, width=e.width))
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        self.content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)

    def _on_global_mousewheel(self, event):
        """让鼠标在页面任意位置都能滚动主内容区."""
        try:
            widget = event.widget
            if isinstance(widget, str):
                widget = self.nametowidget(widget) if widget != "." else self
            if hasattr(widget, "winfo_class") and widget.winfo_class() in {"Treeview", "Text"}:
                return
        except Exception:
            pass
        self.content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        if hasattr(self, "content_canvas"):
            self.content_canvas.yview_moveto(0)

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
            padx=18, pady=15
        )
        card.grid(row=row, column=col, columnspan=colspan, padx=10, pady=10, sticky=tk.NSEW)
        return card

    def _create_soft_card(self, parent, padx=18, pady=16):
        """创建更现代的柔和卡片."""
        outer = tk.Frame(parent, bg=self.colors["soft_shadow"])
        inner = tk.Frame(
            outer, bg="white", relief=tk.FLAT, bd=0,
            highlightbackground=self.colors["border"], highlightthickness=1,
            padx=padx, pady=pady
        )
        inner.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 3))
        return outer, inner

    def _create_button(self, parent, text, command, style="primary"):
        """创建按钮."""
        color_map = {
            "primary": (self.colors["primary"], self.colors["primary_hover"]),
            "success": (self.colors["success"], "#389e0d"),
            "warning": (self.colors["warning"], "#d48806"),
            "danger": (self.colors["danger"], "#cf1322"),
            "secondary": (self.colors["secondary"], "#0891b2"),
            "default": ("#f5f5f5", "#e8e8e8"),
        }
        bg, hover_bg = color_map.get(style, color_map["primary"])
        fg = "white" if style != "default" else self.colors["text"]

        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
            relief=tk.FLAT, padx=17, pady=9,
            font=("微软雅黑", 10, "bold" if style != "default" else "normal"), cursor="hand2", bd=0
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg, padx=19))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg, padx=17))
        return btn

    def _create_tip_card(self, parent, title: str, body: str, color: str | None = None):
        """Create a small explanation card for user-facing workflows."""
        outer, card = self._create_soft_card(parent, padx=16, pady=12)
        outer.pack(fill=tk.X, padx=20, pady=(10, 4))
        tk.Label(
            card, text=title, bg="white", fg=color or self.colors["primary"],
            font=("微软雅黑", 11, "bold")
        ).pack(anchor=tk.W)
        tk.Label(
            card, text=body, bg="white", fg=self.colors["text_secondary"],
            font=("微软雅黑", 9), wraplength=850, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(4, 0))
        return outer, card

    def _center_window(self, win, width: int, height: int):
        """Center child windows on the main app."""
        self.update_idletasks()
        x = self.winfo_x() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_y() + max((self.winfo_height() - height) // 2, 0)
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.transient(self)
        win.lift()

    def _show_result_window(self, title: str, text: str, accent: str | None = None):
        """Modern result dialog shared by reply assistant and utility tools."""
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=self.colors["bg"])
        self._center_window(win, 680, 520)

        header_color = accent or self.colors["primary"]
        header = tk.Frame(win, bg=header_color, height=74)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=header_color, fg="white", font=("微软雅黑", 17, "bold")).pack(anchor=tk.W, padx=24, pady=(14, 0))
        tk.Label(header, text="重点内容已自动复制，可直接粘贴使用", bg=header_color, fg="#eef2ff", font=("微软雅黑", 10)).pack(anchor=tk.W, padx=24, pady=(2, 0))

        body = tk.Frame(win, bg=self.colors["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)
        outer, card = self._create_soft_card(body, padx=18, pady=16)
        outer.pack(fill=tk.BOTH, expand=True)
        lines = [line for line in text.splitlines() if line.strip()]
        focus = lines[0] if lines else text
        tk.Label(card, text="重点", bg="white", fg=header_color, font=("微软雅黑", 10, "bold")).pack(anchor=tk.W)
        tk.Label(card, text=focus, bg="white", fg=self.colors["text"], font=("微软雅黑", 14, "bold"), wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(4, 12))
        detail = scrolledtext.ScrolledText(card, wrap=tk.WORD, font=("微软雅黑", 11), relief=tk.FLAT, padx=10, pady=10, height=12)
        detail.pack(fill=tk.BOTH, expand=True)
        detail.insert(tk.END, text)
        detail.configure(state=tk.DISABLED)

        actions = tk.Frame(win, bg=self.colors["bg"])
        actions.pack(fill=tk.X, padx=20, pady=(0, 16))
        self._create_button(actions, "再次复制", lambda: self._copy_text(text, f"{title} 已复制"), "primary").pack(side=tk.LEFT, padx=4)
        self._create_button(actions, "关闭", win.destroy, "default").pack(side=tk.RIGHT, padx=4)

    def _copy_text(self, text: str, status: str = "已复制到剪贴板"):
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status(status)

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
        ).pack(side=tk.LEFT, padx=(30, 15), expand=True)

        # 一键刷新按钮
        self.home_refresh_btn = tk.Button(
            header, text=" 一键刷新数据 ", bg="white", fg=self.colors["primary"],
            font=("微软雅黑", 11, "bold"), relief=tk.FLAT, cursor="hand2",
            borderwidth=0, highlightthickness=1, highlightbackground=rgba(self.colors["primary"], 0.3)
        )
        self.home_refresh_btn.pack(side=tk.RIGHT, padx=30)
        self.home_refresh_btn.bind("<Button-1>", lambda e: self._home_refresh())
        tk.Label(header, text="  ", bg=self.colors["primary"]).pack(side=tk.RIGHT)

        # 内容区域
        self._home_content = main_frame = tk.Frame(self.content, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        self._render_home_content()

    def _render_home_content(self):
        for w in self._home_content.winfo_children():
            w.destroy()

        # 配置网格权重
        main_frame = self._home_content
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 获取数据
        dash = self.app.home_dashboard()

        # 重点速读，优先展示高重要度、高可信度、中文内容。
        important = self.app.repo.list_articles(limit=80)
        important = sorted(
            important,
            key=lambda a: (float(a.get("importance_score", 0)), float(a.get("credibility_score", 0)), 1 if a.get("language") == "zh" else 0),
            reverse=True,
        )[:4]
        if important:
            focus = tk.Frame(main_frame, bg="white", relief=tk.FLAT, bd=1, highlightbackground=self.colors["border"], highlightthickness=1, padx=16, pady=12)
            focus.grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=(0, 10))
            tk.Label(focus, text="重点速读", bg="white", fg=self.colors["danger"], font=("微软雅黑", 13, "bold")).pack(anchor=tk.W)
            for item in important:
                line = tk.Frame(focus, bg="white")
                line.pack(fill=tk.X, pady=3)
                tk.Label(line, text=f"{item.get('category', '').upper()} | {item.get('title', '')[:70]}", bg="white", fg=self.colors["text"], font=("微软雅黑", 10), anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self._create_button(line, "读", lambda x=item.get("id"): self._show_article_detail(x), "default").pack(side=tk.RIGHT)

        # 卡片
        for i, card_data in enumerate(dash.get("cards", [])):
            row, col = divmod(i, 2)
            card = self._create_card(main_frame, card_data["name"], row + 1, col)

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

    def _home_refresh(self):
        if not hasattr(self, 'home_refresh_btn'):
            return
        self.home_refresh_btn.config(state=tk.DISABLED, text=" 采集中...")
        self.after(50, self._run_home_refresh)

    def _run_home_refresh(self):
        def _collect_and_update():
            try:
                result = self.app.collect_all()
                self.after(0, lambda: self._on_home_refresh_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_home_refresh_error(str(e)))

        import threading
        threading.Thread(target=_collect_and_update, daemon=True).start()

    def _on_home_refresh_done(self, result):
        if hasattr(self, 'home_refresh_btn'):
            self.home_refresh_btn.config(state=tk.NORMAL, text=" 一键刷新数据 ")
        self._render_home_content()
        self._set_status(f"刷新完成 | 天气+{result.get('weather',0)} 新闻+{result.get('news',0)} 热点+{result.get('hot',0)}")

    def _on_home_refresh_error(self, error):
        if hasattr(self, 'home_refresh_btn'):
            self.home_refresh_btn.config(state=tk.NORMAL, text=" 一键刷新数据 ")
        self._set_status(f"刷新失败: {error}")

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
        self._create_tip_card(
            self.content,
            "城市会自动保存",
            "默认城市是北京；先选省区再选城市，广西壮族自治区和全国主要城市都已覆盖。选择新城市后会立即保存到本机，下次打开应用会恢复这个城市。",
            "#1890ff",
        )

        # 城市选择
        select_frame = tk.Frame(self.content, bg=self.colors["bg"])
        select_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            select_frame, text="省区:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT, padx=(0, 10))

        province_combo = ttk.Combobox(
            select_frame, textvariable=self.current_province,
            values=list(PROVINCE_CITIES.keys()), state="readonly", width=18,
            font=("微软雅黑", 10)
        )
        province_combo.pack(side=tk.LEFT, padx=(0, 10))
        province_combo.bind("<<ComboboxSelected>>", lambda e: self._on_province_changed())

        tk.Label(
            select_frame, text="城市:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.city_combo = ttk.Combobox(
            select_frame, textvariable=self.current_city,
            values=list(PROVINCE_CITIES.get(self.current_province.get(), {}).keys()), state="readonly", width=15,
            font=("微软雅黑", 10)
        )
        self.city_combo.pack(side=tk.LEFT)
        self.city_combo.bind("<<ComboboxSelected>>", lambda e: self._on_city_changed())

        self._create_button(select_frame, "刷新天气", self._refresh_weather, "primary").pack(side=tk.LEFT, padx=15)

        # 天气卡片区域
        self.weather_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.weather_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._refresh_weather()

    def _on_province_changed(self):
        province = self.current_province.get()
        cities = list(PROVINCE_CITIES.get(province, {}).keys())
        self.city_combo.configure(values=cities)
        if cities:
            self.current_city.set(cities[0])
            self._on_city_changed()

    def _on_city_changed(self):
        city = self.current_city.get()
        self.app.repo.set_pref("weather_city", city)
        self._set_status(f"已保存天气城市：{city}，下次启动自动恢复")
        self._refresh_weather()

    def _refresh_weather(self):
        """刷新天气数据."""
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        city = self.current_city.get()
        lat, lon = city_coords(city)

        # 从数据库获取天气
        with self.app.repo.db.connect() as conn:
            forecasts = [dict(r) for r in conn.execute(
                "SELECT * FROM weather_forecasts WHERE location_name=? ORDER BY forecast_date LIMIT 7",
                (city,)
            )]
            if not forecasts:
                forecasts = [dict(r) for r in conn.execute(
                    "SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7"
                )]

        if not forecasts:
            outer, card = self._create_soft_card(self.weather_frame, padx=24, pady=20)
            outer.pack(fill=tk.X, pady=30)
            tk.Label(card, text=f"暂无 {city} 天气数据", bg="white", fg=self.colors["text"], font=("微软雅黑", 14, "bold")).pack(anchor=tk.W)
            tk.Label(card, text="点击左侧“一键采集数据”后再回到本页查看。隐私模式开启时会暂停联网采集。", bg="white", fg=self.colors["text_secondary"], font=("微软雅黑", 10), wraplength=760, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))
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

        categories = ["全部", "国内", "新闻", "技术", "政策", "热点", "安全", "科学", "文化", "本地", "事故", "猎奇"]

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

        self.news_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.news_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.news_list_frame = tk.Frame(self.news_frame, bg=self.colors["bg"])
        self.news_list_frame.pack(fill=tk.BOTH, expand=True)

        self._refresh_news()

    def _refresh_news(self):
        """刷新新闻列表."""
        for widget in self.news_list_frame.winfo_children():
            widget.destroy()

        cat_map = {
            "全部": None, "新闻": "news", "技术": "tech", "政策": "policy",
            "热点": "hot", "安全": "security", "科学": "science", "文化": "culture",
            "本地": "local", "事故": "accident", "猎奇": "oddity"
        }
        cat = cat_map.get(self.news_category.get())
        articles = self.app.repo.list_articles(category=cat, limit=30)
        if self.news_category.get() == "国内":
            articles = [a for a in self.app.repo.list_articles(limit=100) if a.get("language") == "zh"][:30]
        elif self.news_category.get() == "猎奇":
            articles = self.app.oddity_service.list_oddities(limit=30)

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
            time_text = format_news_time(a.get("published_at") or a.get("collected_at"))
            tk.Label(
                title_frame, text=time_text, bg="white",
                fg=self.colors["text_secondary"], font=("微软雅黑", 9)
            ).pack(side=tk.RIGHT)

            # 摘要
            summary = a.get("summary", "")[:220]
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
            score = a.get("credibility_score", 0.6)
            importance = float(a.get("importance_score", 0.5))
            tk.Label(
                bottom, text=f"可信度 {score:.0%}", bg="white",
                fg=self.colors["success"] if score >= 0.75 else self.colors["warning"], font=("微软雅黑", 9)
            ).pack(side=tk.LEFT, padx=12)
            tk.Label(
                bottom, text=f"重要度 {importance:.0%}", bg="white",
                fg=self.colors["danger"] if importance >= 0.7 else self.colors["text_secondary"], font=("微软雅黑", 9)
            ).pack(side=tk.LEFT, padx=8)
            self._create_button(bottom, "阅读全文", lambda x=aid: self._show_article_detail(x), "primary").pack(side=tk.RIGHT, padx=2)
            self._create_button(bottom, "导出", lambda x=aid: self._export_article_dialog(x), "default").pack(side=tk.RIGHT, padx=2)
            self._create_button(bottom, "稍后看", lambda x=aid: self._quick_action(x, "read_later"), "default").pack(side=tk.RIGHT, padx=2)
            self._create_button(bottom, "收藏", lambda x=aid: self._quick_action(x, "favorite"), "default").pack(side=tk.RIGHT, padx=2)
            self._create_button(bottom, "已读", lambda x=aid: self._quick_action(x, "read"), "default").pack(side=tk.RIGHT, padx=2)

    def _quick_action(self, aid, state):
        """快速操作：收藏/已读."""
        self.app.personal.set_reading_state("article", aid, state)
        self._set_status(f"文章 {aid} 已标记为 {state}")

    def _show_article_detail(self, aid: int):
        article = self.app.repo.get_article(aid)
        if not article:
            messagebox.showwarning("提示", "文章不存在")
            return
        self.app.personal.set_reading_state("article", aid, "read")
        dialog = tk.Toplevel(self)
        dialog.title(article.get("title", "文章详情"))
        dialog.geometry("820x680")
        dialog.configure(bg="white")

        tk.Label(dialog, text=article.get("title", ""), bg="white", fg=self.colors["text"], font=("微软雅黑", 16, "bold"), wraplength=760, justify=tk.LEFT).pack(anchor=tk.W, padx=20, pady=(18, 8))
        meta = f"来源：{article.get('source_name', '')}    时间：{(article.get('published_at') or article.get('collected_at') or '')[:16]}    分类：{article.get('category', '')}"
        tk.Label(dialog, text=meta, bg="white", fg=self.colors["text_secondary"], font=("微软雅黑", 10)).pack(anchor=tk.W, padx=20)
        cred = self.app.credibility.explain("article", aid)
        tk.Label(dialog, text=f"可信度：{float(cred.get('score', 0.5)):.0%}，{cred.get('explanation', '')}", bg="white", fg=self.colors["success"], font=("微软雅黑", 10)).pack(anchor=tk.W, padx=20, pady=(6, 10))

        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=("微软雅黑", 11), relief=tk.FLAT, padx=12, pady=12)
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        body = article.get("content") or article.get("summary") or "暂无正文摘要，可点击原文查看。"
        if article.get("summary") and article.get("content"):
            body = f"重点摘要：\n{article.get('summary')}\n\n正文：\n{article.get('content')}"
        text.insert(tk.END, body)
        text.configure(state=tk.DISABLED)

        actions = tk.Frame(dialog, bg="white")
        actions.pack(fill=tk.X, padx=20, pady=(0, 16))
        self._create_button(actions, "打开原文", lambda: webbrowser.open(article.get("url", "")), "primary").pack(side=tk.LEFT, padx=4)
        self._create_button(actions, "收藏", lambda: self._quick_action(aid, "favorite"), "default").pack(side=tk.LEFT, padx=4)
        self._create_button(actions, "导出", lambda: self._export_article_dialog(aid), "default").pack(side=tk.LEFT, padx=4)
        self._create_button(actions, "关闭", dialog.destroy, "default").pack(side=tk.RIGHT, padx=4)

    def _export_article_dialog(self, aid: int):
        fmt = simpledialog.askstring("导出文章", "导出格式：markdown / html / json / csv", initialvalue="markdown")
        if not fmt:
            return
        fmt = fmt.strip().lower()
        suffix = {"markdown": ".md", "html": ".html", "json": ".json", "csv": ".csv"}.get(fmt, ".md")
        path = filedialog.asksaveasfilename(title="保存导出文件", defaultextension=suffix, filetypes=[("导出文件", f"*{suffix}"), ("所有文件", "*.*")])
        if not path:
            return
        out = self.app.export_article(aid, Path(path), fmt)
        messagebox.showinfo("导出完成", f"已导出：{out}")

    # ========== 每日语录 ==========

    def _show_quote(self):
        self._clear_content()
        self._switch_page("quote")
        self._set_status("每日学习卡")

        # 标题
        header = tk.Frame(self.content, bg="#52c41a", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="每日学习卡",
            bg="#52c41a", fg="white",
            font=("微软雅黑", 20, "bold")
        ).pack(expand=True)
        self._create_tip_card(
            self.content,
            "换批会优先展示较少出现的学习卡",
            "每张卡包含一句话、知识点和行动建议。点击“下一批学习卡”会按展示次数轮换，帮助你少看重复内容。",
            "#52c41a",
        )

        # 风格选择
        select_frame = tk.Frame(self.content, bg=self.colors["bg"])
        select_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            select_frame, text="选择风格:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.quote_style = tk.StringVar(value="全部")
        self.quote_style_options = {"全部": None}
        styles = ["全部"]
        for item in self.app.quote_service.list_styles():
            if item.get("count", 0) > 0:
                label = f"{item['label']}({item['count']})"
                self.quote_style_options[label] = item["key"]
                styles.append(label)
        ttk.Combobox(
            select_frame, textvariable=self.quote_style,
            values=styles, state="readonly", width=12,
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT)

        self.quote_batch_var = tk.StringVar(value="")
        self._create_button(select_frame, "下一批学习卡", self._refresh_quotes, "success").pack(side=tk.LEFT, padx=15)
        tk.Label(
            select_frame, textvariable=self.quote_batch_var,
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9)
        ).pack(side=tk.LEFT)

        # 语录列表
        self.quote_frame = tk.Frame(self.content, bg=self.colors["bg"])
        self.quote_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._refresh_quotes()

    def _refresh_quotes(self):
        """刷新语录列表."""
        for widget in self.quote_frame.winfo_children():
            widget.destroy()

        label_map = {item["key"]: item["label"] for item in self.app.quote_service.list_styles()}
        style = getattr(self, "quote_style_options", {"全部": None}).get(self.quote_style.get())

        # 获取多条语录
        quotes = []
        with self.app.repo.db.connect() as conn:
            if style:
                rows = conn.execute(
                    """SELECT * FROM daily_quotes WHERE style = ? AND (lesson <> '' OR action <> '')
                    ORDER BY shown_count ASC, RANDOM() LIMIT 8""",
                    (style,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM daily_quotes WHERE lesson <> '' OR action <> ''
                    ORDER BY shown_count ASC, RANDOM() LIMIT 8"""
                ).fetchall()
            quotes = [dict(r) for r in rows]
            for q in quotes:
                conn.execute("UPDATE daily_quotes SET shown_count=shown_count+1, last_shown_at=CURRENT_TIMESTAMP WHERE id=?", (q["id"],))

        if not quotes:
            if hasattr(self, "quote_batch_var"):
                self.quote_batch_var.set("当前分类内容不足，请选择“全部”查看更多")
            tk.Label(
                self.quote_frame, text="当前分类暂无学习卡，请选择“全部”查看更多。",
                bg=self.colors["bg"], fg=self.colors["text_secondary"],
                font=("微软雅黑", 12)
            ).pack(pady=50)
            return

        if hasattr(self, "quote_batch_var"):
            self.quote_batch_var.set(f"已换出 {len(quotes)} 张，优先展示低重复内容")
        self._set_status(f"每日学习卡已换批：{len(quotes)} 张")

        # 学习卡片
        for q in quotes:
            outer, card = self._create_soft_card(self.quote_frame, padx=20, pady=15)
            outer.pack(fill=tk.X, pady=6)

            # 语录内容
            tk.Label(
                card, text=f"\u300c{q.get('content', '')}\u300d",
                bg="white", fg=self.colors["text"],
                font=("微软雅黑", 12), wraplength=600, justify=tk.LEFT
            ).pack(anchor=tk.W)

            lesson = q.get("lesson", "")
            action = q.get("action", "")
            if lesson:
                tk.Label(card, text=f"知识点：{lesson}", bg="white", fg=self.colors["text_secondary"], font=("微软雅黑", 10), wraplength=720, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))
            if action:
                tk.Label(card, text=f"行动：{action}", bg="white", fg=self.colors["primary"], font=("微软雅黑", 10, "bold"), wraplength=720, justify=tk.LEFT).pack(anchor=tk.W, pady=(4, 0))

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
                    bottom, text=label_map.get(style_label, style_label),
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
        self.tech_summary_var = tk.StringVar(value="当前显示最近 30 条技术变化，检测结果会去重更新。")
        tk.Label(btn_frame, textvariable=self.tech_summary_var, bg=self.colors["bg"], fg=self.colors["text_secondary"], font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=12)

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
        total = self.app.tech_service.count_changes()
        messagebox.showinfo("检测完成", f"新增 {count} 个技术变化，当前共 {total} 个，列表显示最近 30 个。")
        self._refresh_tech()

    def _refresh_tech(self):
        """刷新技术变化列表."""
        for item in self.tech_tree.get_children():
            self.tech_tree.delete(item)

        changes = self.app.tech_service.list_changes(limit=30)
        total = self.app.tech_service.count_changes()
        if hasattr(self, "tech_summary_var"):
            self.tech_summary_var.set(f"当前共 {total} 个技术变化，正在显示最近 {len(changes)} 个。")
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
        self._switch_page("api")
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
            text="管理内置 API 与外置 API。外置新闻 API 可绑定到新闻模块，后续一键采集会自动读取兼容数据。",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 10), wraplength=600
        ).pack(anchor=tk.W, padx=25, pady=(10, 0))

        action_frame = tk.Frame(self.content, bg=self.colors["bg"])
        action_frame.pack(fill=tk.X, padx=20, pady=(8, 0))
        self.api_filter = tk.StringVar(value="全部")
        for label in ["全部", "内置", "外置", "新闻", "天气", "热榜", "需配置"]:
            tk.Radiobutton(
                action_frame, text=label, variable=self.api_filter, value=label, command=self._refresh_toolbox,
                indicatoron=0, bg=self.colors["tag_bg"], fg=self.colors["text"], selectcolor=self.colors["primary"],
                padx=10, pady=4, relief=tk.FLAT, font=("微软雅黑", 9)
            ).pack(side=tk.LEFT, padx=3)
        self._create_button(action_frame, "添加外置 API", self._add_external_api_dialog, "success").pack(side=tk.RIGHT)
        self.api_validate_btn = self._create_button(action_frame, "一键检测 API", self._validate_all_apis, "warning")
        self.api_validate_btn.pack(side=tk.RIGHT, padx=8)
        self.api_summary_var = tk.StringVar(value="检测会真实请求免费内置 API，需配置 Key 的接口会保持“需配置”状态。")
        tk.Label(
            self.content, textvariable=self.api_summary_var,
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9), anchor=tk.W
        ).pack(fill=tk.X, padx=25, pady=(6, 0))

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
        filter_val = getattr(self, "api_filter", tk.StringVar(value="全部")).get()
        if filter_val == "内置":
            apis = [a for a in apis if a.get("api_kind", "built_in") == "built_in"]
        elif filter_val == "外置":
            apis = [a for a in apis if a.get("api_kind") == "external"]
        elif filter_val == "需配置":
            apis = [a for a in apis if a.get("status") == "needs_config"]
        elif filter_val != "全部":
            apis = [a for a in apis if a.get("category") == filter_val or a.get("target_module") == {"新闻":"news", "天气":"weather", "热榜":"hot"}.get(filter_val)]

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
                kind_text = "外置" if a.get("api_kind") == "external" else "内置"
                status_text = f"{kind_text}·" + ("可用" if status == "enabled" else "需配置" if status == "needs_config" else "禁用")
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

                self._create_button(right, "编辑", lambda x=a: self._edit_api_dialog(x), "default").pack(side=tk.RIGHT, padx=2)
                self._create_button(right, "检测", lambda x=a: self._validate_one_api(x), "primary").pack(side=tk.RIGHT, padx=2)
                if status == "needs_config" or a.get("auth_type") != "No":
                    self._create_button(right, "配置 Key", lambda x=a: self._config_api_key(x), "warning").pack(side=tk.RIGHT, padx=2)

    def _validate_one_api(self, api):
        self._set_status(f"正在检测 {api.get('name', '')}...")
        self.update_idletasks()
        result = self.app.api_service.validate_api(api)
        messagebox.showinfo("API 检测", f"{api.get('name', '')}\n状态: {result['status']}\n结果: {result['message']}")
        self._refresh_toolbox()
        self._set_status("API 检测完成")

    def _validate_all_apis(self):
        self._set_status("正在后台检测所有免费内置 API...")
        if hasattr(self, "api_summary_var"):
            self.api_summary_var.set("检测中，请稍候。期间可以继续查看其他页面。")
        if hasattr(self, "api_validate_btn"):
            self.api_validate_btn.configure(state=tk.DISABLED, text="检测中...")

        def do_validate():
            result = self.app.api_service.validate_all_enabled_free()
            self.after(0, lambda: self._on_validate_all_apis_done(result))

        threading.Thread(target=do_validate, daemon=True).start()

    def _on_validate_all_apis_done(self, result):
        if hasattr(self, "api_validate_btn"):
            self.api_validate_btn.configure(state=tk.NORMAL, text="一键检测 API")
        detail = "\n".join(f"{r['name']}: {r['message']}" for r in result["failed"][:12])
        message = f"检测完成：{result['ok']}/{result['total']} 可用"
        if detail:
            message += f"\n\n需处理：\n{detail}"
        if hasattr(self, "api_summary_var"):
            self.api_summary_var.set(message.replace("\n\n", "；").replace("\n", "；")[:240])
        self._refresh_toolbox()
        self._set_status("API 检测完成")
        messagebox.showinfo("一键检测 API", message)

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
            self.app.api_service.save_api(api.get("id"), api_key=key, status="enabled")
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

    def _edit_api_dialog(self, api):
        """编辑 API 信息."""
        dialog = tk.Toplevel(self)
        dialog.title(f"编辑 API - {api.get('name', '')}")
        dialog.geometry("520x420")
        dialog.resizable(False, False)

        fields = {}
        rows = [
            ("名称", "name"), ("提供商", "provider"), ("分类", "category"),
            ("绑定模块", "target_module"), ("接口地址", "base_url"), ("说明", "description"),
        ]
        tk.Label(dialog, text="编辑 API 配置", font=("微软雅黑", 14, "bold")).pack(pady=12)
        form = tk.Frame(dialog)
        form.pack(fill=tk.BOTH, expand=True, padx=20)
        for label, key in rows:
            line = tk.Frame(form)
            line.pack(fill=tk.X, pady=5)
            tk.Label(line, text=label, width=10, anchor=tk.E, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(0, 8))
            entry = tk.Entry(line, font=("微软雅黑", 10))
            entry.insert(0, str(api.get(key, "")))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            fields[key] = entry

        def save():
            updates = {key: entry.get().strip() for key, entry in fields.items()}
            self.app.api_service.save_api(api["id"], **updates)
            messagebox.showinfo("成功", "API 已更新")
            dialog.destroy()
            self._refresh_toolbox()

        btns = tk.Frame(dialog)
        btns.pack(pady=14)
        tk.Button(btns, text="保存", command=save, bg=self.colors["primary"], fg="white", relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="取消", command=dialog.destroy, bg="#f5f5f5", relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=8)

    def _add_external_api_dialog(self):
        """添加外置 API，并按绑定模块纳入后续采集."""
        dialog = tk.Toplevel(self)
        dialog.title("添加外置 API")
        dialog.geometry("540x460")
        dialog.resizable(False, False)

        fields = {}
        rows = [
            ("名称", "name", "我的新闻 API"),
            ("提供商", "provider", "custom"),
            ("分类", "category", "新闻"),
            ("绑定模块", "target_module", "news"),
            ("接口地址", "base_url", "https://example.com/api/news"),
            ("说明", "description", "外置新闻源"),
            ("鉴权类型", "auth_type", "No"),
            ("API Key", "api_key", ""),
        ]
        tk.Label(dialog, text="添加外置 API", font=("微软雅黑", 14, "bold")).pack(pady=12)
        tk.Label(dialog, text="绑定模块填 news/weather/hot/tech/quote。新闻类 API 会同步加入来源管理，并在一键采集时尝试读取。", fg="#666", wraplength=460).pack(pady=(0, 10))
        form = tk.Frame(dialog)
        form.pack(fill=tk.BOTH, expand=True, padx=20)
        for label, key, default in rows:
            line = tk.Frame(form)
            line.pack(fill=tk.X, pady=4)
            tk.Label(line, text=label, width=10, anchor=tk.E, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(0, 8))
            entry = tk.Entry(line, font=("微软雅黑", 10), show="*" if key == "api_key" else "")
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            fields[key] = entry

        def save():
            data = {key: entry.get().strip() for key, entry in fields.items()}
            if not data["name"] or not data["base_url"]:
                messagebox.showwarning("提示", "名称和接口地址必填")
                return
            self.app.api_service.add_external_api(**data)
            category_map = {"新闻": "news", "热榜": "hot", "天气": "weather", "技术": "tech"}
            if data["target_module"] in {"news", "hot", "tech"}:
                self.app.source_mgr.create_source(data["name"], "api", category_map.get(data["category"], data["target_module"]), data["base_url"], data["auth_type"], {"api_key": data["api_key"]})
            messagebox.showinfo("成功", "外置 API 已添加")
            dialog.destroy()
            self._refresh_toolbox()

        btns = tk.Frame(dialog)
        btns.pack(pady=14)
        tk.Button(btns, text="保存", command=save, bg=self.colors["success"], fg="white", relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="取消", command=dialog.destroy, bg="#f5f5f5", relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=8)

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

        self._create_button(search_frame, "本地搜索", self._do_search, "primary").pack(side=tk.LEFT)
        self._create_button(search_frame, "百度新闻搜索", self._do_baidu_search, "success").pack(side=tk.LEFT, padx=8)

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

    def _do_baidu_search(self):
        """百度新闻在线搜索."""
        query = self.search_entry.get().strip()
        if not query:
            return
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        self.search_result_label.configure(text="正在搜索百度新闻...")
        self.update_idletasks()

        from news_intelligence_desktop.connectors.extra_sources import BaiduNewsConnector
        baidu = BaiduNewsConnector()
        result = baidu.search(query, limit=20)
        if result.ok:
            for r in result.data:
                self.search_tree.insert("", tk.END, values=(
                    "百度新闻", r.get("title", ""), r.get("summary", "")[:80]
                ))
            self.search_result_label.configure(text=f"百度新闻找到 {len(result.data)} 条结果，耗时 {result.response_ms:.0f}ms")
        else:
            self.search_result_label.configure(text=f"百度搜索失败: {result.error}")

    def _rebuild_index(self):
        """重建搜索索引."""
        count = self.app.search_service.rebuild_index()
        messagebox.showinfo("重建完成", f"已重建 {count} 条索引")

    # ========== 个人中心 ==========

    def _show_personal(self):
        self._clear_content()
        self._switch_page("user")
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
        privacy_text = "已开启：一键采集会暂停联网请求，只查看本地缓存。" if self.app.personal.privacy_enabled() else "已关闭：一键采集会正常访问天气、新闻、热搜和外置来源。"
        tk.Label(
            privacy_frame, text=privacy_text,
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9), wraplength=760, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(4, 0))

        backup_frame = tk.Frame(self.content, bg=self.colors["bg"])
        backup_frame.pack(fill=tk.X, padx=20, pady=8)
        self._create_button(backup_frame, "创建备份", self._create_backup_dialog, "primary").pack(side=tk.LEFT, padx=4)
        self._create_button(backup_frame, "恢复备份", self._restore_backup_dialog, "warning").pack(side=tk.LEFT, padx=4)

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
        if enabled:
            self._set_status("隐私模式已开启：联网采集暂停")
            messagebox.showinfo("隐私模式", "隐私模式已开启。\n\n天气、新闻、热搜、API 和外置来源采集都会暂停，已有本地内容仍可查看。")
        else:
            self._set_status("隐私模式已关闭：联网采集恢复")
            messagebox.showinfo("隐私模式", "隐私模式已关闭。\n\n可以继续使用一键采集更新天气、新闻、热搜和外置来源。")
        self._show_personal()

    def _create_backup_dialog(self):
        path = filedialog.asksaveasfilename(title="保存备份", defaultextension=".sqlite3", filetypes=[("SQLite 备份", "*.sqlite3"), ("所有文件", "*.*")])
        if not path:
            return
        out = self.app.create_backup(Path(path))
        messagebox.showinfo("备份完成", f"已备份：{out}")

    def _restore_backup_dialog(self):
        path = filedialog.askopenfilename(title="选择备份文件", filetypes=[("SQLite 备份", "*.sqlite3"), ("所有文件", "*.*")])
        if not path:
            return
        if not messagebox.askyesno("确认恢复", "恢复备份会覆盖当前数据，请确认已保留当前数据备份。"):
            return
        ok = self.app.backup_service.restore_backup(Path(path))
        messagebox.showinfo("恢复结果", "恢复成功，请重启应用" if ok else "恢复失败")

    # ========== 晨报晚报 / 热点 / 猎奇 / 关注 / 政策 ==========

    def _show_briefs(self):
        self._clear_content()
        self._switch_page("brief")
        self._set_status("晨报晚报")
        self._page_header("晨报晚报", "#13c2c2")
        action = tk.Frame(self.content, bg=self.colors["bg"])
        action.pack(fill=tk.X, padx=20, pady=12)
        self._create_button(action, "生成晨报", lambda: self._generate_brief("晨报"), "primary").pack(side=tk.LEFT, padx=4)
        self._create_button(action, "生成晚报", lambda: self._generate_brief("晚报"), "success").pack(side=tk.LEFT, padx=4)
        self.brief_text = scrolledtext.ScrolledText(self.content, wrap=tk.WORD, font=("微软雅黑", 11), padx=12, pady=12)
        self.brief_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        briefs = self.app.brief_service.list_briefs()
        if briefs:
            self.brief_text.insert(tk.END, briefs[0].get("body", ""))
        else:
            self.brief_text.insert(tk.END, "点击生成晨报或晚报，系统会按技术、重要新闻、政策、本地、热点、天气地震和语录汇总。")

    def _generate_brief(self, brief_type: str):
        brief = self.app.generate_brief(brief_type)
        self.brief_text.configure(state=tk.NORMAL)
        self.brief_text.delete("1.0", tk.END)
        self.brief_text.insert(tk.END, brief.get("body", ""))
        self._set_status(f"已生成{brief_type}")

    def _show_hot_report(self):
        self._clear_content()
        self._switch_page("hot")
        self._set_status("热点报告")
        self._page_header("热点报告", "#f5222d")
        articles = self.app.repo.list_articles(category="hot", limit=50)
        self._render_article_cards(articles, "暂无热点数据，请先一键采集。")

    def _show_oddity(self):
        self._clear_content()
        self._switch_page("oddity")
        self._set_status("猎奇内容")
        self._page_header("猎奇内容", "#eb2f96")
        articles = self.app.oddity_service.list_oddities(limit=50)
        self._render_article_cards(articles, "暂无奇闻、趣闻、争议类内容。")

    def _show_watchlist(self):
        self._clear_content()
        self._switch_page("watch")
        self._set_status("关注清单")
        self._page_header("关注清单", "#52c41a")
        action = tk.Frame(self.content, bg=self.colors["bg"])
        action.pack(fill=tk.X, padx=20, pady=12)
        self._create_button(action, "添加关注", self._add_watch_dialog, "success").pack(side=tk.LEFT, padx=4)
        matches = self.app.personal.watchlist_matches()
        tk.Label(self.content, text=f"当前命中 {len(matches)} 条关注内容", bg=self.colors["bg"], fg=self.colors["text_secondary"], font=("微软雅黑", 10)).pack(anchor=tk.W, padx=20)
        articles = [m["article"] for m in matches]
        self._render_article_cards(articles, "暂无关注命中。可添加关键词、公司、技术栈、城市、政策主题或人物。")

    def _add_watch_dialog(self):
        name = simpledialog.askstring("添加关注", "关注名称：")
        if not name:
            return
        item_type = simpledialog.askstring("添加关注", "类型：keyword/company/tech_stack/city/policy_topic/person", initialvalue="keyword") or "keyword"
        keywords = simpledialog.askstring("添加关注", "关键词，多个用逗号分隔：")
        if not keywords:
            return
        self.app.personal.add_watchlist(name, item_type, [k.strip() for k in keywords.split(",") if k.strip()])
        self._show_watchlist()

    def _show_policy(self):
        self._clear_content()
        self._switch_page("policy")
        self._set_status("政策追踪")
        self._page_header("政策追踪", "#fa8c16")
        action = tk.Frame(self.content, bg=self.colors["bg"])
        action.pack(fill=tk.X, padx=20, pady=12)
        self._create_button(action, "添加政策", self._add_policy_dialog, "success").pack(side=tk.LEFT, padx=4)
        policies = self.app.policy_service.list_policies(limit=80)
        rows = [{"id": 0, "title": p["title"], "summary": p.get("summary", ""), "source_name": p.get("issuer") or p.get("source_name", ""), "url": p.get("source_url", ""), "category": "policy", "collected_at": p.get("collected_at", "")} for p in policies]
        self._render_article_cards(rows, "暂无政策条目。")

    def _add_policy_dialog(self):
        title = simpledialog.askstring("添加政策", "政策标题：")
        if not title:
            return
        issuer = simpledialog.askstring("添加政策", "发布机构：", initialvalue="") or ""
        region = simpledialog.askstring("添加政策", "地区：", initialvalue="全国") or ""
        summary = simpledialog.askstring("添加政策", "摘要：", initialvalue="") or ""
        self.app.policy_service.add_policy(title, issuer=issuer, region=region, summary=summary)
        self._show_policy()

    def _show_fun_tools(self):
        self._clear_content()
        self._switch_page("fun")
        self._set_status("娱乐工具")
        self._page_header("娱乐工具", "#eb2f96")
        wrapper = tk.Frame(self.content, bg=self.colors["bg"])
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=18)
        tk.Label(
            wrapper,
            text="这些工具会生成可直接粘贴使用的结果，并自动复制到剪贴板。",
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 10), anchor=tk.W
        ).grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=(0, 10))
        tools = [
            ("三步行动计划", "把模糊目标拆成能开始的步骤", self._tool_action_plan),
            ("决策矩阵", "给选择加权评分，减少纠结", self._tool_decision_matrix),
            ("沟通重写", "把生硬表达改成更清楚温和", self._tool_rewrite_message),
            ("复盘模板", "生成一份 3 分钟复盘", self._tool_review_template),
            ("专注启动器", "生成 25 分钟专注任务", self._tool_focus_starter),
            ("信息判断", "判断新闻是否值得继续读", self._tool_info_check),
            ("学习卡片", "抽一张不重复的知识卡", lambda: self._show_learning_quote()),
            ("社交破冰", "生成具体可用的开场白", self._tool_icebreaker),
            ("今日微任务", "给今天一个可完成的小任务", self._tool_micro_task),
            ("反内耗处理", "把焦虑变成下一步动作", self._tool_reduce_overthinking),
        ]
        for idx, (title, desc, cmd) in enumerate(tools):
            outer, card = self._create_soft_card(wrapper)
            outer.grid(row=(idx // 2) + 1, column=idx % 2, sticky=tk.NSEW, padx=10, pady=10)
            wrapper.columnconfigure(idx % 2, weight=1)
            accent = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#eb2f96"][idx % 5]
            top = tk.Frame(card, bg="white")
            top.pack(fill=tk.X)
            tk.Label(top, text=title, bg="white", fg=accent, font=("微软雅黑", 14, "bold")).pack(side=tk.LEFT, anchor=tk.W)
            tk.Label(top, text="可复制", bg=self.colors["tag_bg"], fg=self.colors["text_secondary"], font=("微软雅黑", 8), padx=8, pady=2).pack(side=tk.RIGHT)
            tk.Label(card, text=desc, bg="white", fg=self.colors["text"], font=("微软雅黑", 10), wraplength=430, justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 10))
            btn_text = "生成并复制" if title not in {"社交破冰", "今日微任务", "学习卡片"} else "抽取并复制"
            self._create_button(card, btn_text, cmd, "secondary" if idx % 3 == 1 else "primary").pack(anchor=tk.W)

    def _copy_result_dialog(self, title: str, text: str):
        self._copy_text(text, f"{title} 已生成并复制到剪贴板")
        self._show_result_window(title, text, "#eb2f96")

    def _tool_action_plan(self):
        goal = simpledialog.askstring("三步行动计划", "你想推进什么事？", initialvalue="整理今天的信息")
        if not goal:
            return
        text = f"目标：{goal}\n1. 用一句话定义完成标准。\n2. 找到 15 分钟内能做完的第一步。\n3. 完成后记录一个结果和一个阻碍。"
        self._copy_result_dialog("三步行动计划", text)

    def _tool_decision_matrix(self):
        options = simpledialog.askstring("决策矩阵", "输入选项，用逗号分隔：", initialvalue="方案A,方案B")
        if not options:
            return
        rows = [o.strip() for o in options.split(",") if o.strip()]
        text = "评分维度：收益 / 成本 / 风险 / 可逆性 / 30天后是否后悔\n" + "\n".join(f"- {r}: 分别打 1-5 分，总分最高优先试行。" for r in rows)
        self._copy_result_dialog("决策矩阵", text)

    def _tool_rewrite_message(self):
        raw = simpledialog.askstring("沟通重写", "输入你想发的话：")
        if not raw:
            return
        text = f"原意：{raw}\n建议表达：我理解这个事情的重点是……我这边可以先做……预计在……给你反馈。"
        self._copy_result_dialog("沟通重写", text)

    def _tool_review_template(self):
        text = "3 分钟复盘：\n1. 今天发生了什么？\n2. 哪个动作有效？\n3. 哪个阻碍重复出现？\n4. 明天只改一个什么动作？"
        self._copy_result_dialog("复盘模板", text)

    def _tool_focus_starter(self):
        task = simpledialog.askstring("专注启动器", "接下来 25 分钟做什么？", initialvalue="处理一条最重要的信息")
        if not task:
            return
        text = f"25 分钟专注任务：{task}\n规则：只开一个窗口；手机放远；结束后写一句产出。"
        self._copy_result_dialog("专注启动器", text)

    def _tool_info_check(self):
        text = "信息判断清单：\n1. 来源是谁？\n2. 是否有原始链接？\n3. 事实、观点、推测分别是哪句？\n4. 是否有第二来源验证？\n5. 读完后需要行动吗？"
        self._copy_result_dialog("信息判断", text)

    def _show_learning_quote(self):
        q = self.app.quote_service.get_quote()
        text = f"{q.get('content', '')}\n\n知识点：{q.get('lesson', '')}\n行动：{q.get('action', '')}"
        self._copy_result_dialog("学习卡片", text)

    def _tool_icebreaker(self):
        scenes = ["最近有什么让你觉得值得记录的小事？", "你最近在学什么东西？", "这周有没有一件事让你觉得自己进步了？", "如果今天只推荐一条信息，你会推荐什么？"]
        self._copy_result_dialog("社交破冰", random.choice(scenes))

    def _tool_micro_task(self):
        tasks = ["清理 5 条无用收藏", "给一个关注主题添加关键词", "读一篇长文并写 3 句摘要", "整理明天第一件事", "把一个复杂问题写成检查清单"]
        self._copy_result_dialog("今日微任务", random.choice(tasks))

    def _tool_reduce_overthinking(self):
        worry = simpledialog.askstring("反内耗处理", "你现在最担心什么？")
        if not worry:
            return
        text = f"担心：{worry}\n可控部分：写下一个 10 分钟内能做的动作。\n不可控部分：标记为等待信息。\n下一步：现在只执行可控动作。"
        self._copy_result_dialog("反内耗处理", text)

    # ========== 回复助手 ==========

    REPLY_TEMPLATES = {
        "撩妹": [
            "你今天有点奇怪，奇怪地可爱。",
            "你是不是偷了什么东西？偷走了我的心。",
            "你知道你和星星的区别吗？星星在天上，你在我心里。",
            "我最近体重增加了，因为心里多了一个你。",
            "你笑起来的样子，比我见过的所有风景都好看。",
            "我想变成你的手机，每天被你捧在手心。",
            "你知道我为什么这么困吗？因为我为你神魂颠倒。",
            "你一定是我的 Sunshine，因为你照亮了我的世界。",
            "我想和你一起变老，但首先我想和你一起变胖。",
            "你今天看起来有点累，是不是在我脑海里跑了一整天？",
        ],
        "工作沟通": [
            "收到，我会尽快处理，预计今天内给您反馈。",
            "感谢提醒，我马上安排跟进，有进展第一时间同步。",
            "这个方案我觉得可以，我这边配合执行。",
            "我理解您的意思，我来整理一下，稍后发给您确认。",
            "好的，我先看一下具体情况，有问题再跟您沟通。",
            "这个需求我记下了，排期后告诉您。",
            "收到，我会在今天下班前完成。",
            "明白，我先做个初步方案，明天跟您对一下。",
        ],
        "朋友闲聊": [
            "哈哈，你太有才了！",
            "笑死，你怎么这么搞笑。",
            "确实，我也是这么想的。",
            "好久不见，最近怎么样？",
            "走起，好久没聚了，约一个！",
            "你这话说得太对了，深有同感。",
            "厉害了，你这是要上天啊。",
            "认真的吗？那我必须支持一下。",
            "你这个人，真的是让人无话可说。",
            "好的好的，听你的。",
        ],
        "道歉": [
            "不好意思，是我考虑不周，下次一定注意。",
            "真的很抱歉，给你添麻烦了。",
            "对不起，我错了，我会马上改正。",
            "抱歉，这个事情我确实做得不够好，我会改进。",
            "不好意思，让你久等了，我马上处理。",
            "抱歉打扰了，方便的时候回复我就好。",
            "这次是我疏忽了，以后一定避免。",
        ],
        "感谢": [
            "太感谢了，帮了我大忙！",
            "非常感谢你的帮忙，记在心里了。",
            "谢谢你，真的帮了我很多。",
            "太给力了，有你真好！",
            "感谢支持，改天请你吃饭！",
            "多谢多谢，下次有事找我。",
            "谢谢你耐心解答，学到很多。",
        ],
        "拒绝": [
            "不好意思，这次时间实在安排不开，下次一定参加。",
            "感谢邀请，但最近实在太忙了，下次再约。",
            "抱歉，这个事情我确实帮不上忙，不好意思。",
            "不好意思，已经有其他安排了，下次提前约。",
            "感谢好意，但我这次真的不太方便。",
            "抱歉，最近档期满了，下次一定。",
        ],
        "安慰": [
            "别太难过了，一切都会好起来的。",
            "没关系的，谁都有不顺的时候。",
            "辛苦了，你已经做得很好了。",
            "别担心，有我在呢。",
            "慢慢来，不着急，我等你。",
            "加油，我相信你可以的。",
            "没事的，这次不行还有下次。",
            "你已经很棒了，别给自己太大压力。",
        ],
        "表白": [
            "我喜欢你，认真的那种。",
            "我想了很久，还是想告诉你，我喜欢你。",
            "遇见你之后，我觉得每天都很有意义。",
            "我想和你在一起，可以吗？",
            "你是我见过最特别的人，我喜欢你。",
            "我对你不只是朋友的感觉，我想更进一步。",
        ],
    }

    def _show_reply_assistant(self):
        self._clear_content()
        self._switch_page("reply")
        self._set_status("回复助手")
        self._page_header("聊天回复助手", "#722ed1")

        tip = tk.Frame(self.content, bg=self.colors["bg"])
        tip.pack(fill=tk.X, padx=24, pady=(12, 0))
        tk.Label(tip, text="选择场景，一键复制回复内容到剪贴板，告别聊天尴尬。",
                 bg=self.colors["bg"], fg=self.colors["text_secondary"], font=("微软雅黑", 10)).pack(anchor=tk.W)

        wrapper = tk.Frame(self.content, bg=self.colors["bg"])
        wrapper.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)

        for idx, (scene, replies) in enumerate(self.REPLY_TEMPLATES.items()):
            card = tk.Frame(wrapper, bg="white", relief=tk.FLAT, bd=1,
                           highlightbackground=self.colors["border"], highlightthickness=1, padx=16, pady=14)
            card.grid(row=idx // 2, column=idx % 2, sticky=tk.NSEW, padx=8, pady=8)
            wrapper.columnconfigure(idx % 2, weight=1)

            tk.Label(card, text=scene, bg="white", fg=self.colors["text"],
                     font=("微软雅黑", 13, "bold")).pack(anchor=tk.W)
            tk.Label(card, text=f"{len(replies)} 条回复模板", bg="white",
                     fg=self.colors["text_secondary"], font=("微软雅黑", 9)).pack(anchor=tk.W, pady=(2, 8))

            btn_frame = tk.Frame(card, bg="white")
            btn_frame.pack(fill=tk.X)
            self._create_button(btn_frame, "随机一条", lambda s=scene: self._reply_random(s), "primary").pack(side=tk.LEFT, padx=2)
            self._create_button(btn_frame, "查看全部", lambda s=scene: self._reply_show_all(s), "secondary").pack(side=tk.LEFT, padx=2)

    def _reply_random(self, scene: str):
        reply = random.choice(self.REPLY_TEMPLATES[scene])
        self._copy_text(reply, f"{scene} 回复已复制")
        self._show_result_window(f"{scene} 回复", reply, "#722ed1")

    def _reply_show_all(self, scene: str):
        replies = self.REPLY_TEMPLATES[scene]
        win = tk.Toplevel(self)
        win.title(f"{scene} 回复模板")
        win.configure(bg=self.colors["bg"])
        self._center_window(win, 720, 560)

        header = tk.Frame(win, bg="#722ed1", height=72)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"{scene} 回复模板", bg="#722ed1", fg="white",
                 font=("微软雅黑", 17, "bold")).pack(anchor=tk.W, padx=22, pady=(12, 0))
        tk.Label(header, text="点击复制后可直接粘贴发送，重点回复放在卡片正文。", bg="#722ed1", fg="#f3e8ff",
                 font=("微软雅黑", 10)).pack(anchor=tk.W, padx=22, pady=(2, 0))

        frame = tk.Frame(win, bg=self.colors["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)
        canvas = tk.Canvas(frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.colors["bg"])
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for i, reply in enumerate(replies, 1):
            outer, row = self._create_soft_card(inner, padx=14, pady=12)
            outer.pack(fill=tk.X, pady=5, padx=4)
            tk.Label(row, text=f"模板 {i}", bg="white", fg="#722ed1",
                     font=("微软雅黑", 9, "bold")).pack(anchor=tk.W)
            tk.Label(row, text=reply, bg="white", fg=self.colors["text"],
                     font=("微软雅黑", 11, "bold" if i == 1 else "normal"), wraplength=540, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(5, 0))

            def copy_one(r=reply):
                self._copy_text(r, "回复已复制到剪贴板")

            self._create_button(row, "复制", copy_one, "secondary").pack(side=tk.RIGHT, padx=4)

    def _page_header(self, title: str, color: str):
        header = tk.Frame(self.content, bg=color, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=color, fg="white", font=("微软雅黑", 20, "bold")).pack(expand=True)

    def _render_article_cards(self, articles: list[dict], empty_text: str):
        frame = tk.Frame(self.content, bg=self.colors["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        if not articles:
            tk.Label(frame, text=empty_text, bg=self.colors["bg"], fg=self.colors["text_secondary"], font=("微软雅黑", 11)).pack(pady=50)
            return
        for a in articles[:60]:
            card = tk.Frame(frame, bg="white", relief=tk.FLAT, bd=1, highlightbackground=self.colors["border"], highlightthickness=1, padx=15, pady=12)
            card.pack(fill=tk.X, pady=5)
            tk.Label(card, text=a.get("title", ""), bg="white", fg=self.colors["text"], font=("微软雅黑", 11, "bold"), wraplength=780, justify=tk.LEFT).pack(anchor=tk.W)
            if a.get("summary"):
                tk.Label(card, text=a.get("summary", "")[:260], bg="white", fg=self.colors["text_secondary"], font=("微软雅黑", 9), wraplength=780, justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 0))
            bottom = tk.Frame(card, bg="white")
            bottom.pack(fill=tk.X, pady=(8, 0))
            meta = f"来源: {a.get('source_name', '')}  时间: {format_news_time(a.get('published_at') or a.get('collected_at'))}  重要度: {float(a.get('importance_score', 0.5)):.0%}"
            tk.Label(bottom, text=meta, bg="white", fg=self.colors["text_secondary"], font=("微软雅黑", 9)).pack(side=tk.LEFT)
            aid = a.get("id", 0)
            if aid:
                self._create_button(bottom, "阅读全文", lambda x=aid: self._show_article_detail(x), "primary").pack(side=tk.RIGHT, padx=2)

    # ========== 来源管理 ==========

    def _show_sources(self):
        self._clear_content()
        self._switch_page("source")
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

        actions = tk.Frame(self.content, bg=self.colors["bg"])
        actions.pack(fill=tk.X, padx=20, pady=(12, 0))
        self._create_button(actions, "添加 RSS 新闻源", lambda: self._add_source_dialog("rss"), "success").pack(side=tk.LEFT, padx=4)
        self._create_button(actions, "添加 API 新闻源", lambda: self._add_source_dialog("api"), "primary").pack(side=tk.LEFT, padx=4)
        self.source_check_btn = self._create_button(actions, "一键检测", self._health_check_sources, "warning")
        self.source_check_btn.pack(side=tk.LEFT, padx=4)
        self.source_summary_var = tk.StringVar(value="检测会真实访问 RSS/API 来源，用于发现失效源和错误原因。")
        tk.Label(
            self.content, textvariable=self.source_summary_var,
            bg=self.colors["bg"], fg=self.colors["text_secondary"],
            font=("微软雅黑", 9), anchor=tk.W
        ).pack(fill=tk.X, padx=25, pady=(8, 0))

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

    def _add_source_dialog(self, type_: str):
        name = simpledialog.askstring("添加来源", "来源名称：")
        if not name:
            return
        category = simpledialog.askstring("添加来源", "分类：news/tech/hot/policy/security", initialvalue="news") or "news"
        url = simpledialog.askstring("添加来源", "RSS 或 API 地址：")
        if not url:
            return
        self.app.source_mgr.create_source(name, type_, category, url)
        messagebox.showinfo("成功", "来源已添加，后续一键采集会自动尝试读取")
        self._show_sources()

    def _health_check_sources(self):
        """一键检测所有来源可用性."""
        from news_intelligence_desktop.connectors.news_rss import RssConnector
        import threading

        sources = self.app.source_mgr.list_sources()
        self._set_status(f"正在后台检测 {len(sources)} 个来源...")
        if hasattr(self, "source_summary_var"):
            self.source_summary_var.set(f"检测中：共 {len(sources)} 个来源，请稍候。")
        if hasattr(self, "source_check_btn"):
            self.source_check_btn.configure(state=tk.DISABLED, text="检测中...")

        results = {"ok": 0, "fail": 0, "details": []}
        rss = RssConnector()
        lock = threading.Lock()

        def check_one(src):
            name = src.get("name", "")
            url = src.get("url", "")
            stype = src.get("type", "")
            status = "跳过"
            err = "非RSS/API类型"
            if stype == "rss" and url:
                result = rss.fetch_feed(url, name)
                if result.ok:
                    status, err = "正常", ""
                else:
                    status, err = "失败", result.error[:50]
            elif stype == "api" and url:
                from news_intelligence_desktop.connectors.generic_api import GenericApiCaller
                caller = GenericApiCaller()
                data = caller.call(url)
                if data.get("ok"):
                    status, err = "正常", ""
                else:
                    status, err = "失败", data.get("error", "")[:50]
            with lock:
                if status == "正常":
                    results["ok"] += 1
                elif status == "失败":
                    results["fail"] += 1
                results["details"].append((name, status, err))

        def do_check():
            threads = []
            for src in sources:
                t = threading.Thread(target=check_one, args=(src,))
                t.start()
                threads.append(t)
            for t in threads:
                t.join(timeout=20)
            self.after(0, lambda: self._on_health_check_sources_done(results))

        threading.Thread(target=do_check, daemon=True).start()

    def _on_health_check_sources_done(self, results):
        if hasattr(self, "source_check_btn"):
            self.source_check_btn.configure(state=tk.NORMAL, text="一键检测")

        msg = f"检测完成：{results['ok']} 个正常，{results['fail']} 个失败\n\n"
        for name, status, err in results["details"]:
            if status != "正常":
                msg += f"  {name}: {status} {err}\n"
        if results["fail"] == 0:
            msg += "所有来源均可用"
        if hasattr(self, "source_summary_var"):
            self.source_summary_var.set(msg.replace("\n\n", "；").replace("\n", "；")[:240])
        self._set_status("来源检测完成")
        messagebox.showinfo("检测结果", msg)

    # ========== 数据采集 ==========

    def _start_collect(self):
        """开始采集."""
        if self.app.personal.privacy_enabled():
            self._set_status("隐私模式已开启：采集已暂停")
            messagebox.showinfo("采集暂停", "当前处于隐私模式。\n\n联网采集已暂停，关闭隐私模式后可以继续更新天气、新闻、热搜和外置来源。")
            return
        self.collect_btn.configure(state=tk.DISABLED, text="采集中...")
        self._set_status("正在采集数据...")
        self._collecting = True
        self._pulse_collect_status(0)

        def do_collect():
            try:
                result = self.app.collect_all()
                self.after(0, lambda: self._on_collect_done(result))
            except Exception as e:
                self.after(0, lambda: self._on_collect_error(str(e)))

        threading.Thread(target=do_collect, daemon=True).start()

    def _on_collect_done(self, result):
        """采集完成."""
        self._collecting = False
        self.collect_btn.configure(state=tk.NORMAL, text="一键采集数据")
        if result.get("privacy_paused"):
            self._set_status("隐私模式已开启：采集已暂停")
            messagebox.showinfo("采集暂停", "当前处于隐私模式，已跳过所有联网请求。")
            return
        msg = (f"采集完成: 天气{result.get('weather',0)} "
               f"地震{result.get('earthquake',0)} "
               f"新闻{result.get('news',0)} "
               f"热点{result.get('hot',0)} "
               f"技术{result.get('tech',0)} "
               f"语录{result.get('quote',0)} "
               f"外置{result.get('custom',0)}")
        self._set_status(msg)
        if result.get("errors"):
            messagebox.showwarning("采集警告", f"部分采集失败:\n" + "\n".join(result["errors"]))
        else:
            messagebox.showinfo("采集完成", msg)

    def _on_collect_error(self, error):
        """采集失败."""
        self._collecting = False
        self.collect_btn.configure(state=tk.NORMAL, text="一键采集数据")
        self._set_status("采集失败")
        messagebox.showerror("采集错误", error)

    def _pulse_collect_status(self, step: int):
        if not getattr(self, "_collecting", False):
            return
        dots = "." * ((step % 3) + 1)
        self._set_status(f"后台静默采集中{dots} 可继续浏览已缓存内容")
        self.after(900, lambda: self._pulse_collect_status(step + 1))


def run_gui(data_dir: Path | None = None) -> int:
    """启动图形界面."""
    settings = AppSettings.load(data_dir)
    app_service = AppService(settings)
    app_service.initialize()

    app = App(app_service)
    app.mainloop()
    return 0
