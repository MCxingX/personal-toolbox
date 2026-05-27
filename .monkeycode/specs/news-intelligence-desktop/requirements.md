# Requirements Document

## Introduction

本需求文档定义一个 Python 本地桌面资讯聚合与舆情观察程序。系统面向个人用户，聚合天气预报、地震动态、国际新闻、国内新闻、热点报告、猎奇资讯和关键词相关评论线索，并为后续打包为 Windows exe 文件提供明确的功能边界。

系统的数据来源以公开 API、RSS Feed、授权开放数据源和用户手动配置的数据源为主。系统在抓取网页内容时遵守站点服务条款、robots 规则、访问频率限制和版权要求。系统展示摘要、来源链接、发布时间、热度指标和舆情分析结果，完整正文以跳转原始来源为主。

## Glossary

- **系统**: Python 本地桌面资讯聚合与舆情观察程序。
- **资讯源**: 新闻 API、RSS Feed、公开开放数据接口或用户配置的合规网页源。
- **热点报告**: 系统基于近期资讯聚合、关键词频率、来源数量和时间趋势生成的简要分析结果。
- **舆情线索**: 与关键词相关的新闻摘要、公开评论摘要、情绪倾向、讨论热词和来源链接。
- **猎奇资讯**: 异闻、科技趣闻、社会奇闻、特殊事件等非主流热点资讯分类。
- **本地数据库**: 存储资讯条目、来源配置、关键词、抓取日志和用户偏好的 SQLite 数据库。
- **数据采集任务**: 按时间计划执行的数据拉取、解析、清洗、去重和入库流程。

## Requirements

### Requirement 1: 桌面应用启动与导航

**User Story:** AS 个人用户, I want 打开本地软件查看分类资讯, so that 我可以在一个桌面程序中集中浏览新闻、天气、地震和热点内容。

#### Acceptance Criteria

1. WHEN 用户启动系统, 系统 SHALL 显示桌面主窗口和主要模块入口。
2. WHEN 用户选择任一模块入口, 系统 SHALL 展示对应模块的数据列表、刷新状态和筛选条件。
3. WHILE 系统正在采集数据, 系统 SHALL 展示采集进度、当前来源名称和可读状态提示。
4. IF 系统首次启动且本地数据库为空, 系统 SHALL 创建默认来源配置和基础分类配置。
5. IF 系统启动时发现本地数据库不可用, 系统 SHALL 显示修复提示并保留可导出错误日志。

### Requirement 2: 数据源配置与管理

**User Story:** AS 个人用户, I want 配置和启用不同资讯源, so that 我可以控制系统从哪些公开来源获取内容。

#### Acceptance Criteria

1. WHEN 用户打开来源管理页面, 系统 SHALL 展示来源名称、类型、分类、启用状态、调用限制和最后采集时间。
2. WHEN 用户新增资讯源, 系统 SHALL 校验来源 URL、来源类型、分类归属和必要认证字段。
3. WHEN 用户停用资讯源, 系统 SHALL 在后续采集任务中跳过该资讯源。
4. IF 资讯源需要 API Key, 系统 SHALL 将密钥保存在本地配置文件或系统凭据存储中。
5. IF 资讯源返回限流或认证错误, 系统 SHALL 记录错误原因并暂停该来源的短周期重试。

### Requirement 3: 天气预报模块

**User Story:** AS 个人用户, I want 查看指定城市或坐标的天气预报, so that 我可以快速了解近期天气变化。

#### Acceptance Criteria

1. WHEN 用户配置城市或坐标, 系统 SHALL 查询地理编码并保存用户选择的位置。
2. WHEN 用户打开天气模块, 系统 SHALL 展示当前天气、逐小时预报、未来多日预报和更新时间。
3. WHEN 用户刷新天气数据, 系统 SHALL 从公开天气接口获取最新天气预报。
4. IF 天气接口请求失败, 系统 SHALL 展示上次成功获取的数据和失败原因。
5. IF 用户配置多个位置, 系统 SHALL 支持在天气模块中切换位置。

### Requirement 4: 地震新闻与地震动态模块

**User Story:** AS 个人用户, I want 查看近期地震动态和相关新闻, so that 我可以关注全球或指定区域的地震事件。

#### Acceptance Criteria

1. WHEN 用户打开地震模块, 系统 SHALL 展示近期地震事件列表、震级、地点、深度、时间和来源链接。
2. WHEN 用户设置震级阈值或区域范围, 系统 SHALL 按条件过滤地震事件。
3. WHEN 系统获取到高震级事件, 系统 SHALL 在热点区域突出显示该事件。
4. IF 地震接口返回空结果, 系统 SHALL 展示空状态和当前筛选条件。
5. IF 地震事件存在关联新闻, 系统 SHALL 展示关联新闻摘要和原始链接。

### Requirement 5: 国内新闻与国际新闻模块

**User Story:** AS 个人用户, I want 浏览国内新闻和国际新闻, so that 我可以快速查看不同地区的最新资讯。

#### Acceptance Criteria

1. WHEN 系统执行新闻采集任务, 系统 SHALL 按国内新闻、国际新闻和来源语言保存资讯条目。
2. WHEN 用户打开国内新闻模块, 系统 SHALL 展示国内资讯列表、发布时间、来源、摘要和链接。
3. WHEN 用户打开国际新闻模块, 系统 SHALL 展示国际资讯列表、发布时间、来源、摘要和链接。
4. WHEN 用户使用排序控件, 系统 SHALL 按发布时间、来源数量或热度评分排序。
5. IF 新闻条目重复, 系统 SHALL 合并重复条目并保留多个来源链接。

### Requirement 6: 猎奇资讯模块

**User Story:** AS 个人用户, I want 查看猎奇和非主流热点内容, so that 我可以发现近期特别事件和趣闻。

#### Acceptance Criteria

1. WHEN 系统采集资讯条目, 系统 SHALL 根据分类规则、关键词规则和来源标签识别猎奇资讯。
2. WHEN 用户打开猎奇模块, 系统 SHALL 展示猎奇资讯列表、类别标签、摘要、来源和发布时间。
3. WHEN 用户调整猎奇关键词, 系统 SHALL 使用用户关键词更新后续分类结果。
4. IF 条目涉及低可信来源, 系统 SHALL 标注来源可信度提示。
5. IF 条目包含敏感或争议性内容, 系统 SHALL 以摘要和来源链接形式展示。

### Requirement 7: 热点报告模块

**User Story:** AS 个人用户, I want 查看最近热点报告, so that 我可以快速理解近期讨论集中的主题。

#### Acceptance Criteria

1. WHEN 用户打开热点报告模块, 系统 SHALL 展示指定时间窗口内的热点主题、代表资讯、来源数量和趋势方向。
2. WHEN 系统生成热点报告, 系统 SHALL 基于标题、摘要、关键词、发布时间和来源数量计算主题热度。
3. WHEN 用户切换时间窗口, 系统 SHALL 重新生成对应时间范围的热点报告。
4. IF 热点主题缺少足够来源支撑, 系统 SHALL 降低主题可信度评分。
5. IF 用户导出热点报告, 系统 SHALL 生成本地 Markdown 或 HTML 报告文件。

### Requirement 8: 关键词检索与舆情线索模块

**User Story:** AS 个人用户, I want 输入关键词并查看相关新闻、评论线索和舆论倾向, so that 我可以追踪指定话题的公开讨论情况。

#### Acceptance Criteria

1. WHEN 用户输入关键词并提交检索, 系统 SHALL 查询本地数据库和已配置的公开搜索接口。
2. WHEN 系统返回关键词结果, 系统 SHALL 展示相关资讯、发布时间、来源、摘要、热词和链接。
3. WHEN 结果包含公开评论摘要或讨论片段, 系统 SHALL 展示评论来源、发布时间、摘要和链接。
4. WHEN 系统分析舆情倾向, 系统 SHALL 输出正向、中性、负向和未知四类统计结果。
5. IF 评论来源需要登录、绕过限制或违反来源规则, 系统 SHALL 跳过该来源并记录跳过原因。

### Requirement 9: 数据采集、清洗和去重

**User Story:** AS 个人用户, I want 系统自动更新近期数据, so that 我可以减少手动搜索和整理工作。

#### Acceptance Criteria

1. WHEN 到达计划采集时间, 系统 SHALL 执行启用来源的数据采集任务。
2. WHEN 系统接收原始数据, 系统 SHALL 标准化标题、摘要、来源、发布时间、URL、分类和语言字段。
3. WHEN 系统发现相同 URL 或高度相似标题, 系统 SHALL 将条目标记为重复候选并执行合并策略。
4. IF 单个来源连续失败达到配置阈值, 系统 SHALL 暂停该来源并提示用户检查配置。
5. IF 采集任务被用户取消, 系统 SHALL 保存已完成结果并记录取消时间。

### Requirement 10: 本地存储与隐私

**User Story:** AS 个人用户, I want 数据和配置保存在本地, so that 我可以控制自己的关键词、配置和历史记录。

#### Acceptance Criteria

1. WHEN 系统保存资讯条目, 系统 SHALL 将结构化数据写入本地 SQLite 数据库。
2. WHEN 系统保存用户配置, 系统 SHALL 将非敏感配置写入本地配置文件。
3. WHEN 系统保存敏感配置, 系统 SHALL 使用本地凭据存储或加密文件保存敏感字段。
4. WHEN 用户请求清理历史数据, 系统 SHALL 按时间范围和分类清理本地缓存数据。
5. IF 数据库迁移失败, 系统 SHALL 保留迁移前备份并展示错误日志路径。

### Requirement 11: 打包为 Windows exe

**User Story:** AS 个人用户, I want 将 Python 程序打包为 Windows exe 文件, so that 我可以在 Windows 设备上直接运行本地软件。

#### Acceptance Criteria

1. WHEN 开发进入发布阶段, 系统 SHALL 提供 PyInstaller 打包配置和资源文件清单。
2. WHEN 执行打包命令, 系统 SHALL 生成可运行的 Windows exe 文件和必要资源目录。
3. WHEN 用户首次运行 exe 文件, 系统 SHALL 在用户数据目录创建数据库和配置文件。
4. IF exe 运行缺少运行资源, 系统 SHALL 展示可读错误并写入日志文件。
5. IF 系统依赖 API Key, 系统 SHALL 在首次运行向用户提示配置方式。

### Requirement 12: 合规与安全边界

**User Story:** AS 个人用户, I want 系统使用合规数据来源, so that 我可以降低版权、平台规则和账号风险。

#### Acceptance Criteria

1. WHEN 系统配置默认来源, 系统 SHALL 使用公开 API、RSS Feed 和明确授权的开放数据源。
2. WHEN 用户添加网页来源, 系统 SHALL 展示合规提示和访问频率配置。
3. WHEN 来源规则禁止抓取或需要登录权限, 系统 SHALL 跳过该来源。
4. WHEN 系统展示第三方内容, 系统 SHALL 显示来源名称、原始链接和发布时间。
5. IF 用户配置高频请求参数, 系统 SHALL 限制请求频率并提示合理范围。

### Requirement 13: 第三方网页接入模块

**User Story:** AS 个人用户, I want 添加第三方公开网页作为资讯来源, so that 我可以把自己常看的网页内容接入本地软件统一查看。

#### Acceptance Criteria

1. WHEN 用户添加第三方网页来源, 系统 SHALL 保存网页名称、URL、分类、编码、解析规则和刷新频率。
2. WHEN 用户测试网页来源, 系统 SHALL 拉取公开页面内容并展示标题、摘要、发布时间候选和链接候选。
3. WHEN 用户配置解析规则, 系统 SHALL 支持 CSS Selector、XPath 和正文自动提取三种方式。
4. IF 页面需要登录、验证码、设备校验或访问授权, 系统 SHALL 跳过该页面并展示跳过原因。
5. IF 页面返回结构变化导致解析失败, 系统 SHALL 保留最近一次成功解析结果并提示用户调整规则。

### Requirement 14: 本地抓包文件导入与展示模块

**User Story:** AS 个人用户, I want 导入自己从浏览器导出的抓包文件, so that 我可以在本地软件中查看其中的公开资讯、热点和评论片段。

#### Acceptance Criteria

1. WHEN 用户导入 HAR、HTML 或 JSON 文件, 系统 SHALL 在本地解析文件并展示可识别的请求、响应摘要和候选内容。
2. WHEN 系统解析 HAR 文件, 系统 SHALL 提取 URL、状态码、MIME 类型、响应时间、响应大小和文本响应片段。
3. WHEN 响应内容包含资讯条目、评论片段或热点列表, 系统 SHALL 将候选内容映射为资讯条目、评论线索或热点候选。
4. WHEN 用户确认候选内容入库, 系统 SHALL 保存来源文件名、导入时间、原始 URL、摘要和解析字段。
5. IF 导入文件包含 Cookie、Authorization、Token 或个人敏感字段, 系统 SHALL 在入库前执行脱敏并提示用户确认。
6. IF 导入内容来自私有页面、登录态页面或受限接口, 系统 SHALL 标记为本地临时查看内容并限制自动刷新。

### Requirement 15: 猎奇内容分级与本地展示

**User Story:** AS 个人用户, I want 在本地查看猎奇内容并看到风险提示, so that 我可以区分趣闻、争议内容和低可信内容。

#### Acceptance Criteria

1. WHEN 系统识别猎奇内容, 系统 SHALL 根据关键词、来源可信度和内容类别生成猎奇标签。
2. WHEN 用户打开猎奇详情, 系统 SHALL 展示标题、摘要、来源、原始链接、标签和可信度提示。
3. WHEN 内容包含惊悚、事故、争议或低可信特征, 系统 SHALL 在详情页展示内容提示。
4. WHEN 用户调整猎奇展示偏好, 系统 SHALL 按偏好过滤或折叠对应内容。
5. IF 内容缺少可靠来源支撑, 系统 SHALL 降低可信度评分并展示来源数量。

### Requirement 16: 新闻订阅与本地推送

**User Story:** AS 个人用户, I want 系统根据我的兴趣和热点变化推送新闻, so that 我可以及时看到重要资讯和关键词相关内容。

#### Acceptance Criteria

1. WHEN 用户创建订阅规则, 系统 SHALL 保存关键词、分类、来源、最低热度、最低可信度和推送频率。
2. WHEN 新资讯匹配订阅规则, 系统 SHALL 生成一条待推送通知并记录匹配原因。
3. WHEN 系统推送通知, 系统 SHALL 展示标题、摘要、来源、分类、热度评分和打开详情入口。
4. WHEN 同一主题出现多条重复资讯, 系统 SHALL 合并为一条聚合推送并展示来源数量。
5. IF 当前时间处于免打扰时段, 系统 SHALL 延迟普通通知并允许紧急通知继续展示。
6. IF 用户对某条推送选择忽略或屏蔽, 系统 SHALL 更新订阅偏好并减少相似内容推送。

### Requirement 17: 推送中心与推送历史

**User Story:** AS 个人用户, I want 查看历史推送和调整推送策略, so that 我可以控制本地软件的信息打扰程度。

#### Acceptance Criteria

1. WHEN 用户打开推送中心, 系统 SHALL 展示未读推送、已读推送、聚合推送和被延迟推送。
2. WHEN 用户点击推送记录, 系统 SHALL 打开对应资讯详情、热点报告或关键词舆情结果。
3. WHEN 用户调整免打扰时段, 系统 SHALL 使用新的时间范围控制后续通知展示。
4. WHEN 用户调整推送渠道, 系统 SHALL 支持桌面通知、应用内红点和系统托盘提醒。
5. IF 推送发送失败, 系统 SHALL 保留推送记录并展示失败原因。

### Requirement 18: 全领域今日概览

**User Story:** AS 个人用户, I want 一次性看到今天各领域发生的重要信息, so that 我可以快速了解政策、金融、IT、互联网、娱乐、事故和安全等领域动态。

#### Acceptance Criteria

1. WHEN 用户打开今日概览, 系统 SHALL 按政策、金融、IT、互联网、娱乐、社会、事故、交通、天气、地震、安全和网络安全频道展示今日要点。
2. WHEN 系统生成今日概览, 系统 SHALL 为每个频道输出重要事件、代表来源、摘要、地区、时间和可信度评分。
3. WHEN 某频道无足够新内容, 系统 SHALL 展示最近更新时间和空状态说明。
4. WHEN 用户点击任一概览条目, 系统 SHALL 打开详情页并展示来源链接、相关资讯和同主题聚合。
5. IF 某条资讯被多个频道命中, 系统 SHALL 归入主频道并在详情中展示关联频道。

### Requirement 19: 政策信息与区域切换

**User Story:** AS 个人用户, I want 查看最新政策和本地政策, so that 我可以及时了解全国和指定地区的政策变化。

#### Acceptance Criteria

1. WHEN 用户设置关注区域, 系统 SHALL 保存国家、省、市、区县和自定义地区配置。
2. WHEN 系统采集政策信息, 系统 SHALL 按全国、省级、市级、区县级和行业政策归类。
3. WHEN 用户切换区域, 系统 SHALL 展示该区域政策、上级地区政策和全国政策摘要。
4. WHEN 系统发现最新政策, 系统 SHALL 根据用户订阅规则生成政策推送。
5. IF 政策来源包含正式发布机关或原文链接, 系统 SHALL 优先展示发布机关、文号、发布时间和原文链接。

### Requirement 20: 本地事件与安全资讯

**User Story:** AS 个人用户, I want 关注本地事故、车祸、安全宣传和网络安全资讯, so that 我可以及时了解身边和行业安全相关信息。

#### Acceptance Criteria

1. WHEN 用户启用本地事件频道, 系统 SHALL 按关注区域筛选事故、交通、车祸、消防、极端天气和公共安全资讯。
2. WHEN 用户启用安全宣传频道, 系统 SHALL 聚合官方安全提示、反诈宣传、交通安全、消防安全和应急管理信息。
3. WHEN 用户启用网络安全频道, 系统 SHALL 聚合漏洞通告、数据泄露新闻、安全厂商博客、攻防演练动态和行业安全资讯。
4. WHEN 本地事件或安全资讯达到紧急阈值, 系统 SHALL 生成高优先级推送。
5. IF 事件缺少权威来源或地区信息, 系统 SHALL 降低可信度评分并展示来源提示。

### Requirement 21: API 工具箱目录

**User Story:** AS 个人用户, I want 将 public-apis、枫雨 API 和其他公共 API 收录为工具箱, so that 我可以按分类查找、启用和测试各类 API 能力。

#### Acceptance Criteria

1. WHEN 系统同步 API 目录, 系统 SHALL 保存 API 名称、分类、描述、认证方式、HTTPS、CORS、文档链接、基础 URL、启用状态和风险标签。
2. WHEN 用户打开 API 工具箱, 系统 SHALL 按动物、动漫、反恶意软件、艺术设计、区块链、书籍、商业、日历、加密货币、货币兑换、数据验证、金融、天气、健康、机器学习、新闻、交通等分类展示 API。
3. WHEN 用户搜索 API, 系统 SHALL 按名称、分类、描述、认证方式和标签返回匹配结果。
4. WHEN 用户启用 API, 系统 SHALL 校验认证配置、限频配置和用途标签。
5. IF API 需要 key、OAuth 或付费额度, 系统 SHALL 在启用前提示配置要求和调用成本字段。

### Requirement 22: API 插件式调用与结果展示

**User Story:** AS 个人用户, I want 在本地工具箱中测试和调用已启用 API, so that 我可以把不同 API 的结果用于新闻、查询、娱乐、金融、开发和生活工具。

#### Acceptance Criteria

1. WHEN 用户打开某个 API 工具, 系统 SHALL 展示参数表单、示例请求、返回格式、调用限制和最近调用记录。
2. WHEN 用户提交 API 调用, 系统 SHALL 按连接器配置发送请求并展示结构化 JSON、文本、图片或文件结果。
3. WHEN API 返回结果可映射为资讯、热榜、市场行情、参考资料或工具结果, 系统 SHALL 允许用户保存到对应模块。
4. WHEN API 调用失败, 系统 SHALL 展示 HTTP 状态码、错误摘要、重试建议和日志入口。
5. IF API 被标记为敏感、账号相关、解析类或高成本, 系统 SHALL 在调用前展示风险标签和用途提示。

### Requirement 23: 个人每日信息中枢

**User Story:** AS 个人用户, I want 每天打开软件先看到技术、新闻、政策、热点和生活提醒, so that 我可以快速知道今天发生了什么并减少信息遗漏。

#### Acceptance Criteria

1. WHEN 用户打开系统首页, 系统 SHALL 展示今日总览、技术变化、重要新闻、政策变化、本地事件、热点吃瓜、天气地震和每日语录。
2. WHEN 系统生成首页卡片, 系统 SHALL 为每张卡片展示摘要、更新时间、重要程度、来源数量和打开详情入口。
3. WHEN 用户调整首页布局, 系统 SHALL 保存卡片顺序、隐藏状态和默认展开状态。
4. WHEN 某类信息达到高优先级, 系统 SHALL 在首页突出显示并进入推送队列。
5. IF 用户打开 API 工具箱, 系统 SHALL 通过独立按钮进入工具箱页面并保持首页主线聚焦每日信息。

### Requirement 24: 每日语录与情绪鼓励

**User Story:** AS 个人用户, I want 每天看到一句让我开心、放松或被鼓励的话, so that 我可以在看信息时获得一点积极反馈。

#### Acceptance Criteria

1. WHEN 用户打开首页, 系统 SHALL 展示每日语录、鼓励文案或轻松内容卡片。
2. WHEN 用户选择语录风格, 系统 SHALL 支持开心一点、别委屈、加油鼓励、冷静理性、幽默段子和技术人专属风格。
3. WHEN 用户点击换一句, 系统 SHALL 从本地语录库或已启用语录 API 获取新内容。
4. WHEN 系统展示语录, 系统 SHALL 标注来源类型、本地库或 API 来源。
5. IF 语录 API 请求失败, 系统 SHALL 使用本地语录库兜底展示。

### Requirement 25: 技术变化追踪

**User Story:** AS 个人用户, I want 每天了解技术、AI、开源、互联网产品和安全行业发生了哪些变化, so that 我可以保持技术敏感度。

#### Acceptance Criteria

1. WHEN 系统采集技术资讯, 系统 SHALL 按 AI、开源、编程语言、框架、云服务、安全、产品更新和大厂动态分类。
2. WHEN 系统识别版本发布、重大漏洞、框架更新或产品变化, 系统 SHALL 生成技术变化条目。
3. WHEN 用户打开技术变化页面, 系统 SHALL 展示变化摘要、影响范围、相关链接和推荐关注程度。
4. WHEN 技术变化匹配用户关注关键词, 系统 SHALL 生成技术推送。
5. IF 技术变化来源为非官方二手消息, 系统 SHALL 降低可信度评分并提示等待官方确认。

### Requirement 26: 阅读状态与个人收藏

**User Story:** AS 个人用户, I want 标记信息的阅读状态、收藏和稍后看, so that 我可以管理每天看到的重要内容。

#### Acceptance Criteria

1. WHEN 用户查看资讯、政策、技术变化、热点或语录, 系统 SHALL 支持标记未读、已读、稍后看、收藏和已忽略。
2. WHEN 用户打开收藏或稍后看页面, 系统 SHALL 按时间、频道、标签和来源筛选内容。
3. WHEN 用户忽略某条内容, 系统 SHALL 在首页和推送中心降低相似内容展示优先级。
4. WHEN 内容被自动聚合, 系统 SHALL 保留每个原始条目的阅读状态。
5. IF 用户清理阅读历史, 系统 SHALL 保留收藏内容并提示清理范围。

### Requirement 27: 个人关注清单

**User Story:** AS 个人用户, I want 配置我关心的关键词、公司、技术栈、城市、政策主题和人物, so that 系统可以优先展示与我相关的信息。

#### Acceptance Criteria

1. WHEN 用户创建关注项, 系统 SHALL 保存名称、类型、关键词、排除词、优先级和启用状态。
2. WHEN 系统采集到匹配关注项的内容, 系统 SHALL 提升首页排序和推送优先级。
3. WHEN 用户打开关注详情, 系统 SHALL 展示匹配内容、趋势变化和最近更新时间。
4. WHEN 关注项命中低可信来源, 系统 SHALL 展示可信度提示。
5. IF 关注项长期无结果, 系统 SHALL 提示用户调整关键词或来源。

### Requirement 28: 晨报与晚报

**User Story:** AS 个人用户, I want 每天固定时间看到晨报和晚报, so that 我可以用更少时间了解当天变化。

#### Acceptance Criteria

1. WHEN 到达用户配置的晨报或晚报时间, 系统 SHALL 生成本地摘要报告。
2. WHEN 报告生成完成, 系统 SHALL 展示技术变化、重要新闻、政策变化、本地事件、热点吃瓜、天气地震和每日语录。
3. WHEN 用户打开报告历史, 系统 SHALL 按日期查看历史晨报和晚报。
4. WHEN 用户导出报告, 系统 SHALL 支持 Markdown、HTML 和 PDF 友好结构。
5. IF 生成时部分来源失败, 系统 SHALL 使用已缓存内容并标注来源缺失。

### Requirement 29: 本地全文搜索

**User Story:** AS 个人用户, I want 搜索本地保存的新闻、政策、技术变化、热点、语录和 API 结果, so that 我可以快速找回看过或采集过的信息。

#### Acceptance Criteria

1. WHEN 用户输入搜索词, 系统 SHALL 在标题、摘要、正文、标签、来源和备注中检索。
2. WHEN 系统返回搜索结果, 系统 SHALL 支持按频道、时间、来源、阅读状态、收藏状态和可信度筛选。
3. WHEN 用户打开搜索结果, 系统 SHALL 高亮命中的关键词。
4. WHEN 内容被更新或删除索引, 系统 SHALL 同步更新本地搜索索引。
5. IF 搜索索引损坏, 系统 SHALL 提供重建索引操作。

### Requirement 30: 数据导出

**User Story:** AS 个人用户, I want 导出报告、列表、收藏和 API 调用结果, so that 我可以归档或分享自己的信息整理结果。

#### Acceptance Criteria

1. WHEN 用户导出单条内容, 系统 SHALL 支持 Markdown、HTML、JSON 和复制纯文本。
2. WHEN 用户导出列表或报告, 系统 SHALL 支持 Markdown、HTML、CSV 和 JSON。
3. WHEN 导出包含来源链接, 系统 SHALL 保留标题、来源、发布时间、采集时间和原始链接。
4. WHEN 导出包含个人配置或 API 调用结果, 系统 SHALL 默认脱敏 key、token、Cookie 和 Authorization 字段。
5. IF 导出失败, 系统 SHALL 展示失败原因和日志入口。

### Requirement 31: 备份与恢复

**User Story:** AS 个人用户, I want 备份和恢复配置、订阅规则、收藏、阅读状态和本地数据库, so that 我可以安全迁移或重装软件。

#### Acceptance Criteria

1. WHEN 用户创建备份, 系统 SHALL 打包配置、来源、关注清单、订阅规则、收藏、阅读状态和数据库快照。
2. WHEN 用户恢复备份, 系统 SHALL 校验备份版本、结构完整性和数据兼容性。
3. WHEN 备份包含敏感配置, 系统 SHALL 提示用户选择保留、脱敏或跳过。
4. WHEN 恢复操作执行前, 系统 SHALL 创建当前数据的保护快照。
5. IF 备份恢复失败, 系统 SHALL 回滚到恢复前状态并展示错误摘要。

### Requirement 32: 可信度解释

**User Story:** AS 个人用户, I want 看到每条内容的重要性和可信度原因, so that 我可以判断哪些信息值得关注。

#### Acceptance Criteria

1. WHEN 系统展示内容卡片, 系统 SHALL 展示重要程度和可信度评分。
2. WHEN 用户点击评分说明, 系统 SHALL 展示来源等级、来源数量、是否官方来源、转载情况、标题夸张度和时间新鲜度。
3. WHEN 内容来自低可信或单一来源, 系统 SHALL 给出明确提示。
4. WHEN 多来源内容互相印证, 系统 SHALL 提升可信度并展示印证来源数量。
5. IF 评分依据不足, 系统 SHALL 标记为待确认。

### Requirement 33: 来源健康度

**User Story:** AS 个人用户, I want 查看每个数据来源是否稳定可用, so that 我可以知道哪些来源需要调整或关闭。

#### Acceptance Criteria

1. WHEN 用户打开来源健康页, 系统 SHALL 展示来源成功率、失败次数、平均响应时间、最近成功时间和最近错误。
2. WHEN 来源连续失败, 系统 SHALL 自动降低采集频率并提示用户检查配置。
3. WHEN 来源恢复成功, 系统 SHALL 恢复正常采集节奏并记录恢复时间。
4. WHEN 用户测试来源, 系统 SHALL 展示请求状态、解析结果和错误摘要。
5. IF 来源被废弃或长期不可用, 系统 SHALL 建议停用或替换来源。

### Requirement 34: 离线模式

**User Story:** AS 个人用户, I want 在没有网络时继续查看最近缓存、收藏、历史报告和本地语录, so that 软件在离线状态下也可用。

#### Acceptance Criteria

1. WHEN 系统检测到网络不可用, 系统 SHALL 进入离线展示状态。
2. WHEN 用户处于离线状态, 系统 SHALL 允许查看最近缓存、收藏、稍后看、历史晨报晚报和本地语录库。
3. WHEN 用户执行需要联网的操作, 系统 SHALL 将任务加入待同步队列或提示网络需求。
4. WHEN 网络恢复, 系统 SHALL 执行待同步任务并刷新首页。
5. IF 缓存内容过期, 系统 SHALL 标注缓存时间和过期状态。

### Requirement 35: 隐私模式

**User Story:** AS 个人用户, I want 一键关闭外部 API 调用并只使用本地缓存、RSS 和手动来源, so that 我可以在敏感场景下减少外部请求。

#### Acceptance Criteria

1. WHEN 用户开启隐私模式, 系统 SHALL 暂停第三方 API 调用、可选 key 来源和工具箱 API 调试。
2. WHEN 隐私模式开启, 系统 SHALL 允许查看本地缓存、收藏、历史报告、RSS 已缓存内容和本地语录。
3. WHEN 用户尝试启用外部请求, 系统 SHALL 展示隐私模式提示并要求用户确认关闭隐私模式。
4. WHEN 隐私模式关闭, 系统 SHALL 恢复用户原有来源启用状态。
5. IF 隐私模式下存在待同步任务, 系统 SHALL 保留任务并等待用户关闭隐私模式后执行。

### Requirement 36: 特别收藏网页页签

**User Story:** AS 个人用户, I want 把特别关注的网页或站点加入特别收藏并生成独立页签, so that 我可以只查看这些网页发布的信息。

#### Acceptance Criteria

1. WHEN 用户将网页或站点加入特别收藏, 系统 SHALL 保存名称、入口 URL、匹配域名、匹配路径、分类、采集规则、启用状态和页签显示顺序。
2. WHEN 特别收藏来源发布或采集到新内容, 系统 SHALL 将内容关联到对应特别收藏页签。
3. WHEN 用户打开特别收藏页签, 系统 SHALL 只展示该网页、站点或配置规则匹配到的信息。
4. WHEN 用户配置特别收藏匹配范围, 系统 SHALL 支持精确 URL、同域名、指定路径前缀和自定义匹配规则。
5. WHEN 特别收藏来源命中多个页签, 系统 SHALL 在每个匹配页签中展示并保留同一条内容的统一阅读状态。
6. IF 特别收藏网页采集失败, 系统 SHALL 在该页签展示来源健康状态、最近错误和规则测试入口。
