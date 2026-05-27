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
        'news_intelligence_desktop.app.main',
        'news_intelligence_desktop.config.settings',
        'news_intelligence_desktop.storage.database',
        'news_intelligence_desktop.storage.repository',
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
        'news_intelligence_desktop.connectors.weather_earthquake',
        'news_intelligence_desktop.connectors.news_rss',
        'news_intelligence_desktop.analysis',
        'news_intelligence_desktop.ui.console',
        'requests', 'feedparser', 'bs4', 'jieba', 'apscheduler',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
