from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.services.app_service import AppService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="news-intelligence", description="News Intelligence Desktop - 个人每日信息中枢")
    parser.add_argument("--data-dir", type=Path, help="Override data directory")
    parser.add_argument("--console", action="store_true", help="Run console dashboard")
    parser.add_argument("--collect", action="store_true", help="Run data collection")
    parser.add_argument("--json", action="store_true", help="JSON output")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add-special", help="Add special favorite web tab")
    p.add_argument("name"); p.add_argument("url")
    p.add_argument("--mode", default="domain", choices=["domain", "exact", "path_prefix", "custom_contains"])
    p.add_argument("--path", default=""); p.add_argument("--json", action="store_true")

    p = sub.add_parser("search", help="Search local content")
    p.add_argument("query"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("brief", help="Generate morning/evening brief")
    p.add_argument("type", choices=["晨报", "晚报"]); p.add_argument("--json", action="store_true")

    p = sub.add_parser("export-article", help="Export article")
    p.add_argument("article_id", type=int); p.add_argument("output", type=Path)
    p.add_argument("--format", default="markdown", choices=["markdown", "html", "json", "csv"]); p.add_argument("--json", action="store_true")

    p = sub.add_parser("backup", help="Create backup")
    p.add_argument("output", type=Path); p.add_argument("--json", action="store_true")

    p = sub.add_parser("privacy", help="Toggle privacy mode")
    p.add_argument("state", choices=["on", "off", "status"]); p.add_argument("--json", action="store_true")

    p = sub.add_parser("collect", help="Run data collection")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("add-watchlist", help="Add watchlist item")
    p.add_argument("name"); p.add_argument("type", choices=["keyword", "company", "tech_stack", "city", "policy_topic", "person"])
    p.add_argument("keywords", nargs="+"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("add-quote", help="Add daily quote")
    p.add_argument("content"); p.add_argument("--author", default=""); p.add_argument("--style", default="encourage")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list-apis", help="List API catalog")
    p.add_argument("--category"); p.add_argument("--provider"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("source-health", help="Show source health")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("notifications", help="List notifications")
    p.add_argument("--status"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("read", help="Mark article as read")
    p.add_argument("article_id", type=int); p.add_argument("--json", action="store_true")

    p = sub.add_parser("favorite", help="Mark article as favorite")
    p.add_argument("article_id", type=int); p.add_argument("--json", action="store_true")

    p = sub.add_parser("collection", help="List collection")
    p.add_argument("type", choices=["favorite", "read_later"]); p.add_argument("--json", action="store_true")

    p = sub.add_parser("rebuild-index", help="Rebuild search index")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("add-source", help="Add data source")
    p.add_argument("name"); p.add_argument("type", choices=["api", "rss", "web"])
    p.add_argument("category"); p.add_argument("url")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list-feeds", help="List available RSS feeds")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("tech-detect", help="Detect tech changes from articles")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("policy-add", help="Add a policy item")
    p.add_argument("title"); p.add_argument("--issuer", default=""); p.add_argument("--region", default="")
    p.add_argument("--category", default=""); p.add_argument("--summary", default="")
    p.add_argument("--source-url", default=""); p.add_argument("--json", action="store_true")

    p = sub.add_parser("policy-list", help="List policy items")
    p.add_argument("--region"); p.add_argument("--category"); p.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = AppSettings.load(data_dir=args.data_dir)
    app = AppService(settings)
    app.initialize()

    if args.collect:
        result = app.collect_all()
        _out(args, {"message": f"采集完成: weather={result['weather']}, earthquake={result['earthquake']}, news={result['news']}, hot={result['hot']}", **result})
        return 0

    if args.command:
        return _dispatch(app, args)

    if args.console:
        from news_intelligence_desktop.ui.console import ConsoleUI
        return ConsoleUI(app).run()

    dash = app.home_dashboard()
    if args.json:
        print(json.dumps(dash, ensure_ascii=False, indent=2))
    else:
        print(dash["title"])
        for card in dash["cards"]:
            print(f"  [{card['name']}] {card['summary']}")
    return 0


def _dispatch(app: AppService, args: argparse.Namespace) -> int:
    cmd = args.command
    if cmd == "add-special":
        fid = app.personal.add_special_favorite(args.name, args.url, args.mode, args.path)
        count = len(app.personal.special_tab_articles(fid))
        _out(args, {"message": f"已创建特别收藏：{args.name}，匹配 {count} 条", "id": fid, "count": count})
    elif cmd == "search":
        results = app.search(args.query)
        _out(args, {"message": f"搜索完成：{len(results)} 条结果", "results": results})
    elif cmd == "brief":
        brief = app.generate_brief(args.type)
        _out(args, {"message": f"已生成{args.type}：{brief['title']}", "brief": brief})
    elif cmd == "export-article":
        out = app.export_article(args.article_id, args.output, args.format)
        _out(args, {"message": f"已导出：{out}", "output": str(out)})
    elif cmd == "backup":
        out = app.create_backup(args.output)
        _out(args, {"message": f"已备份：{out}", "output": str(out)})
    elif cmd == "privacy":
        if args.state == "on":
            app.personal.set_privacy_mode(True)
        elif args.state == "off":
            app.personal.set_privacy_mode(False)
        enabled = app.personal.privacy_enabled()
        _out(args, {"message": f"隐私模式：{'开启' if enabled else '关闭'}", "enabled": enabled})
    elif cmd == "collect":
        result = app.collect_all()
        _out(args, {"message": f"采集完成", **result})
    elif cmd == "add-watchlist":
        wid = app.personal.add_watchlist(args.name, args.type, args.keywords)
        _out(args, {"message": f"已添加关注：{args.name}", "id": wid})
    elif cmd == "add-quote":
        qid = app.quote_service.add_quote(args.content, args.author, args.style)
        _out(args, {"message": f"已添加语录", "id": qid})
    elif cmd == "list-apis":
        apis = app.api_service.list_apis(args.category, args.provider)
        _out(args, {"message": f"共 {len(apis)} 个 API", "apis": apis})
    elif cmd == "source-health":
        health = app.source_health.get_health()
        _out(args, {"message": f"共 {len(health)} 个来源", "health": health})
    elif cmd == "notifications":
        notifs = app.notification_service.list_notifications(args.status)
        _out(args, {"message": f"共 {len(notifs)} 条通知", "notifications": notifs})
    elif cmd == "read":
        app.personal.set_reading_state("article", args.article_id, "read")
        _out(args, {"message": f"已标记已读：{args.article_id}"})
    elif cmd == "favorite":
        app.personal.set_reading_state("article", args.article_id, "favorite")
        _out(args, {"message": f"已收藏：{args.article_id}"})
    elif cmd == "collection":
        items = app.personal.list_collection(args.type)
        _out(args, {"message": f"共 {len(items)} 条", "items": items})
    elif cmd == "rebuild-index":
        count = app.search_service.rebuild_index()
        _out(args, {"message": f"已重建索引：{count} 条", "count": count})
    elif cmd == "add-source":
        sid = app.source_mgr.create_source(args.name, args.type, args.category, args.url)
        _out(args, {"message": f"已添加来源：{args.name}", "id": sid})
    elif cmd == "list-feeds":
        from news_intelligence_desktop.connectors.extra_sources import MultiRssConnector
        feeds = MultiRssConnector().list_available_feeds()
        _out(args, {"message": f"共 {len(feeds)} 个可用 RSS 源", "feeds": feeds})
    elif cmd == "tech-detect":
        count = app.tech_service.detect_and_store()
        _out(args, {"message": f"检测到 {count} 个技术变化", "count": count})
    elif cmd == "policy-add":
        from news_intelligence_desktop.services.policy_capture import PolicyService
        policy_svc = PolicyService(app.repo)
        pid = policy_svc.add_policy(
            title=args.title, issuer=args.issuer, region=args.region,
            category=args.category, summary=args.summary, source_url=args.source_url,
        )
        _out(args, {"message": f"已添加政策：{args.title}", "id": pid})
    elif cmd == "policy-list":
        from news_intelligence_desktop.services.policy_capture import PolicyService
        policy_svc = PolicyService(app.repo)
        policies = policy_svc.list_policies(region=args.region, category=args.category)
        _out(args, {"message": f"共 {len(policies)} 条政策", "policies": policies})
    else:
        parser.print_help()
    return 0


def _out(args, data: dict) -> None:
    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data.get("message", json.dumps(data, ensure_ascii=False)))


if __name__ == "__main__":
    raise SystemExit(main())
