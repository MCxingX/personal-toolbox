# News Intelligence Desktop

本地个人每日信息中枢与 API 工具箱。

## 功能

- 首页信息中枢：今日总览、技术变化、重要新闻、政策变化、本地事件、热点吃瓜、天气地震、每日语录
- 天气预报：Open-Meteo 免费天气 API
- 地震动态：USGS 全球地震数据
- 新闻资讯：RSS 聚合、韩小韩 API、GDELT 全球新闻
- 热点报告：多来源聚合、关键词频率、趋势方向
- 猎奇内容：奇闻、趣闻、争议内容分级展示
- 技术变化：AI、开源、框架、云服务、安全、大厂动态
- 每日语录：开心、别委屈、加油、冷静、幽默、技术人专属
- API 工具箱：韩小韩、枫雨、天行、聚合、Open-Meteo、USGS、GDELT
- 特别收藏网页页签：按域名、精确 URL、路径前缀匹配
- 个人关注清单：关键词、公司、技术栈、城市、政策主题、人物
- 晨报/晚报：每日固定时间生成摘要
- 本地全文搜索：SQLite FTS5
- 数据导出：Markdown、HTML、JSON、CSV
- 备份与恢复
- 可信度解释
- 来源健康度
- 隐私模式
- 离线模式

## 快速开始

### 安装依赖

```bash
pip install requests feedparser beautifulsoup4 jieba apscheduler
pip install PySide6  # 图形界面（可选）
```

### 启动应用

```bash
# 图形界面（推荐，点击按钮即可）
python3 -m news_intelligence_desktop.app.main

# 控制台交互界面
python3 -m news_intelligence_desktop.app.main --console

# JSON 输出首页
python3 -m news_intelligence_desktop.app.main --json
```

### 图形界面功能

启动后，左侧有导航栏，点击按钮即可切换页面：

| 按钮 | 功能 |
|------|------|
| 首页总览 | 查看今日信息汇总卡片 |
| 天气预报 | 查看 7 天天气 |
| 地震动态 | 查看全球地震 |
| 新闻资讯 | 浏览新闻，支持分类筛选 |
| 每日语录 | 获取鼓励/幽默/技术语录 |
| 技术变化 | 追踪技术更新 |
| API 工具箱 | 查看可用 API |
| 搜索 | 全文搜索本地内容 |
| 个人中心 | 收藏、稍后看、隐私模式 |
| 来源管理 | 查看数据源状态 |
| 一键采集 | 后台自动采集所有数据 |

## 命令行用法

```bash
# 采集数据
python3 -m news_intelligence_desktop.app.main collect

# 特别收藏
python3 -m news_intelligence_desktop.app.main add-special 示例技术 https://example.com/tech

# 搜索
python3 -m news_intelligence_desktop.app.main search AI

# 晨报
python3 -m news_intelligence_desktop.app.main brief 晨报

# 导出
python3 -m news_intelligence_desktop.app.main export-article 1 ./exports/article.md

# 备份
python3 -m news_intelligence_desktop.app.main backup ./backups/news.sqlite3

# 隐私模式
python3 -m news_intelligence_desktop.app.main privacy on

# 关注清单
python3 -m news_intelligence_desktop.app.main add-watchlist AI关注 tech_stack AI 模型

# 语录
python3 -m news_intelligence_desktop.app.main add-quote "今天也要加油" --style encourage

# API 目录
python3 -m news_intelligence_desktop.app.main list-apis

# 来源健康
python3 -m news_intelligence_desktop.app.main source-health

# 通知
python3 -m news_intelligence_desktop.app.main notifications

# 阅读状态
python3 -m news_intelligence_desktop.app.main read 1
python3 -m news_intelligence_desktop.app.main favorite 1

# 收藏列表
python3 -m news_intelligence_desktop.app.main collection favorite

# 重建索引
python3 -m news_intelligence_desktop.app.main rebuild-index

# 添加来源
python3 -m news_intelligence_desktop.app.main add-source 36氪 rss news https://36kr.com/feed

# 列出 RSS 源
python3 -m news_intelligence_desktop.app.main list-feeds

# 检测技术变化
python3 -m news_intelligence_desktop.app.main tech-detect

# 政策管理
python3 -m news_intelligence_desktop.app.main policy-add "数据安全法" --issuer 全国人大 --region national
python3 -m news_intelligence_desktop.app.main policy-list --region national
```

## 测试

```bash
python3 -m unittest discover -s tests
```

## 打包 Windows exe

```bash
pyinstaller news_intelligence.spec
```

## 数据目录

默认：`~/.news_intelligence_desktop`

可通过 `--data-dir` 指定：

```bash
python3 -m news_intelligence_desktop.app.main --data-dir /tmp/news-intel --console
```

## 项目结构

```
news_intelligence_desktop/
├── app/
│   ├── __init__.py
│   └── main.py              # 主入口（命令行解析）
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置管理
├── connectors/
│   ├── __init__.py          # 基础连接器
│   ├── weather_earthquake.py # 天气/地震
│   ├── news_rss.py          # RSS/韩小韩/GDELT
│   ├── quote_rss.py         # 语录/RSS
│   ├── optional_api.py      # 天行/聚合
│   ├── web_page.py          # 网页抓取
│   ├── generic_api.py       # 通用 API
│   └── extra_sources.py     # 扩展数据源
├── services/
│   ├── __init__.py
│   ├── app_service.py       # 应用服务（组装）
│   ├── collector.py         # 数据采集
│   ├── source_manager.py    # 来源管理
│   ├── daily_quote.py       # 每日语录
│   ├── tech_change.py       # 技术变化
│   ├── home_dashboard.py    # 首页仪表盘
│   ├── brief.py             # 晨报/晚报
│   ├── notification.py      # 通知管理
│   ├── api_toolbox.py       # API 工具箱
│   ├── personal.py          # 个人中心
│   ├── enhanced_services.py # 搜索/导出/备份
│   ├── policy_capture.py    # 政策/抓包/地区
│   └── oddity.py            # 猎奇内容
├── storage/
│   ├── __init__.py
│   ├── database.py          # 数据库 Schema
│   └── repository.py        # 数据访问层
├── analysis/
│   └── __init__.py          # 关键词/情感/分类
└── ui/
    ├── __init__.py
    ├── console.py           # 控制台 UI
    ├── gui.py               # PySide6 图形界面
    └── qt_app.py            # Qt 应用（旧版）
```

## 技术栈

- Python 3.11+
- SQLite FTS5（全文搜索）
- requests / feedparser / beautifulsoup4
- jieba（中文分词）
- APScheduler（定时任务）
- PySide6（图形界面，可选）
- PyInstaller（打包 exe）

---

## 🔑 第三方 API 配置

### TopHubData 热榜 API

本项目支持通过 TopHubData API 获取全网各平台热榜数据（微博、知乎、抖音、B站等）。

#### 获取 API Key

1. 访问 [https://www.tophubdata.com](https://www.tophubdata.com)
2. 注册账号
3. 在个人中心获取 API Key

#### 在软件中配置

1. 打开应用，点击菜单 **「设置」→「API 配置」**
2. 在 **TopHub API Key** 栏填入你的 Key
3. 点击 **「保存」**

> **安全提示**：API Key 仅存储在您的本地 SQLite 数据库中，不会硬编码到代码里，也不会上传到任何服务器。即使项目代码公开在 GitHub，您的 Key 也是安全的。

#### 接口说明

| 接口 | 限制 | 费用 |
|------|------|------|
| 全部榜单列表 | 每天 1000 次 | 免费 |
| 榜单详情 | 每天 1000 次 | 免费 |

#### 可用榜单（示例）

| 榜单 | 说明 |
|------|------|
| 微博热搜 | 微博实时热搜话题 |
| 知乎热榜 | 知乎每日热榜 |
| 抖音热榜 | 抖音热门话题 |
| B站热榜 | B站热门视频 |
| 百度热搜 | 百度热搜榜 |
| 今日头条 | 头条热门资讯 |
| 豆瓣热榜 | 豆瓣热门话题 |

> 完整榜单列表请以 TopHubData 官网为准：[https://www.tophubdata.com/documentation](https://www.tophubdata.com/documentation)
