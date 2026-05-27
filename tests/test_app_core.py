from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.services.app_service import AppService
from news_intelligence_desktop.storage.repository import ArticleInput


class TestAppCore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = AppSettings.load(Path(self.tmp.name))
        self.app = AppService(self.settings)
        self.app.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def test_home_dashboard(self):
        dash = self.app.home_dashboard()
        self.assertIn("个人每日信息中枢", dash["title"])
        self.assertGreaterEqual(len(dash["cards"]), 8)
        self.assertEqual(dash["privacy_mode"], False)

    def test_reading_states(self):
        articles = self.app.repo.list_articles(limit=1)
        self.assertTrue(articles)
        aid = articles[0]["id"]
        self.app.personal.set_reading_state("article", aid, "favorite")
        self.assertEqual(self.app.personal.get_reading_state("article", aid), "favorite")
        favs = self.app.personal.list_collection("favorite")
        self.assertTrue(any(a["id"] == aid for a in favs))

    def test_special_favorite_domain(self):
        fid = self.app.personal.add_special_favorite("示例技术", "https://example.com/tech")
        items = self.app.personal.special_tab_articles(fid)
        self.assertTrue(any("example.com" in a["url"] for a in items))

    def test_special_favorite_exact(self):
        aid = self.app.repo.add_article(ArticleInput(
            title="特别站点发布", summary="测试", source_name="特别站点",
            source_url="https://special.example/news", url="https://special.example/news/1", category="custom",
        ))
        fid = self.app.personal.add_special_favorite("特别站点", "https://special.example/news/1", "exact")
        items = self.app.personal.special_tab_articles(fid)
        self.assertEqual([a["id"] for a in items], [aid])

    def test_watchlist(self):
        wid = self.app.personal.add_watchlist("AI关注", "tech_stack", ["AI", "模型"])
        matches = self.app.personal.watchlist_matches()
        self.assertTrue(matches)

    def test_daily_quote(self):
        q = self.app.quote_service.get_home_quote()
        self.assertIn("content", q)
        self.assertIn("style_label", q)
        styles = self.app.quote_service.list_styles()
        self.assertTrue(len(styles) >= 5)

    def test_tech_changes(self):
        count = self.app.tech_service.detect_and_store()
        self.assertIsInstance(count, int)

    def test_search(self):
        results = self.app.search("AI")
        self.assertTrue(len(results) >= 1)

    def test_brief(self):
        brief = self.app.generate_brief("晨报")
        self.assertIn("晨报", brief["title"])
        self.assertIn("body", brief)

    def test_export(self):
        articles = self.app.repo.list_articles(limit=1)
        aid = articles[0]["id"]
        out = Path(self.tmp.name) / "exports" / "test.md"
        result = self.app.export_article(aid, out)
        self.assertTrue(result.exists())
        content = result.read_text()
        self.assertTrue(len(content) > 10)

    def test_backup(self):
        out = Path(self.tmp.name) / "backups" / "test.sqlite3"
        result = self.app.create_backup(out)
        self.assertTrue(result.exists())

    def test_privacy_mode(self):
        self.app.personal.set_privacy_mode(True)
        self.assertTrue(self.app.personal.privacy_enabled())
        self.app.personal.set_privacy_mode(False)
        self.assertFalse(self.app.personal.privacy_enabled())

    def test_source_health(self):
        self.app.repo.record_source_success(1, 100)
        self.app.repo.record_source_failure(1, "timeout")
        health = self.app.source_health.get_health()
        self.assertTrue(any(h["id"] == 1 for h in health))

    def test_credibility(self):
        articles = self.app.repo.list_articles(limit=1)
        aid = articles[0]["id"]
        cred = self.app.credibility.explain("article", aid)
        self.assertIn("score", cred)

    def test_notification(self):
        nid = self.app.notification_service.enqueue("测试通知", "测试内容")
        notifs = self.app.notification_service.list_notifications()
        self.assertTrue(any(n["id"] == nid for n in notifs))
        self.app.notification_service.mark_read(nid)

    def test_subscription_rule(self):
        rid = self.app.notification_service.create_rule("AI追踪", ["AI", "模型"])
        rules = self.app.notification_service.list_rules()
        self.assertTrue(any(r["id"] == rid for r in rules))

    def test_api_catalog(self):
        apis = self.app.api_service.list_apis()
        self.assertTrue(len(apis) >= 5)
        categories = self.app.api_service.list_categories()
        self.assertTrue(len(categories) >= 3)

    def test_weather_forecast(self):
        from news_intelligence_desktop.connectors.weather_earthquake import WeatherConnector
        conn = WeatherConnector()
        result = conn.fetch_forecast(days=1)
        self.assertIsInstance(result.ok, bool)

    def test_earthquake(self):
        from news_intelligence_desktop.connectors.weather_earthquake import EarthquakeConnector
        conn = EarthquakeConnector()
        result = conn.fetch_recent(limit=5)
        self.assertIsInstance(result.ok, bool)

    def test_vvhan_hot(self):
        from news_intelligence_desktop.connectors.news_rss import VvhanConnector
        conn = VvhanConnector()
        result = conn.fetch_hot("hot")
        self.assertIsInstance(result.ok, bool)

    def test_gdelt(self):
        from news_intelligence_desktop.connectors.news_rss import GdeltConnector
        conn = GdeltConnector()
        result = conn.search("technology", max_records=3)
        self.assertIsInstance(result.ok, bool)

    def test_analysis(self):
        from news_intelligence_desktop.analysis import extract_keywords, analyze_sentiment, classify_channel, detect_tech_change
        kws = extract_keywords(["AI 模型发布 Python 框架更新"], top_n=5)
        self.assertTrue(kws)
        sent = analyze_sentiment(["这是一个好消息", "漏洞被发现"])
        self.assertTrue(sent.total >= 2)
        ch = classify_channel("Python 3.13 Release")
        self.assertIn("tech", ch)
        tc = detect_tech_change("Python 3.13.0 Release")
        self.assertIsNotNone(tc)

    def test_cli_json_output(self):
        from news_intelligence_desktop.app.main import main
        data_dir = Path(self.tmp.name) / "cli"
        self.assertEqual(main(["--data-dir", str(data_dir), "--json"]), 0)


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name) / "cli_data"

    def tearDown(self):
        self.tmp.cleanup()

    def test_console_run(self):
        from news_intelligence_desktop.app.main import main
        self.assertEqual(main(["--data-dir", str(self.data_dir), "--json"]), 0)

    def test_json_output(self):
        from news_intelligence_desktop.app.main import main
        self.assertEqual(main(["--data-dir", str(self.data_dir), "--json"]), 0)

    def test_add_special(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "add-special", "测试", "https://example.com"])

    def test_search(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "search", "AI"])

    def test_brief(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "brief", "晨报"])

    def test_privacy(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "privacy", "on"])
        main(["--data-dir", str(self.data_dir), "privacy", "off"])

    def test_collect(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "collect"])

    def test_add_watchlist(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "add-watchlist", "AI", "tech_stack", "AI", "模型"])

    def test_add_quote(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "add-quote", "测试语录", "--style", "tech"])

    def test_list_apis(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "list-apis"])

    def test_source_health(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "source-health"])

    def test_notifications(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "notifications"])

    def test_read_favorite(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "read", "1"])
        main(["--data-dir", str(self.data_dir), "favorite", "1"])

    def test_collection(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "collection", "favorite"])

    def test_rebuild_index(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "rebuild-index"])

    def test_add_source(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "add-source", "测试源", "rss", "news", "https://example.com/rss"])

    def test_backup(self):
        from news_intelligence_desktop.app.main import main
        out = Path(self.tmp.name) / "backup.sqlite3"
        main(["--data-dir", str(self.data_dir), "backup", str(out)])


if __name__ == "__main__":
    unittest.main()
