from __future__ import annotations

import json
import os
import sys
from datetime import date


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    
    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith('_'):
                setattr(cls, attr, '')


def supports_color() -> bool:
    """Check if terminal supports color."""
    if os.environ.get('NO_COLOR'):
        return False
    if not hasattr(sys.stdout, 'isatty'):
        return False
    if not sys.stdout.isatty():
        return False
    return True


if not supports_color():
    Colors.disable()


class ConsoleUI:
    def __init__(self, app_service):
        self.app = app_service
        self.running = True
        self.page_size = 10
        self.current_page = 0

    def run(self) -> int:
        self._print_header()
        while self.running:
            self._main_menu()
        return 0

    def _print_header(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  News Intelligence Desktop{Colors.RESET}")
        print(f"{Colors.BOLD}  个人每日信息中枢与 API 工具箱{Colors.RESET}")
        print(f"{Colors.DIM}  输入 h 显示帮助，q 退出{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    def _main_menu(self) -> None:
        print(f"{Colors.BOLD}┌─────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}1{Colors.RESET}. 首页信息中枢                    {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}2{Colors.RESET}. 天气预报                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}3{Colors.RESET}. 地震动态                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}4{Colors.RESET}. 新闻资讯                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}5{Colors.RESET}. 热点报告                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}6{Colors.RESET}. 猎奇内容                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}7{Colors.RESET}. 技术变化                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}8{Colors.RESET}. 每日语录                        {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}9{Colors.RESET}. API 工具箱                      {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}10{Colors.RESET}. 特别收藏                       {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}11{Colors.RESET}. 个人中心                       {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}12{Colors.RESET}. 来源管理                       {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}13{Colors.RESET}. 搜索                           {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}14{Colors.RESET}. 数据采集                       {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}│{Colors.RESET}  {Colors.CYAN}0{Colors.RESET}. 退出                           {Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.BOLD}└─────────────────────────────────────┘{Colors.RESET}")
        
        choice = input(f"\n{Colors.YELLOW}请选择 [0-14]: {Colors.RESET}").strip()
        
        handlers = {
            "1": self._home, "2": self._weather, "3": self._earthquake,
            "4": self._news, "5": self._hot_report, "6": self._oddity,
            "7": self._tech_changes, "8": self._daily_quote, "9": self._api_toolbox,
            "10": self._special_favorites, "11": self._personal, "12": self._sources,
            "13": self._search_menu, "14": self._collect_menu,
            "0": self._exit, "q": self._exit, "h": self._help,
        }
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print(f"{Colors.RED}无效选择，请重新输入。{Colors.RESET}\n")

    def _help(self) -> None:
        print(f"\n{Colors.BOLD}--- 帮助 ---{Colors.RESET}")
        print(f"  {Colors.CYAN}h{Colors.RESET} - 显示帮助")
        print(f"  {Colors.CYAN}q{Colors.RESET} - 退出程序")
        print(f"  {Colors.CYAN}1-14{Colors.RESET} - 选择功能菜单")
        print(f"  {Colors.CYAN}n/p{Colors.RESET} - 下一页/上一页（在列表页面中）")
        print(f"  {Colors.CYAN}d <id>{Colors.RESET} - 查看文章详情（在新闻列表中）")
        print(f"  {Colors.CYAN}f <id>{Colors.RESET} - 收藏文章")
        print(f"  {Colors.CYAN}r <id>{Colors.RESET} - 标记文章已读")
        print()

    def _home(self) -> None:
        dash = self.app.home_dashboard()
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}  {dash['title']}{Colors.RESET}")
        if dash.get("privacy_mode"):
            print(f"  {Colors.YELLOW}[隐私模式已开启]{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        
        for card in dash["cards"]:
            icon = self._card_icon(card["name"])
            color = self._card_color(card["name"])
            print(f"\n{color}{Colors.BOLD}{icon} {card['name']}{Colors.RESET}")
            print(f"   {Colors.DIM}{card['summary']}{Colors.RESET}")
            
            if card.get("quote"):
                q = card["quote"]
                print(f"   {Colors.GREEN}── {q.get('style_label', '语录')}: {q['content']}{Colors.RESET}")
            
            for item in card.get("items", [])[:3]:
                print(f"   {Colors.WHITE}• {item['title']}{Colors.RESET}")
        
        if dash.get("special_tabs"):
            print(f"\n{Colors.DIM}{'─'*40}{Colors.RESET}")
            print(f"{Colors.MAGENTA}特别收藏页签:{Colors.RESET}")
            for tab in dash["special_tabs"]:
                print(f"   [{Colors.CYAN}{tab['id']}{Colors.RESET}] {tab['name']} ({tab['match_domain']})")
        
        print()

    def _card_icon(self, name: str) -> str:
        icons = {
            "今日总览": "[总]", "技术变化": "[技]", "重要新闻": "[新]",
            "政策变化": "[政]", "本地事件": "[本]", "热点吃瓜": "[热]",
            "天气地震": "[天]", "每日语录": "[语]",
        }
        return icons.get(name, "[·]")

    def _card_color(self, name: str) -> str:
        colors = {
            "今日总览": Colors.CYAN, "技术变化": Colors.BLUE, "重要新闻": Colors.GREEN,
            "政策变化": Colors.YELLOW, "本地事件": Colors.MAGENTA, "热点吃瓜": Colors.RED,
            "天气地震": Colors.CYAN, "每日语录": Colors.GREEN,
        }
        return colors.get(name, Colors.WHITE)

    def _weather(self) -> None:
        forecasts = []
        with self.app.repo.db.connect() as conn:
            forecasts = [dict(r) for r in conn.execute("SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7")]
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 天气预报 ---{Colors.RESET}")
        if not forecasts:
            print(f"{Colors.DIM}暂无天气数据，等待采集。{Colors.RESET}")
        else:
            for f in forecasts:
                temp_high = f.get('temp_high', '--')
                temp_low = f.get('temp_low', '--')
                desc = f.get('description', '')
                print(f"  {Colors.WHITE}{f['forecast_date']}{Colors.RESET}  "
                      f"高温:{Colors.RED}{temp_high}°C{Colors.RESET}  "
                      f"低温:{Colors.BLUE}{temp_low}°C{Colors.RESET}  {desc}")
        print()

    def _earthquake(self) -> None:
        with self.app.repo.db.connect() as conn:
            events = [dict(r) for r in conn.execute("SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 10")]
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 地震动态 ---{Colors.RESET}")
        if not events:
            print(f"{Colors.DIM}暂无地震数据，等待采集。{Colors.RESET}")
        else:
            for e in events:
                mag = e['magnitude']
                mag_color = Colors.RED if mag >= 6 else Colors.YELLOW if mag >= 5 else Colors.WHITE
                print(f"  {mag_color}M{mag}{Colors.RESET}  {e['place']}  {Colors.DIM}{e['event_time'][:16]}{Colors.RESET}")
        print()

    def _news(self, page: int = 0) -> None:
        articles = self.app.repo.list_articles(limit=100)
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 新闻资讯 ---{Colors.RESET}")
        
        cats = {
            "news": ("新闻", Colors.GREEN), "tech": ("技术", Colors.BLUE),
            "policy": ("政策", Colors.YELLOW), "hot": ("热点", Colors.RED),
            "local": ("本地", Colors.MAGENTA), "accident": ("事故", Colors.RED),
        }
        
        total = 0
        for cat, (label, color) in cats.items():
            items = [a for a in articles if a["category"] == cat]
            if items:
                print(f"\n  {color}{Colors.BOLD}[{label}]{Colors.RESET}")
                for a in items[:5]:
                    state = self.app.personal.get_reading_state("article", a["id"])
                    mark = f"{Colors.GREEN}✓{Colors.RESET}" if state == "read" else f"{Colors.YELLOW}☆{Colors.RESET}" if state == "favorite" else f"{Colors.DIM}○{Colors.RESET}"
                    print(f"    {mark} {Colors.CYAN}[{a['id']}]{Colors.RESET} {a['title']}")
                    print(f"      {Colors.DIM}{a['source_name']}  {a.get('published_at', '')[:16]}{Colors.RESET}")
                    total += 1
        
        print(f"\n{Colors.DIM}共 {total} 条新闻。输入 d <id> 查看详情，f <id> 收藏{Colors.RESET}")
        
        cmd = input(f"{Colors.YELLOW}> {Colors.RESET}").strip()
        if cmd.startswith("d "):
            try:
                aid = int(cmd[2:])
                self._article_detail(aid)
            except ValueError:
                print(f"{Colors.RED}无效 ID{Colors.RESET}")
        elif cmd.startswith("f "):
            try:
                aid = int(cmd[2:])
                self.app.personal.set_reading_state("article", aid, "favorite")
                print(f"{Colors.GREEN}已收藏文章 {aid}{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}无效 ID{Colors.RESET}")
        print()

    def _article_detail(self, article_id: int) -> None:
        article = self.app.repo.get_article(article_id)
        if not article:
            print(f"{Colors.RED}文章不存在{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}{'─'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{article['title']}{Colors.RESET}")
        print(f"{Colors.DIM}来源: {article['source_name']} | 分类: {article['category']}{Colors.RESET}")
        print(f"{Colors.DIM}链接: {article['url']}{Colors.RESET}")
        print(f"{Colors.DIM}采集时间: {article.get('collected_at', '')}{Colors.RESET}")
        
        cred = self.app.credibility.explain("article", article_id)
        print(f"可信度: {Colors.GREEN}{cred.get('score', 0):.1f}{Colors.RESET} - {cred.get('explanation', '')}")
        
        if article.get("summary"):
            print(f"\n{Colors.WHITE}{article['summary']}{Colors.RESET}")
        
        if article.get("content"):
            print(f"\n{Colors.DIM}{article['content'][:500]}{Colors.RESET}")
        
        state = self.app.personal.get_reading_state("article", article_id)
        print(f"\n状态: {state}")
        print(f"{Colors.DIM}操作: r=已读 f=收藏 l=稍后看 q=返回{Colors.RESET}")
        
        cmd = input(f"{Colors.YELLOW}> {Colors.RESET}").strip()
        if cmd == "r":
            self.app.personal.set_reading_state("article", article_id, "read")
            print(f"{Colors.GREEN}已标记已读{Colors.RESET}")
        elif cmd == "f":
            self.app.personal.set_reading_state("article", article_id, "favorite")
            print(f"{Colors.GREEN}已收藏{Colors.RESET}")
        elif cmd == "l":
            self.app.personal.set_reading_state("article", article_id, "read_later")
            print(f"{Colors.GREEN}已添加到稍后看{Colors.RESET}")
        
        print(f"{Colors.BOLD}{'─'*60}{Colors.RESET}\n")

    def _hot_report(self) -> None:
        articles = self.app.repo.list_articles(category="hot", limit=20)
        print(f"\n{Colors.BOLD}{Colors.RED}--- 热点报告 ---{Colors.RESET}")
        if not articles:
            print(f"{Colors.DIM}暂无热点数据。{Colors.RESET}")
        else:
            for i, a in enumerate(articles[:10], 1):
                print(f"  {Colors.CYAN}{i}.{Colors.RESET} {a['title']}")
                if a.get("summary"):
                    print(f"     {Colors.DIM}{a['summary'][:80]}{Colors.RESET}")
        print()

    def _oddity(self) -> None:
        articles = [a for a in self.app.repo.list_articles(limit=50) if a.get("category") in ("oddity", "entertainment")]
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 猎奇内容 ---{Colors.RESET}")
        if not articles:
            print(f"{Colors.DIM}暂无猎奇内容。{Colors.RESET}")
        else:
            for a in articles[:10]:
                cred = self.app.credibility.explain("article", a["id"])
                print(f"  {a['title']}")
                print(f"    可信度: {Colors.GREEN}{cred.get('score', 0):.1f}{Colors.RESET}  {Colors.DIM}{cred.get('explanation', '')[:40]}{Colors.RESET}")
        print()

    def _tech_changes(self) -> None:
        changes = self.app.tech_service.list_changes(limit=15)
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- 技术变化 ---{Colors.RESET}")
        if not changes:
            print(f"{Colors.DIM}暂无技术变化，等待采集或手动添加。{Colors.RESET}")
        else:
            for c in changes:
                change_type = c.get('change_type', '')
                type_color = Colors.RED if 'cve' in change_type else Colors.YELLOW if 'breaking' in change_type else Colors.GREEN
                print(f"  {type_color}[{change_type}]{Colors.RESET} {c['title']}")
                print(f"    {Colors.DIM}{c.get('source_name', '')}  {c.get('published_at', '')[:16]}{Colors.RESET}")
        print()

    def _daily_quote(self) -> None:
        q = self.app.quote_service.get_home_quote()
        print(f"\n{Colors.BOLD}{Colors.GREEN}--- 每日语录 ({q.get('style_label', '')}) ---{Colors.RESET}")
        print(f"\n  {Colors.GREEN}「{q['content']}」{Colors.RESET}")
        if q.get("author"):
            print(f"  {Colors.DIM}—— {q['author']}{Colors.RESET}")
        print(f"\n  {Colors.DIM}风格选择: {', '.join(s['label'] for s in self.app.quote_service.list_styles())}{Colors.RESET}")
        print()

    def _api_toolbox(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- API 工具箱 ---{Colors.RESET}")
        categories = self.app.api_service.list_categories()
        print(f"  {Colors.DIM}分类: {', '.join(categories)}{Colors.RESET}")
        
        apis = self.app.api_service.list_apis()
        for api in apis[:15]:
            status_icon = f"{Colors.GREEN}●{Colors.RESET}" if api["status"] == "enabled" else f"{Colors.YELLOW}○{Colors.RESET}" if api["status"] == "needs_config" else f"{Colors.DIM}◌{Colors.RESET}"
            print(f"  {status_icon} [{Colors.CYAN}{api['id']}{Colors.RESET}] {api['name']}  "
                  f"({Colors.DIM}{api['provider']}/{api['category']}{Colors.RESET})  "
                  f"{api['status']}")
        
        print(f"\n  {Colors.DIM}共 {len(apis)} 个 API{Colors.RESET}")
        print()

    def _special_favorites(self) -> None:
        tabs = self.app.personal.list_special_tabs()
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- 特别收藏 ---{Colors.RESET}")
        if not tabs:
            print(f"{Colors.DIM}暂无特别收藏，使用命令添加:{Colors.RESET}")
            print(f"  {Colors.CYAN}python3 -m news_intelligence_desktop.app.main add-special <名称> <URL>{Colors.RESET}")
        else:
            for tab in tabs:
                items = self.app.personal.special_tab_articles(tab["id"])
                print(f"\n  [{Colors.CYAN}{tab['id']}{Colors.RESET}] {tab['name']}  "
                      f"({Colors.DIM}{tab['match_domain']}{Colors.RESET})  "
                      f"匹配 {Colors.GREEN}{len(items)}{Colors.RESET} 条")
                for item in items[:3]:
                    print(f"    {Colors.WHITE}• {item['title']}{Colors.RESET}")
        print()

    def _personal(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 个人中心 ---{Colors.RESET}")
        favorites = self.app.personal.list_collection("favorite")
        read_later = self.app.personal.list_collection("read_later")
        watchlist = self.app.personal.list_watchlist()
        privacy = self.app.personal.privacy_enabled()
        
        print(f"  收藏: {Colors.GREEN}{len(favorites)}{Colors.RESET} 条")
        print(f"  稍后看: {Colors.YELLOW}{len(read_later)}{Colors.RESET} 条")
        print(f"  关注清单: {Colors.CYAN}{len(watchlist)}{Colors.RESET} 项")
        print(f"  隐私模式: {Colors.RED if privacy else Colors.GREEN}{'开启' if privacy else '关闭'}{Colors.RESET}")
        
        if favorites:
            print(f"\n  {Colors.BOLD}最近收藏:{Colors.RESET}")
            for a in favorites[:5]:
                print(f"    {Colors.YELLOW}☆{Colors.RESET} {a['title']}")
        print()

    def _sources(self) -> None:
        sources = self.app.source_mgr.list_sources()
        health = self.app.source_health.get_health()
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 来源管理 ---{Colors.RESET}")
        
        health_map = {h["id"]: h for h in health}
        for src in sources:
            icon = f"{Colors.GREEN}●{Colors.RESET}" if src["enabled"] else f"{Colors.DIM}○{Colors.RESET}"
            h = health_map.get(src["id"], {})
            status = ""
            if h.get("paused"):
                status = f" {Colors.RED}[已暂停]{Colors.RESET}"
            elif h.get("failure_count", 0) > 0:
                status = f" {Colors.YELLOW}[失败{h['failure_count']}次]{Colors.RESET}"
            print(f"  {icon} [{Colors.CYAN}{src['id']}{Colors.RESET}] {src['name']}  "
                  f"({Colors.DIM}{src['type']}/{src['category']}{Colors.RESET}){status}")
        print()

    def _search_menu(self) -> None:
        query = input(f"\n{Colors.YELLOW}搜索关键词: {Colors.RESET}").strip()
        if not query:
            return
        
        results = self.app.search(query)
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- 搜索结果: {query} ---{Colors.RESET}")
        
        if not results:
            print(f"{Colors.DIM}未找到匹配内容。{Colors.RESET}")
        else:
            for i, r in enumerate(results[:10], 1):
                print(f"  {Colors.CYAN}{i}.{Colors.RESET} {r.get('title', '')}")
                if r.get("snippet"):
                    print(f"     {Colors.DIM}{r['snippet'][:80]}{Colors.RESET}")
        print()

    def _collect_menu(self) -> None:
        print(f"\n{Colors.YELLOW}正在采集数据...{Colors.RESET}")
        result = self.app.collect_all()
        print(f"\n{Colors.GREEN}采集完成:{Colors.RESET}")
        print(f"  天气: {result['weather']} 条")
        print(f"  地震: {result['earthquake']} 条")
        print(f"  新闻: {result['news']} 条")
        print(f"  热点: {result['hot']} 条")
        if result.get("errors"):
            print(f"  {Colors.RED}错误:{Colors.RESET}")
            for err in result["errors"]:
                print(f"    - {err}")
        print()

    def _exit(self) -> None:
        self.running = False
        print(f"\n{Colors.GREEN}再见！{Colors.RESET}\n")
