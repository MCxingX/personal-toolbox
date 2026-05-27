from __future__ import annotations

import json
from datetime import date


class ConsoleUI:
    def __init__(self, app_service):
        self.app = app_service
        self.running = True

    def run(self) -> int:
        print("\n=== News Intelligence Desktop ===")
        print("个人每日信息中枢与 API 工具箱\n")
        while self.running:
            self._main_menu()
        return 0

    def _main_menu(self) -> None:
        print("┌─────────────────────────────────────┐")
        print("│  1. 首页信息中枢                      │")
        print("│  2. 天气预报                          │")
        print("│  3. 地震动态                          │")
        print("│  4. 新闻资讯                          │")
        print("│  5. 热点报告                          │")
        print("│  6. 猎奇内容                          │")
        print("│  7. 技术变化                          │")
        print("│  8. 每日语录                          │")
        print("│  9. API 工具箱                        │")
        print("│ 10. 特别收藏                          │")
        print("│ 11. 个人中心                          │")
        print("│ 12. 来源管理                          │")
        print("│  0. 退出                              │")
        print("└─────────────────────────────────────┘")
        choice = input("\n请选择 [0-12]: ").strip()
        handlers = {
            "1": self._home, "2": self._weather, "3": self._earthquake,
            "4": self._news, "5": self._hot_report, "6": self._oddity,
            "7": self._tech_changes, "8": self._daily_quote, "9": self._api_toolbox,
            "10": self._special_favorites, "11": self._personal, "12": self._sources,
            "0": self._exit,
        }
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print("无效选择，请重新输入。\n")

    def _home(self) -> None:
        dash = self.app.home_dashboard()
        print(f"\n{'='*60}")
        print(f"  {dash['title']}")
        if dash.get("privacy_mode"):
            print("  [隐私模式已开启]")
        print(f"{'='*60}")
        for card in dash["cards"]:
            icon = self._card_icon(card["name"])
            print(f"\n{icon} {card['name']}")
            print(f"   {card['summary']}")
            if card.get("quote"):
                q = card["quote"]
                print(f"   ── {q.get('style_label', '语录')}: {q['content']}")
            for item in card.get("items", [])[:3]:
                print(f"   • {item['title']}")
        if dash.get("special_tabs"):
            print(f"\n{'─'*40}")
            print("特别收藏页签:")
            for tab in dash["special_tabs"]:
                print(f"   [{tab['id']}] {tab['name']} ({tab['match_domain']})")
        print()

    def _card_icon(self, name: str) -> str:
        icons = {"今日总览": "[总]", "技术变化": "[技]", "重要新闻": "[新]", "政策变化": "[政]", "本地事件": "[本]", "热点吃瓜": "[热]", "天气地震": "[天]", "每日语录": "[语]"}
        return icons.get(name, "[·]")

    def _weather(self) -> None:
        forecasts = []
        with self.app.repo.db.connect() as conn:
            forecasts = [dict(r) for r in conn.execute("SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7")]
        print("\n--- 天气预报 ---")
        if not forecasts:
            print("暂无天气数据，等待采集。")
        else:
            for f in forecasts:
                print(f"  {f['forecast_date']}  高温:{f['temp_high']}°C  低温:{f['temp_low']}°C  {f['description']}")
        print()

    def _earthquake(self) -> None:
        with self.app.repo.db.connect() as conn:
            events = [dict(r) for r in conn.execute("SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 10")]
        print("\n--- 地震动态 ---")
        if not events:
            print("暂无地震数据，等待采集。")
        else:
            for e in events:
                print(f"  M{e['magnitude']}  {e['place']}  {e['event_time'][:16]}")
        print()

    def _news(self) -> None:
        articles = self.app.repo.list_articles(limit=20)
        print("\n--- 新闻资讯 ---")
        cats = {"news": "新闻", "tech": "技术", "policy": "政策", "hot": "热点", "local": "本地", "accident": "事故"}
        for cat, label in cats.items():
            items = [a for a in articles if a["category"] == cat]
            if items:
                print(f"\n  [{label}]")
                for a in items[:5]:
                    state = self.app.personal.get_reading_state("article", a["id"])
                    mark = "✓" if state == "read" else "☆" if state == "favorite" else "○"
                    print(f"    {mark} {a['title']}")
                    print(f"      {a['source_name']}  {a.get('published_at', '')[:16]}")
        print()

    def _hot_report(self) -> None:
        articles = self.app.repo.list_articles(category="hot", limit=20)
        print("\n--- 热点报告 ---")
        if not articles:
            print("暂无热点数据。")
        else:
            for i, a in enumerate(articles[:10], 1):
                print(f"  {i}. {a['title']}")
                if a.get("summary"):
                    print(f"     {a['summary'][:80]}")
        print()

    def _oddity(self) -> None:
        articles = [a for a in self.app.repo.list_articles(limit=50) if a.get("category") in ("oddity", "entertainment")]
        print("\n--- 猎奇内容 ---")
        if not articles:
            print("暂无猎奇内容。")
        else:
            for a in articles[:10]:
                cred = self.app.credibility.explain("article", a["id"])
                print(f"  {a['title']}")
                print(f"    可信度: {cred.get('score', 0):.1f}  {cred.get('explanation', '')[:40]}")
        print()

    def _tech_changes(self) -> None:
        changes = self.app.tech_service.list_changes(limit=15)
        print("\n--- 技术变化 ---")
        if not changes:
            print("暂无技术变化，等待采集或手动添加。")
        else:
            for c in changes:
                print(f"  [{c.get('change_type', '')}] {c['title']}")
                print(f"    {c.get('source_name', '')}  {c.get('published_at', '')[:16]}")
        print()

    def _daily_quote(self) -> None:
        q = self.app.quote_service.get_home_quote()
        print(f"\n--- 每日语录 ({q.get('style_label', '')}) ---")
        print(f"\n  「{q['content']}」")
        if q.get("author"):
            print(f"  —— {q['author']}")
        print(f"\n  风格选择: {', '.join(s['label'] for s in self.app.quote_service.list_styles())}")
        print()

    def _api_toolbox(self) -> None:
        print("\n--- API 工具箱 ---")
        categories = self.app.api_service.list_categories()
        print(f"  分类: {', '.join(categories)}")
        apis = self.app.api_service.list_apis()
        for api in apis[:15]:
            status_icon = "●" if api["status"] == "enabled" else "○" if api["status"] == "needs_config" else "◌"
            print(f"  {status_icon} [{api['id']}] {api['name']}  ({api['provider']}/{api['category']})  {api['status']}")
        print(f"\n  共 {len(apis)} 个 API")
        print()

    def _special_favorites(self) -> None:
        tabs = self.app.personal.list_special_tabs()
        print("\n--- 特别收藏 ---")
        if not tabs:
            print("暂无特别收藏，使用命令添加:")
            print("  python3 -m news_intelligence_desktop.app.main add-special <名称> <URL>")
        else:
            for tab in tabs:
                items = self.app.personal.special_tab_articles(tab["id"])
                print(f"\n  [{tab['id']}] {tab['name']}  ({tab['match_domain']})  匹配 {len(items)} 条")
                for item in items[:3]:
                    print(f"    • {item['title']}")
        print()

    def _personal(self) -> None:
        print("\n--- 个人中心 ---")
        favorites = self.app.personal.list_collection("favorite")
        read_later = self.app.personal.list_collection("read_later")
        watchlist = self.app.personal.list_watchlist()
        privacy = self.app.personal.privacy_enabled()
        print(f"  收藏: {len(favorites)} 条")
        print(f"  稍后看: {len(read_later)} 条")
        print(f"  关注清单: {len(watchlist)} 项")
        print(f"  隐私模式: {'开启' if privacy else '关闭'}")
        if favorites:
            print("\n  最近收藏:")
            for a in favorites[:5]:
                print(f"    ☆ {a['title']}")
        print()

    def _sources(self) -> None:
        sources = self.app.source_mgr.list_sources()
        health = self.app.source_health.get_health()
        print("\n--- 来源管理 ---")
        health_map = {h["id"]: h for h in health}
        for src in sources:
            icon = "●" if src["enabled"] else "○"
            h = health_map.get(src["id"], {})
            status = ""
            if h.get("paused"):
                status = " [已暂停]"
            elif h.get("failure_count", 0) > 0:
                status = f" [失败{h['failure_count']}次]"
            print(f"  {icon} [{src['id']}] {src['name']}  ({src['type']}/{src['category']}){status}")
        print()

    def _exit(self) -> None:
        self.running = False
        print("再见！")
