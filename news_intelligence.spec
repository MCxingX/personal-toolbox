# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / 'news_intelligence_desktop' / 'app' / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'news_intelligence_desktop' / 'config'), 'news_intelligence_desktop/config'),
        (str(root / 'news_intelligence_desktop' / 'storage'), 'news_intelligence_desktop/storage'),
        (str(root / 'news_intelligence_desktop' / 'services'), 'news_intelligence_desktop/services'),
        (str(root / 'news_intelligence_desktop' / 'connectors'), 'news_intelligence_desktop/connectors'),
        (str(root / 'news_intelligence_desktop' / 'analysis'), 'news_intelligence_desktop/analysis'),
        (str(root / 'news_intelligence_desktop' / 'ui'), 'news_intelligence_desktop/ui'),
    ],
    hiddenimports=[
        # 核心模块
        'news_intelligence_desktop.app.main',
        'news_intelligence_desktop.config.settings',
        'news_intelligence_desktop.config.china_cities',
        'news_intelligence_desktop.storage.database',
        'news_intelligence_desktop.storage.repository',
        'news_intelligence_desktop.storage.settings_db',

        # 服务模块
        'news_intelligence_desktop.services.app_service',
        'news_intelligence_desktop.services.source_manager',
        'news_intelligence_desktop.services.collector',
        'news_intelligence_desktop.services.daily_quote',
        'news_intelligence_desktop.services.tech_change',
        'news_intelligence_desktop.services.home_dashboard',
        'news_intelligence_desktop.services.brief',
        'news_intelligence_desktop.services.notification',
        'news_intelligence_desktop.services.api_toolbox',
        'news_intelligence_desktop.services.personal',
        'news_intelligence_desktop.services.enhanced_services',
        'news_intelligence_desktop.services.oddity',
        'news_intelligence_desktop.services.policy_capture',
        'news_intelligence_desktop.services.news_quality',
        'news_intelligence_desktop.services.rate_limiter',
        'news_intelligence_desktop.services.data_retention',
        'news_intelligence_desktop.services.settings_io',

        # 连接器模块
        'news_intelligence_desktop.connectors.weather_earthquake',
        'news_intelligence_desktop.connectors.news_rss',
        'news_intelligence_desktop.connectors.web_page',
        'news_intelligence_desktop.connectors.packet_capture',
        'news_intelligence_desktop.connectors.tophub',
        'news_intelligence_desktop.connectors.tophub_daily',
        'news_intelligence_desktop.connectors.uapi_connector',
        'news_intelligence_desktop.connectors.sections',
        'news_intelligence_desktop.connectors.generic_api',
        'news_intelligence_desktop.connectors.optional_api',
        'news_intelligence_desktop.connectors.extra_sources',
        'news_intelligence_desktop.connectors.quote_rss',

        # 分析模块
        'news_intelligence_desktop.analysis',

        # UI 模块
        'news_intelligence_desktop.ui.tk_app',
        'news_intelligence_desktop.ui.console',

        # 第三方依赖
        'requests', 'feedparser', 'bs4', 'jieba',
        'lxml', 'uapi_sdk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2', 'torch'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='NewsIntelligence',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台用于日志输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / 'news_intelligence_desktop' / 'resources' / 'icon.ico') if (root / 'news_intelligence_desktop' / 'resources' / 'icon.ico').exists() else None,
)
