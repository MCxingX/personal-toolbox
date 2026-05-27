from __future__ import annotations

from news_intelligence_desktop.services.app_service import AppService


def run_qt_app(app: AppService) -> int:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QMainWindow, QVBoxLayout, QWidget

    qt_app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle("News Intelligence Desktop")
    dashboard = app.home_dashboard()

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(QLabel(dashboard["title"]))
    cards = QListWidget()
    for card in dashboard["cards"]:
        cards.addItem(f"{card['name']} - {card['summary']}")
    layout.addWidget(cards)
    window.setCentralWidget(container)
    window.resize(960, 640)
    window.show()
    return qt_app.exec()
