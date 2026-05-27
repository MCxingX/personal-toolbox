"""Main GUI application with sidebar navigation and page system."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea,
        QStatusBar, QMessageBox, QSplitter, QGroupBox, QGridLayout,
        QTextEdit, QLineEdit, QComboBox, QSpinBox, QCheckBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
        QTabWidget, QSizePolicy, QToolButton, QMenu,
    )
    from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer
    from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QAction
    HAS_QT = True
except ImportError:
    HAS_QT = False

from news_intelligence_desktop.config.settings import AppSettings
from news_intelligence_desktop.services.app_service import AppService


if HAS_QT:

    class CollectWorker(QThread):
        """Background worker for data collection."""
        finished = Signal(dict)
        error = Signal(str)

        def __init__(self, app_service: AppService):
            super().__init__()
            self.app = app_service

        def run(self):
            try:
                result = self.app.collect_all()
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(str(e))


    class SidebarButton(QPushButton):
        """Custom sidebar navigation button."""
        def __init__(self, text: str, icon_text: str = "", parent=None):
            super().__init__(parent)
            self.setText(f"  {icon_text}  {text}" if icon_text else f"  {text}")
            self.setFixedHeight(44)
            self.setCursor(Qt.PointingHandCursor)
            self.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 16px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #333;
                    background: transparent;
                }
                QPushButton:hover {
                    background: #e8f0fe;
                    color: #1a73e8;
                }
                QPushButton:checked {
                    background: #d2e3fc;
                    color: #1a73e8;
                    font-weight: bold;
                }
            """)
            self.setCheckable(True)


    class CardWidget(QFrame):
        """Styled card widget for dashboard items."""
        def __init__(self, title: str, parent=None):
            super().__init__(parent)
            self.setFrameShape(QFrame.StyledPanel)
            self.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 16px;
                }
                QFrame:hover {
                    border: 1px solid #1a73e8;
                }
            """)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)

            self.title_label = QLabel(title)
            self.title_label.setFont(QFont("", 14, QFont.Bold))
            self.title_label.setStyleSheet("color: #1a73e8; border: none;")
            layout.addWidget(self.title_label)

            self.content_layout = QVBoxLayout()
            layout.addLayout(self.content_layout)

        def add_item(self, text: str):
            label = QLabel(f"  {text}")
            label.setStyleSheet("color: #333; border: none; padding: 4px 0;")
            label.setWordWrap(True)
            self.content_layout.addWidget(label)

        def add_summary(self, text: str):
            label = QLabel(text)
            label.setStyleSheet("color: #666; border: none; font-size: 12px;")
            label.setWordWrap(True)
            self.content_layout.addWidget(label)


    class HomePage(QWidget):
        """Home dashboard page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(16)

            # Header
            header = QLabel("个人每日信息中枢")
            header.setFont(QFont("", 20, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            # Scroll area for cards
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")

            cards_widget = QWidget()
            self.cards_layout = QGridLayout(cards_widget)
            self.cards_layout.setSpacing(16)

            scroll.setWidget(cards_widget)
            layout.addWidget(scroll)

            # Refresh button
            btn_layout = QHBoxLayout()
            self.refresh_btn = QPushButton("刷新首页")
            self.refresh_btn.setFixedHeight(40)
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background: #1a73e8;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    padding: 0 24px;
                }
                QPushButton:hover { background: #1557b0; }
                QPushButton:pressed { background: #0d47a1; }
            """)
            self.refresh_btn.clicked.connect(self.refresh)
            btn_layout.addWidget(self.refresh_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        def refresh(self):
            dash = self.app.home_dashboard()

            # Clear old cards
            while self.cards_layout.count():
                item = self.cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Add cards
            for i, card in enumerate(dash.get("cards", [])):
                card_widget = CardWidget(card["name"])
                card_widget.add_summary(card.get("summary", ""))
                for item in card.get("items", [])[:3]:
                    card_widget.add_item(f"  {item['title']}")
                if card.get("quote"):
                    q = card["quote"]
                    card_widget.add_item(f"  {q.get('style_label', '语录')}: {q['content']}")
                row, col = divmod(i, 2)
                self.cards_layout.addWidget(card_widget, row, col)


    class WeatherPage(QWidget):
        """Weather forecast page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("天气预报")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["日期", "高温", "低温", "天气"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

            btn = QPushButton("刷新天气")
            btn.setFixedHeight(36)
            btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            btn.clicked.connect(self.refresh)
            layout.addWidget(btn)

        def refresh(self):
            with self.app.repo.db.connect() as conn:
                forecasts = [dict(r) for r in conn.execute("SELECT * FROM weather_forecasts ORDER BY forecast_date LIMIT 7")]
            self.table.setRowCount(len(forecasts))
            for i, f in enumerate(forecasts):
                self.table.setItem(i, 0, QTableWidgetItem(f.get("forecast_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(str(f.get("temp_high", "--"))))
                self.table.setItem(i, 2, QTableWidgetItem(str(f.get("temp_low", "--"))))
                self.table.setItem(i, 3, QTableWidgetItem(f.get("description", "")))


    class EarthquakePage(QWidget):
        """Earthquake events page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("地震动态")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["震级", "位置", "时间", "来源"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

            btn = QPushButton("刷新地震数据")
            btn.setFixedHeight(36)
            btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            btn.clicked.connect(self.refresh)
            layout.addWidget(btn)

        def refresh(self):
            with self.app.repo.db.connect() as conn:
                events = [dict(r) for r in conn.execute("SELECT * FROM earthquake_events ORDER BY event_time DESC LIMIT 20")]
            self.table.setRowCount(len(events))
            for i, e in enumerate(events):
                self.table.setItem(i, 0, QTableWidgetItem(f"M{e.get('magnitude', 0)}"))
                self.table.setItem(i, 1, QTableWidgetItem(e.get("place", "")))
                self.table.setItem(i, 2, QTableWidgetItem(e.get("event_time", "")[:16]))
                self.table.setItem(i, 3, QTableWidgetItem(e.get("source", "")))


    class NewsPage(QWidget):
        """News articles page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("新闻资讯")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            # Filter
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("分类:"))
            self.category_combo = QComboBox()
            self.category_combo.addItems(["全部", "新闻", "技术", "政策", "热点", "本地"])
            self.category_combo.currentTextChanged.connect(self.refresh)
            filter_layout.addWidget(self.category_combo)
            filter_layout.addStretch()
            layout.addLayout(filter_layout)

            # Table
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "标题", "来源", "分类", "时间"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.table.doubleClicked.connect(self._show_detail)
            layout.addWidget(self.table)

            # Buttons
            btn_layout = QHBoxLayout()
            refresh_btn = QPushButton("刷新列表")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            btn_layout.addWidget(refresh_btn)

            detail_btn = QPushButton("查看详情")
            detail_btn.setFixedHeight(36)
            detail_btn.setStyleSheet("QPushButton { background: #34a853; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #2d8e47; }")
            detail_btn.clicked.connect(self._show_detail)
            btn_layout.addWidget(detail_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        def refresh(self):
            cat_map = {"全部": None, "新闻": "news", "技术": "tech", "政策": "policy", "热点": "hot", "本地": "local"}
            cat = cat_map.get(self.category_combo.currentText())
            articles = self.app.repo.list_articles(category=cat, limit=50)
            self.table.setRowCount(len(articles))
            for i, a in enumerate(articles):
                self.table.setItem(i, 0, QTableWidgetItem(str(a.get("id", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(a.get("title", "")))
                self.table.setItem(i, 2, QTableWidgetItem(a.get("source_name", "")))
                self.table.setItem(i, 3, QTableWidgetItem(a.get("category", "")))
                self.table.setItem(i, 4, QTableWidgetItem(a.get("collected_at", "")[:16]))

        def _show_detail(self):
            row = self.table.currentRow()
            if row < 0:
                return
            aid = int(self.table.item(row, 0).text())
            article = self.app.repo.get_article(aid)
            if not article:
                return

            dlg = QMessageBox(self)
            dlg.setWindowTitle(article.get("title", "文章详情"))
            dlg.setText(f"标题: {article.get('title', '')}\n\n"
                       f"来源: {article.get('source_name', '')}\n"
                       f"分类: {article.get('category', '')}\n"
                       f"链接: {article.get('url', '')}\n\n"
                       f"摘要:\n{article.get('summary', '无')}")
            dlg.exec()


    class QuotePage(QWidget):
        """Daily quote page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("每日语录")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            # Quote display
            self.quote_label = QLabel()
            self.quote_label.setFont(QFont("", 16))
            self.quote_label.setStyleSheet("color: #333; padding: 24px; background: #f8f9fa; border-radius: 12px;")
            self.quote_label.setWordWrap(True)
            self.quote_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.quote_label)

            self.author_label = QLabel()
            self.author_label.setStyleSheet("color: #666; font-size: 14px;")
            self.author_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.author_label)

            # Style selector
            style_layout = QHBoxLayout()
            style_layout.addWidget(QLabel("选择风格:"))
            self.style_combo = QComboBox()
            self.style_combo.addItems(["随机", "开心一点", "别委屈", "加油鼓励", "冷静理性", "幽默段子", "技术人专属", "哲理"])
            style_layout.addWidget(self.style_combo)

            refresh_btn = QPushButton("换一条")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            style_layout.addWidget(refresh_btn)
            style_layout.addStretch()
            layout.addLayout(style_layout)

            layout.addStretch()

        def refresh(self):
            style_map = {"随机": None, "开心一点": "happy", "别委屈": "comfort", "加油鼓励": "encourage",
                        "冷静理性": "calm", "幽默段子": "humor", "技术人专属": "tech", "哲理": "philosophy"}
            style = style_map.get(self.style_combo.currentText())
            q = self.app.quote_service.get_quote(style)
            self.quote_label.setText(f"\u300c{q.get('content', '')}\u300d")
            author = q.get("author", "")
            self.author_label.setText(f"\u2014\u2014 {author}" if author else "")


    class TechChangesPage(QWidget):
        """Tech changes page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("技术变化追踪")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["类型", "标题", "来源", "时间"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

            btn_layout = QHBoxLayout()
            detect_btn = QPushButton("检测技术变化")
            detect_btn.setFixedHeight(36)
            detect_btn.setStyleSheet("QPushButton { background: #34a853; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #2d8e47; }")
            detect_btn.clicked.connect(self._detect)
            btn_layout.addWidget(detect_btn)

            refresh_btn = QPushButton("刷新列表")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            btn_layout.addWidget(refresh_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        def _detect(self):
            count = self.app.tech_service.detect_and_store()
            QMessageBox.information(self, "检测完成", f"检测到 {count} 个技术变化")
            self.refresh()

        def refresh(self):
            changes = self.app.tech_service.list_changes(limit=30)
            self.table.setRowCount(len(changes))
            for i, c in enumerate(changes):
                self.table.setItem(i, 0, QTableWidgetItem(c.get("change_type", "")))
                self.table.setItem(i, 1, QTableWidgetItem(c.get("title", "")))
                self.table.setItem(i, 2, QTableWidgetItem(c.get("source_name", "")))
                self.table.setItem(i, 3, QTableWidgetItem(c.get("published_at", "")[:16]))


    class SearchPage(QWidget):
        """Search page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("搜索")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            # Search input
            search_layout = QHBoxLayout()
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("输入关键词搜索...")
            self.search_input.setFixedHeight(40)
            self.search_input.setStyleSheet("QLineEdit { border: 1px solid #ddd; border-radius: 8px; padding: 0 12px; font-size: 14px; } QLineEdit:focus { border: 1px solid #1a73e8; }")
            self.search_input.returnPressed.connect(self._search)
            search_layout.addWidget(self.search_input)

            search_btn = QPushButton("搜索")
            search_btn.setFixedSize(80, 40)
            search_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; font-size: 14px; } QPushButton:hover { background: #1557b0; }")
            search_btn.clicked.connect(self._search)
            search_layout.addWidget(search_btn)
            layout.addLayout(search_layout)

            # Results
            self.results_table = QTableWidget()
            self.results_table.setColumnCount(3)
            self.results_table.setHorizontalHeaderLabels(["类型", "标题", "摘要"])
            self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.results_table)

            # Rebuild index button
            rebuild_btn = QPushButton("重建搜索索引")
            rebuild_btn.setFixedHeight(36)
            rebuild_btn.setStyleSheet("QPushButton { background: #fbbc04; color: #333; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #e0a800; }")
            rebuild_btn.clicked.connect(self._rebuild)
            layout.addWidget(rebuild_btn)

        def _search(self):
            query = self.search_input.text().strip()
            if not query:
                return
            results = self.app.search(query)
            self.results_table.setRowCount(len(results))
            for i, r in enumerate(results):
                self.results_table.setItem(i, 0, QTableWidgetItem(r.get("item_type", "")))
                self.results_table.setItem(i, 1, QTableWidgetItem(r.get("title", "")))
                self.results_table.setItem(i, 2, QTableWidgetItem(r.get("snippet", "")[:100]))

        def _rebuild(self):
            count = self.app.search_service.rebuild_index()
            QMessageBox.information(self, "重建完成", f"已重建 {count} 条索引")


    class ToolboxPage(QWidget):
        """API Toolbox page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("API 工具箱")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "名称", "提供商", "分类", "状态"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

            refresh_btn = QPushButton("刷新列表")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            layout.addWidget(refresh_btn)

        def refresh(self):
            apis = self.app.api_service.list_apis()
            self.table.setRowCount(len(apis))
            for i, a in enumerate(apis):
                self.table.setItem(i, 0, QTableWidgetItem(str(a.get("id", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(a.get("name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(a.get("provider", "")))
                self.table.setItem(i, 3, QTableWidgetItem(a.get("category", "")))
                status = a.get("status", "")
                item = QTableWidgetItem(status)
                if status == "enabled":
                    item.setForeground(QColor("#34a853"))
                elif status == "needs_config":
                    item.setForeground(QColor("#fbbc04"))
                self.table.setItem(i, 4, item)


    class PersonalPage(QWidget):
        """Personal center page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("个人中心")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            # Stats
            stats_layout = QHBoxLayout()
            self.fav_label = QLabel("收藏: 0")
            self.fav_label.setStyleSheet("font-size: 14px; padding: 8px; background: #e8f5e9; border-radius: 8px;")
            stats_layout.addWidget(self.fav_label)

            self.readlater_label = QLabel("稍后看: 0")
            self.readlater_label.setStyleSheet("font-size: 14px; padding: 8px; background: #fff3e0; border-radius: 8px;")
            stats_layout.addWidget(self.readlater_label)

            self.watch_label = QLabel("关注: 0")
            self.watch_label.setStyleSheet("font-size: 14px; padding: 8px; background: #e3f2fd; border-radius: 8px;")
            stats_layout.addWidget(self.watch_label)
            layout.addLayout(stats_layout)

            # Privacy toggle
            privacy_layout = QHBoxLayout()
            self.privacy_check = QCheckBox("隐私模式")
            self.privacy_check.setStyleSheet("font-size: 14px;")
            self.privacy_check.toggled.connect(self._toggle_privacy)
            privacy_layout.addWidget(self.privacy_check)
            privacy_layout.addStretch()
            layout.addLayout(privacy_layout)

            # Favorites table
            layout.addWidget(QLabel("最近收藏:"))
            self.fav_table = QTableWidget()
            self.fav_table.setColumnCount(3)
            self.fav_table.setHorizontalHeaderLabels(["ID", "标题", "来源"])
            self.fav_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.fav_table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.fav_table)

            refresh_btn = QPushButton("刷新")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            layout.addWidget(refresh_btn)

        def _toggle_privacy(self, checked):
            self.app.personal.set_privacy_mode(checked)
            QMessageBox.information(self, "隐私模式", f"隐私模式已{'开启' if checked else '关闭'}")

        def refresh(self):
            favorites = self.app.personal.list_collection("favorite")
            read_later = self.app.personal.list_collection("read_later")
            watchlist = self.app.personal.list_watchlist()

            self.fav_label.setText(f"收藏: {len(favorites)}")
            self.readlater_label.setText(f"稍后看: {len(read_later)}")
            self.watch_label.setText(f"关注: {len(watchlist)}")

            self.privacy_check.setChecked(self.app.personal.privacy_enabled())

            self.fav_table.setRowCount(min(len(favorites), 20))
            for i, a in enumerate(favorites[:20]):
                self.fav_table.setItem(i, 0, QTableWidgetItem(str(a.get("id", ""))))
                self.fav_table.setItem(i, 1, QTableWidgetItem(a.get("title", "")))
                self.fav_table.setItem(i, 2, QTableWidgetItem(a.get("source_name", "")))


    class SourcesPage(QWidget):
        """Data sources management page."""
        def __init__(self, app_service: AppService, parent=None):
            super().__init__(parent)
            self.app = app_service
            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)

            header = QLabel("来源管理")
            header.setFont(QFont("", 18, QFont.Bold))
            header.setStyleSheet("color: #1a73e8;")
            layout.addWidget(header)

            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "名称", "类型", "分类", "状态"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

            # Health info
            self.health_label = QLabel()
            self.health_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(self.health_label)

            refresh_btn = QPushButton("刷新来源")
            refresh_btn.setFixedHeight(36)
            refresh_btn.setStyleSheet("QPushButton { background: #1a73e8; color: white; border: none; border-radius: 8px; padding: 0 16px; } QPushButton:hover { background: #1557b0; }")
            refresh_btn.clicked.connect(self.refresh)
            layout.addWidget(refresh_btn)

        def refresh(self):
            sources = self.app.source_mgr.list_sources()
            health = self.app.source_health.get_health()
            health_map = {h["id"]: h for h in health}

            self.table.setRowCount(len(sources))
            for i, s in enumerate(sources):
                self.table.setItem(i, 0, QTableWidgetItem(str(s.get("id", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(s.get("name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(s.get("type", "")))
                self.table.setItem(i, 3, QTableWidgetItem(s.get("category", "")))

                h = health_map.get(s["id"], {})
                status = "正常" if s.get("enabled") else "禁用"
                if h.get("paused"):
                    status = "已暂停"
                elif h.get("failure_count", 0) > 0:
                    status = f"失败{h['failure_count']}次"
                item = QTableWidgetItem(status)
                item.setForeground(QColor("#34a853") if status == "正常" else QColor("#ea4335") if "失败" in status else QColor("#666"))
                self.table.setItem(i, 4, item)

            self.health_label.setText(f"共 {len(sources)} 个数据源")


    class MainWindow(QMainWindow):
        """Main application window with sidebar navigation."""
        def __init__(self, app_service: AppService):
            super().__init__()
            self.app = app_service
            self.setWindowTitle("News Intelligence Desktop - 个人每日信息中枢")
            self.setMinimumSize(1200, 800)
            self._setup_ui()
            self._connect_signals()

        def _setup_ui(self):
            # Central widget
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QHBoxLayout(central)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Sidebar
            sidebar = QFrame()
            sidebar.setFixedWidth(220)
            sidebar.setStyleSheet("QFrame { background: #f8f9fa; border-right: 1px solid #e0e0e0; }")
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.setContentsMargins(12, 16, 12, 16)
            sidebar_layout.setSpacing(4)

            # App title
            title = QLabel("News Intelligence")
            title.setFont(QFont("", 14, QFont.Bold))
            title.setStyleSheet("color: #1a73e8; padding: 8px 12px;")
            sidebar_layout.addWidget(title)

            subtitle = QLabel("个人每日信息中枢")
            subtitle.setStyleSheet("color: #666; font-size: 12px; padding: 0 12px 12px 12px;")
            sidebar_layout.addWidget(subtitle)

            # Navigation buttons
            self.nav_buttons = []
            nav_items = [
                ("首页总览", "home"),
                ("天气预报", "cloud"),
                ("地震动态", "activity"),
                ("新闻资讯", "newspaper"),
                ("每日语录", "heart"),
                ("技术变化", "code"),
                ("API 工具箱", "tool"),
                ("搜索", "search"),
                ("个人中心", "user"),
                ("来源管理", "database"),
            ]

            for text, icon in nav_items:
                btn = SidebarButton(text, icon)
                sidebar_layout.addWidget(btn)
                self.nav_buttons.append(btn)

            sidebar_layout.addStretch()

            # Collect button
            self.collect_btn = QPushButton("  一键采集数据")
            self.collect_btn.setFixedHeight(44)
            self.collect_btn.setCursor(Qt.PointingHandCursor)
            self.collect_btn.setStyleSheet("""
                QPushButton {
                    background: #34a853;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #2d8e47; }
                QPushButton:pressed { background: #247a3d; }
                QPushButton:disabled { background: #ccc; }
            """)
            sidebar_layout.addWidget(self.collect_btn)

            main_layout.addWidget(sidebar)

            # Content area
            self.stack = QStackedWidget()
            self.stack.setStyleSheet("QStackedWidget { background: white; }")

            # Create pages
            self.home_page = HomePage(self.app)
            self.weather_page = WeatherPage(self.app)
            self.earthquake_page = EarthquakePage(self.app)
            self.news_page = NewsPage(self.app)
            self.quote_page = QuotePage(self.app)
            self.tech_page = TechChangesPage(self.app)
            self.toolbox_page = ToolboxPage(self.app)
            self.search_page = SearchPage(self.app)
            self.personal_page = PersonalPage(self.app)
            self.sources_page = SourcesPage(self.app)

            self.stack.addWidget(self.home_page)
            self.stack.addWidget(self.weather_page)
            self.stack.addWidget(self.earthquake_page)
            self.stack.addWidget(self.news_page)
            self.stack.addWidget(self.quote_page)
            self.stack.addWidget(self.tech_page)
            self.stack.addWidget(self.toolbox_page)
            self.stack.addWidget(self.search_page)
            self.stack.addWidget(self.personal_page)
            self.stack.addWidget(self.sources_page)

            main_layout.addWidget(self.stack)

            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("就绪")

            # Set first button checked
            self.nav_buttons[0].setChecked(True)

        def _connect_signals(self):
            # Navigation
            for i, btn in enumerate(self.nav_buttons):
                btn.clicked.connect(lambda checked, idx=i: self._navigate(idx))

            # Collect button
            self.collect_btn.clicked.connect(self._start_collect)

        def _navigate(self, index: int):
            # Uncheck all buttons
            for btn in self.nav_buttons:
                btn.setChecked(False)
            # Check selected button
            self.nav_buttons[index].setChecked(True)
            # Switch page
            self.stack.setCurrentIndex(index)

            # Refresh page content
            pages = [
                self.home_page, self.weather_page, self.earthquake_page,
                self.news_page, self.quote_page, self.tech_page,
                self.toolbox_page, self.search_page, self.personal_page,
                self.sources_page,
            ]
            if hasattr(pages[index], 'refresh'):
                pages[index].refresh()

        def _start_collect(self):
            self.collect_btn.setEnabled(False)
            self.collect_btn.setText("  采集中...")
            self.status_bar.showMessage("正在采集数据...")

            self.worker = CollectWorker(self.app)
            self.worker.finished.connect(self._on_collect_done)
            self.worker.error.connect(self._on_collect_error)
            self.worker.start()

        def _on_collect_done(self, result: dict):
            self.collect_btn.setEnabled(True)
            self.collect_btn.setText("  一键采集数据")
            msg = f"采集完成: 天气{result.get('weather',0)} 地震{result.get('earthquake',0)} 新闻{result.get('news',0)} 热点{result.get('hot',0)} 技术{result.get('tech',0)}"
            self.status_bar.showMessage(msg)
            if result.get("errors"):
                QMessageBox.warning(self, "采集警告", f"部分采集失败:\n" + "\n".join(result["errors"]))

        def _on_collect_error(self, error: str):
            self.collect_btn.setEnabled(True)
            self.collect_btn.setText("  一键采集数据")
            self.status_bar.showMessage("采集失败")
            QMessageBox.critical(self, "采集错误", error)


def run_gui(data_dir: Path | None = None) -> int:
    """Run the GUI application."""
    if not HAS_QT:
        print("错误: PySide6 未安装。请运行: pip install PySide6")
        print("或者使用控制台模式: --console")
        return 1

    settings = AppSettings.load(data_dir)
    app_service = AppService(settings)
    app_service.initialize()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set app palette for modern look
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
    palette.setColor(QPalette.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.Button, QColor(248, 249, 250))
    palette.setColor(QPalette.ButtonText, QColor(51, 51, 51))
    palette.setColor(QPalette.Highlight, QColor(26, 115, 232))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow(app_service)
    window.show()

    return app.exec()
