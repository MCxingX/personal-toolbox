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

## 运行

```bash
# 控制台交互界面
python3 -m news_intelligence_desktop.app.main --console

# JSON 输出首页
python3 -m news_intelligence_desktop.app.main --json

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
