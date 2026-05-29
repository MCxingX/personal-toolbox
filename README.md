# News Intelligence Desktop

本地运行的个人信息中枢。它把新闻、热榜、天气、地震、技术动态、语录、收藏和通知集中到一个桌面应用里，数据存放在本机 SQLite 数据库。

## 核心功能

- 首页总览：今日早晚报、国内新闻、技术动态、政策法规、财经金融、安全资讯、天气地震和每日语录。
- 多源采集：RSS、UAPI 热榜、TopHubData、网页来源、HAR/HTML/JSON 抓包导入。
- 板块管理：社交热榜、新闻资讯、科技社区、兴趣圈子、音乐游戏可单独启用或关闭。
- 个人能力：收藏、阅读历史、关注清单、关键词订阅、通知中心、全文搜索。
- 数据安全：API Key 仅保存在本地数据库，支持设置导入导出、数据保留策略和隐私模式。
- Windows 打包：内置 PyInstaller 配置和 `build.bat`。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动桌面应用
python3 -m news_intelligence_desktop.app.main

# 采集全部数据
python3 -m news_intelligence_desktop.app.main collect
```

Windows 用户也可以双击 `启动.bat` 启动应用。

## 常用命令

```bash
# 控制台模式
python3 -m news_intelligence_desktop.app.main --console

# JSON 输出首页
python3 -m news_intelligence_desktop.app.main --json

# 搜索本地内容
python3 -m news_intelligence_desktop.app.main search AI

# 查看通知
python3 -m news_intelligence_desktop.app.main notifications

# 添加 RSS 来源
python3 -m news_intelligence_desktop.app.main add-source 36氪 rss news https://36kr.com/feed

# 备份数据库
python3 -m news_intelligence_desktop.app.main backup ./backups/news.sqlite3
```

## API 配置

TopHubData API Key 在应用设置页填写，保存后进入本地 SQLite 数据库。

```text
设置 -> API Key 配置 -> TopHub API Key -> 保存
```

UAPI 热榜默认走公开接口，并按本地缓存策略减少请求次数。第三方 Key、板块开关和来源配置都可以在设置页导入导出。

## 测试

```bash
python3 -m pytest tests/ -q
python3 -m compileall news_intelligence_desktop
```

## Windows 打包

```bash
build.bat
```

或手动执行：

```bash
pyinstaller news_intelligence.spec
```

## 数据目录

默认数据目录：`~/.news_intelligence_desktop`

可通过 `--data-dir` 指定：

```bash
python3 -m news_intelligence_desktop.app.main --data-dir /tmp/news-intel --console
```

## 技术栈

- Python 3.11+
- Tkinter 桌面界面
- SQLite / FTS5
- requests / feedparser / beautifulsoup4 / lxml
- jieba 中文分词
- PyInstaller Windows 打包
