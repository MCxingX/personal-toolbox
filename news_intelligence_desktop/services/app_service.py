from __future__ import annotations

import json
from datetime import date

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.storage.database import Database
from news_intelligence_desktop.storage.repository import Repository
from news_intelligence_desktop.services.source_manager import SourceManager
from news_intelligence_desktop.services.collector import Collector
from news_intelligence_desktop.services.daily_quote import DailyQuoteService
from news_intelligence_desktop.services.tech_change import TechChangeService
from news_intelligence_desktop.services.home_dashboard import HomeDashboardService
from news_intelligence_desktop.services.brief import BriefService
from news_intelligence_desktop.services.notification import NotificationService
from news_intelligence_desktop.services.api_toolbox import ApiToolboxService
from news_intelligence_desktop.services.personal import PersonalService
from news_intelligence_desktop.services.enhanced_services import SearchService, ExportService, BackupService, CredibilityService, SourceHealthService
from news_intelligence_desktop.services.oddity import OddityService
from news_intelligence_desktop.services.policy_capture import PolicyService
from news_intelligence_desktop.storage.settings_db import SettingsDB


class AppService:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.database = Database(settings.db_path)
        self.repo = Repository(self.database)
        self.settings_db = SettingsDB(settings.db_path)
        self.source_mgr = SourceManager(self.repo)
        self.collector = Collector(self.repo, settings=self.settings_db.get_all())
        self.quote_service = DailyQuoteService(self.repo)
        self.tech_service = TechChangeService(self.repo)
        self.home_service = HomeDashboardService(self.repo, self.quote_service, self.tech_service)
        self.brief_service = BriefService(self.repo, self.quote_service)
        self.notification_service = NotificationService(self.repo)
        self.api_service = ApiToolboxService(self.repo)
        self.personal = PersonalService(self.repo)
        self.search_service = SearchService(self.repo)
        self.export_service = ExportService(self.repo)
        self.backup_service = BackupService(self.repo)
        self.credibility = CredibilityService(self.repo)
        self.source_health = SourceHealthService(self.repo)
        self.oddity_service = OddityService(self.repo)
        self.policy_service = PolicyService(self.repo)

    def initialize(self) -> None:
        self.database.initialize()
        self.repo.seed_defaults()
        self.quote_service.seed_quotes()
        self.api_service.seed_catalog()

        # 启动时检查是否需要清理过期数据（凌晨 0-6 点执行）
        try:
            from news_intelligence_desktop.services.data_retention import check_and_cleanup_if_needed
            result = check_and_cleanup_if_needed(self.repo)
            if result and not result.get("skipped"):
                total = sum(v for k, v in result.items() if k != "skipped")
                if total > 0:
                    print(f"启动清理: 删除 {total} 条过期数据")
        except Exception as e:
            pass  # 清理失败不影响启动

    def home_dashboard(self) -> dict:
        return self.home_service.generate()

    def collect_all(self) -> dict:
        if self.personal.privacy_enabled():
            return {"weather": 0, "earthquake": 0, "news": 0, "hot": 0, "tech": 0, "quote": 0, "custom": 0, "errors": [], "privacy_paused": True}
        return self.collector.collect_all()

    def generate_brief(self, brief_type: str) -> dict:
        return self.brief_service.generate(brief_type)

    def search(self, query: str) -> list[dict]:
        return self.search_service.search(query)

    def export_article(self, article_id: int, output, fmt: str = "markdown"):
        from pathlib import Path
        return self.export_service.export_article(article_id, Path(output), fmt)

    def create_backup(self, output):
        from pathlib import Path
        return self.backup_service.create_backup(Path(output))
