from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

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
        self.assertTrue(len(apis) >= 10)  # Now we have more APIs
        categories = self.app.api_service.list_categories()
        self.assertTrue(len(categories) >= 5)

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
        # Use --json to avoid launching GUI
        self.assertEqual(main(["--data-dir", str(data_dir), "--json"]), 0)

    def test_article_detail(self):
        articles = self.app.repo.list_articles(limit=1)
        aid = articles[0]["id"]
        article = self.app.repo.get_article(aid)
        self.assertIsNotNone(article)
        self.assertEqual(article["id"], aid)

    def test_export_formats(self):
        articles = self.app.repo.list_articles(limit=1)
        aid = articles[0]["id"]
        
        # Test markdown export
        out_md = Path(self.tmp.name) / "exports" / "test.md"
        result = self.app.export_article(aid, out_md, "markdown")
        self.assertTrue(result.exists())
        
        # Test JSON export
        out_json = Path(self.tmp.name) / "exports" / "test.json"
        result = self.app.export_article(aid, out_json, "json")
        self.assertTrue(result.exists())
        data = json.loads(result.read_text())
        self.assertEqual(data["id"], aid)
        
        # Test HTML export
        out_html = Path(self.tmp.name) / "exports" / "test.html"
        result = self.app.export_article(aid, out_html, "html")
        self.assertTrue(result.exists())
        self.assertIn("<html>", result.read_text())

    def test_special_favorite_path_prefix(self):
        self.app.repo.add_article(ArticleInput(
            title="路径匹配测试", summary="测试", source_name="测试",
            source_url="https://example.com", url="https://example.com/blog/post-1", category="tech",
        ))
        fid = self.app.personal.add_special_favorite("博客", "https://example.com/blog", "path_prefix")
        items = self.app.personal.special_tab_articles(fid)
        self.assertTrue(any("blog" in a["url"] for a in items))

    def test_special_favorite_delete(self):
        fid = self.app.personal.add_special_favorite("删除测试", "https://example.com")
        self.app.personal.delete_special_favorite(fid)
        tabs = self.app.personal.list_special_tabs()
        self.assertFalse(any(t["id"] == fid for t in tabs))

    def test_policy_service(self):
        from news_intelligence_desktop.services.policy_capture import PolicyService
        svc = PolicyService(self.app.repo)
        pid = svc.add_policy("测试政策", issuer="国务院", region="national", category="法规")
        policies = svc.list_policies(region="national")
        self.assertTrue(any(p["id"] == pid for p in policies))

    def test_region_service(self):
        from news_intelligence_desktop.services.policy_capture import RegionService
        svc = RegionService(self.app.repo)
        regions = svc.list_regions()
        self.assertTrue(len(regions) >= 5)
        detected = svc.detect_region("北京市发布新政策")
        self.assertIn("beijing", detected)


class TestConnectorsMocked(unittest.TestCase):
    """Test connectors with mocked network calls."""

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_weather_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.weather_earthquake import WeatherConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-05-27", "2026-05-28"],
                "temperature_2m_max": [25, 26],
                "temperature_2m_min": [15, 16],
                "weathercode": [1, 2],
                "precipitation_sum": [0, 0.5],
            }
        }
        mock_get.return_value = mock_response
        
        conn = WeatherConnector()
        result = conn.fetch_forecast(days=2)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[0]["temp_high"], 25)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_weather_connector_failure(self, mock_get):
        from news_intelligence_desktop.connectors.weather_earthquake import WeatherConnector
        
        mock_get.side_effect = Exception("Network error")
        
        conn = WeatherConnector()
        result = conn.fetch_forecast()
        self.assertFalse(result.ok)
        self.assertIn("Network error", result.error)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_earthquake_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.weather_earthquake import EarthquakeConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "id": "test123",
                    "properties": {
                        "mag": 5.5,
                        "place": "Test Location",
                        "time": 1685000000000,
                        "url": "https://example.com/detail",
                    },
                    "geometry": {
                        "coordinates": [120.0, 30.0, 10.0],
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        conn = EarthquakeConnector()
        result = conn.fetch_recent(limit=1)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["magnitude"], 5.5)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_rss_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.news_rss import RssConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article 1</title>
                    <link>https://example.com/1</link>
                    <summary>Summary 1</summary>
                    <pubDate>Wed, 27 May 2026 00:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Test Article 2</title>
                    <link>https://example.com/2</link>
                    <summary>Summary 2</summary>
                </item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_response
        
        conn = RssConnector()
        result = conn.fetch_feed("https://example.com/rss", "TestSource")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[0]["title"], "Test Article 1")

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_vvhan_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.news_rss import VvhanConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"title": "Hot Topic 1", "desc": "Description 1", "url": "https://example.com/1"},
                {"title": "Hot Topic 2", "desc": "Description 2", "url": "https://example.com/2"},
            ]
        }
        mock_get.return_value = mock_response
        
        conn = VvhanConnector()
        result = conn.fetch_hot("hot")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 2)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_gdelt_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.news_rss import GdeltConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {"title": "GDELT Article", "url": "https://example.com/gdelt", "domain": "example.com", "seendate": "20260527T000000"},
            ]
        }
        mock_get.return_value = mock_response
        
        conn = GdeltConnector()
        result = conn.search("test", max_records=1)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 1)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_devto_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.extra_sources import DevToConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "title": "DEV.to Article",
                "description": "A great article",
                "url": "https://dev.to/article",
                "published_at": "2026-05-27T00:00:00Z",
                "tag_list": ["python", "tutorial"],
            }
        ]
        mock_get.return_value = mock_response
        
        conn = DevToConnector()
        result = conn.fetch_articles(top=1)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 1)
        self.assertIn("python", result.data[0]["tags"])

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_lobsters_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.extra_sources import LobstersConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "title": "Lobsters Post",
                "description": "Interesting post",
                "url": "https://lobste.rs/post",
                "created_at": "2026-05-27T00:00:00Z",
                "tags": ["programming", "python"],
            }
        ]
        mock_get.return_value = mock_response
        
        conn = LobstersConnector()
        result = conn.fetch_hot(limit=1)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 1)

    @patch('news_intelligence_desktop.connectors.requests.get')
    def test_hitokoto_connector_success(self, mock_get):
        from news_intelligence_desktop.connectors.quote_rss import QuoteConnector
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hitokoto": "测试语录",
            "from_who": "测试作者",
        }
        mock_get.return_value = mock_response
        
        conn = QuoteConnector()
        result = conn.fetch_hitokoto()
        self.assertTrue(result.ok)
        self.assertEqual(result.data[0]["content"], "测试语录")


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

    def test_list_feeds(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "list-feeds"])

    def test_tech_detect(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "tech-detect"])

    def test_policy_add_list(self):
        from news_intelligence_desktop.app.main import main
        main(["--data-dir", str(self.data_dir), "policy-add", "测试政策", "--issuer", "国务院", "--region", "national"])
        main(["--data-dir", str(self.data_dir), "policy-list", "--region", "national"])


class TestAnalysisEdgeCases(unittest.TestCase):
    """Test analysis functions with edge cases."""

    def test_extract_keywords_empty(self):
        from news_intelligence_desktop.analysis import extract_keywords
        result = extract_keywords([], top_n=5)
        self.assertEqual(result, [])

    def test_extract_keywords_single_word(self):
        from news_intelligence_desktop.analysis import extract_keywords
        result = extract_keywords(["A"], top_n=5)
        self.assertEqual(result, [])

    def test_analyze_sentiment_empty(self):
        from news_intelligence_desktop.analysis import analyze_sentiment
        result = analyze_sentiment([])
        self.assertEqual(result.total, 0)

    def test_classify_channel_unknown(self):
        from news_intelligence_desktop.analysis import classify_channel
        result = classify_channel("Random text without keywords")
        self.assertEqual(result, ["general"])

    def test_detect_tech_change_none(self):
        from news_intelligence_desktop.analysis import detect_tech_change
        result = detect_tech_change("Just a normal article")
        self.assertIsNone(result)


class TestRepositoryEdgeCases(unittest.TestCase):
    """Test repository with edge cases."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = AppSettings.load(Path(self.tmp.name))
        self.app = AppService(self.settings)
        self.app.initialize()

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_article_duplicate_url(self):
        article = ArticleInput(title="Test", summary="Test", source_name="Test", source_url="https://example.com", url="https://example.com/duplicate")
        aid1 = self.app.repo.add_article(article)
        aid2 = self.app.repo.add_article(article)
        self.assertEqual(aid1, aid2)  # Should return same ID due to OR IGNORE

    def test_get_article_not_found(self):
        result = self.app.repo.get_article(99999)
        self.assertIsNone(result)

    def test_list_articles_empty_category(self):
        articles = self.app.repo.list_articles(category="nonexistent")
        self.assertEqual(articles, [])

    def test_privacy_mode_idempotent(self):
        self.app.personal.set_privacy_mode(True)
        self.app.personal.set_privacy_mode(True)  # Should not raise
        self.assertTrue(self.app.personal.privacy_enabled())


if __name__ == "__main__":
    unittest.main()
