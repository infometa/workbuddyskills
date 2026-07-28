---
name: opinions-crawler
description: |
  基于 OpenCLI 的舆情数据抓取技能。覆盖国内外主流社媒（搜索、用户信息、帖子/视频列表、视频详情及互动量、评论、弹幕等）和商店平台数据爬取。当用户需要抓取舆情数据、采集社媒内容、获取商店评分评论、或者需要安装和配置 OpenCLI 时使用。
  Triggers: 舆情数据、爬取社媒、抓取评论、获取弹幕、商店评分、opencli 安装、舆情监控、社交媒体数据采集、app store review、google play 评分、xiaohongshu/bilibili/weibo/twitter/youtube 数据抓取
agent_created: true
---

# Opinions Crawler — 基于 OpenCLI 的舆情数据抓取

基于 [OpenCLI](https://github.com/jackwener/OpenCLI)（23,500+ Star）构建的舆情数据抓取方案。OpenCLI 通过 Chrome 扩展复用浏览器登录态，无需处理账号密码、验证码，零 LLM 成本即可从 100+ 平台获取结构化数据。

## 适用场景

- 社媒舆情监控：热搜、关键词搜索、用户内容追踪
- 竞品分析：商店评分变化、用户评价情感分析
- 内容采集：视频详情、互动数据、评论、弹幕
- 用户画像：社媒用户主页信息、历史发帖

## 前置条件

- Node.js >= 20.0.0
- Chrome/Chromium 浏览器
- 目标网站已在 Chrome 中登录

## 快速安装

```bash
# 1. 安装 CLI
npm install -g @jackwener/opencli

# 2. 下载 Chrome 扩展
# 从 https://github.com/jackwener/opencli/releases 下载最新 opencli-extension.zip
# 解压后，打开 chrome://extensions，开启「开发者模式」，
# 点击「加载已解压的扩展程序」，选择解压后的文件夹

# 3. 验证安装
opencli doctor
# 期望输出: [OK] Daemon / [OK] Extension / [OK] Connectivity

# 4. 查看所有支持的命令
opencli list
```

详细安装指引见 `references/installation.md`。

## 舆情数据抓取速查

### 通用选项

所有命令均支持：

| 选项 | 说明 |
|------|------|
| `-f json` | JSON 格式输出（推荐用于数据解析） |
| `-f table\|csv\|yaml\|md` | 其他输出格式 |
| `--limit N` | 结果数量（默认通常为 20） |
| `-v` | 详细模式，显示调试信息 |

### 国内社媒

#### Bilibili（B站）

```bash
# 热搜 / 排行榜
opencli bilibili hot --limit 10 -f json
opencli bilibili ranking --limit 10 -f json

# 搜索
opencli bilibili search "关键词" --limit 10 -f json

# 用户信息 & 投稿列表
opencli bilibili user-videos <uid> --limit 20 -f json          # 用户投稿列表
opencli bilibili following <uid> --limit 20 -f json          # 查看他人的关注

# 视频详情 (标题、作者、时长、播放量、弹幕数、评论数等)
opencli bilibili video BV1xx411c7mD -f json
opencli bilibili video https://www.bilibili.com/video/BV1xx411c7mD/ -f json

# 视频评论 (支持楼中楼)
opencli bilibili comments BV1xx411c7mD --limit 50 -f json      # 顶层评论
opencli bilibili comments BV1xx411c7mD --parent <rpid> --limit 20 -f json  # 楼中楼回复

# 视频字幕
opencli bilibili subtitle BV1xx411c7mD --lang zh-CN            # CC字幕
opencli bilibili subtitle BV1xx411c7mD --lang ai-zh             # AI字幕

# AI 视频摘要
opencli bilibili summary BV1xx411c7mD -f json
```

#### 微博

> ⚠️ `weibo hot` 当前版本返回 404，暂不可用。其他命令（search、user、feed 等）需登录态。

```bash
# 搜索
opencli weibo search "关键词" --limit 20 -f json

# 用户信息
opencli weibo user <uid> -f json

# 用户帖子列表（支持日期范围）
opencli weibo user-posts <uid> --start 2026-06-01 --end 2026-06-25 --limit 20 -f json

# 微博详情
opencli weibo post <id> -f json

# 微博评论
opencli weibo comments <id> --limit 20 -f json

# 首页时间线
opencli weibo feed --limit 20 -f json                  # 推荐流
opencli weibo feed --type following --limit 20 -f json # 关注流
```

#### 小红书

```bash
# 搜索笔记
opencli xiaohongshu search "关键词" --limit 20 -f json

# 推荐 Feed
opencli xiaohongshu feed --limit 20 -f json

# 笔记评论
opencli xiaohongshu comments <note_id> --limit 20 -f json

# 用户信息 & 笔记列表
opencli xiaohongshu user <user_id> -f json

# 创作者数据
opencli xiaohongshu creator-notes <user_id> --limit 20 -f json
opencli xiaohongshu creator-profile <user_id> -f json
opencli xiaohongshu creator-stats <user_id> -f json
```

#### 知乎

> ⚠️ `zhihu hot` 当前版本可能返回空数据，建议优先使用搜索功能。

```bash
# 热榜
opencli zhihu hot --limit 10 -f json

# 搜索
opencli zhihu search "关键词" --limit 20 -f json

# 问题详情 & 回答
opencli zhihu question <question_id> --limit 20 -f json
```

#### 抖音

```bash
# 需登录 creator.douyin.com（创作者中心）
opencli douyin profile -f json                            # 账号信息
opencli douyin videos --limit 20 -f json                  # 作品列表
opencli douyin hashtag search "关键词" --limit 10          # 搜索话题
opencli douyin hashtag hot --limit 10                      # 热点词
opencli douyin stats <video_id>                            # 作品数据分析
```

#### 百度贴吧

```bash
opencli tieba hot --limit 10 -f json                      # 热议榜
opencli tieba search "关键词" --limit 20                   # 全站搜索
opencli tieba posts "吧名" --limit 20                      # 吧内帖子
opencli tieba read <thread_id> --limit 20                  # 帖子详情
```

#### 豆瓣

> ⚠️ 豆瓣命令需要 Chrome 中已登录 douban.com，否则返回 AUTH_REQUIRED 错误。

```bash
opencli douban search "关键词"                             # 电影/图书/音乐搜索
opencli douban top250 --limit 10 -f json                  # 电影 Top 250
opencli douban subject <id> -f json                       # 条目详情+评分
opencli douban reviews                                     # 短评列表
opencli douban movie-hot --limit 10                        # 电影热门
```

#### 虎扑

```bash
opencli hupu hot --limit 10 -f json                       # 首页热帖（公开可用）
opencli hupu search "关键词" --limit 20                    # 搜索帖子
opencli hupu detail <tid> --replies true                   # 帖子+热门回复
```

#### 雪球

> ⚠️ 雪球命令需要 Chrome 中已登录 xueqiu.com，否则返回 HTTP 400 错误。

```bash
opencli xueqiu hot --limit 10 -f json                     # 热门动态
opencli xueqiu search "茅台"                               # 搜索股票
opencli xueqiu stock SH600519                              # 实时行情
opencli xueqiu comments SH600519 --limit 20                # 股票讨论
opencli xueqiu hot-stock --limit 10                        # 热门股票榜
```

#### 今日头条 & 36氪

```bash
# 今日头条热搜（公开）
opencli toutiao hot --limit 20 -f json

# 36氪热榜
opencli 36kr hot --limit 10 -f json
opencli 36kr search "关键词" --limit 10
```

#### 即刻

```bash
opencli jike feed --limit 20 -f json                      # 动态流
opencli jike search "关键词" --limit 20                    # 搜索帖子
opencli jike post <post_id>                               # 帖子+评论
opencli jike topic <topic_id>                             # 话题详情
```

### 国际社媒

#### X (Twitter)

```bash
# 搜索推文
opencli twitter search "关键词" --limit 20 -f json

# 热门趋势
opencli twitter trending -f json

# 用户时间线
opencli twitter timeline <username> --limit 20 -f json

# 用户信息
opencli twitter profile <username> -f json

# 推文详情（含互动数据）
opencli twitter tweets <tweet_id> -f json

# 用户帖子列表
opencli twitter user-posts <username> --limit 20 -f json

# 关注/粉丝列表
opencli twitter following <username> --limit 20 -f json
opencli twitter followers <username> --limit 20 -f json
```

#### YouTube

```bash
# 搜索视频
opencli youtube search "关键词" --limit 20 -f json

# 视频详情（标题、播放量、点赞数等）
opencli youtube video <video_id> -f json

# 视频评论
opencli youtube comments <video_id> --limit 50 -f json

# 频道信息
opencli youtube channel <channel_id> -f json
```

#### Reddit

> ⚠️ `reddit hot` 当前版本可能返回解析错误，建议优先使用 `reddit search` 或 `reddit subreddit`。

```bash
# 热门
opencli reddit hot --limit 20 -f json

# 搜索
opencli reddit search "关键词" --limit 20 -f json

# 子版块
opencli reddit subreddit <name> --limit 20 -f json

# 用户信息 & 帖子
opencli reddit user <username> -f json
opencli reddit user-posts <username> --limit 20 -f json
opencli reddit user-comments <username> --limit 20 -f json
```

### 商店平台数据

OpenCLI 暂未内置 Apple App Store / Google Play 等商店适配器。推荐以下方案：

**方案一：appstore-review-cli（推荐）**

专为商店评分和评论设计的 CLI 工具，支持 Apple App Store 和 Google Play：

```bash
pip install appstore-review-cli

# Apple App Store
appstore-reviews search "App名称"
appstore-reviews reviews <app_id> --stars 2 --days 30 --pages 5
appstore-reviews reviews <app_id> --keywords crash,bug --stars 2
appstore-reviews reviews <app_id> --format json

# Google Play
appstore-reviews --store google search "App名称"
appstore-reviews --store google reviews <package_name> --stars 2 --days 30
appstore-reviews --store google reviews <package_name> --format csv

# 版本对比
appstore-reviews version-diff <app_id> --old 4.23.0 --new 4.29.0 --pages 5

# 评分趋势
appstore-reviews trend <app_id> --period week --pages 5
```

**方案二：OpenCLI browser 命令**

使用 `opencli browser` 直接操控浏览器访问商店页面：

```bash
# 打开商店页面进行手动/半自动抓取
opencli browser open "https://play.google.com/store/apps/details?id=<package_id>"
opencli browser open "https://apps.apple.com/app/id<app_id>"
opencli browser screenshot
opencli browser get --selector ".review-text"
```

**方案三：为商店编写自定义适配器**

如果商店数据是长期需求，可使用 OpenCLI 的适配器框架：

```bash
opencli explore "https://play.google.com/store/apps/details?id=com.example" --site googleplay
opencli synthesize googleplay
```

详细内容见 `references/app-stores.md`。

## 批量抓取与数据处理

### 结构化输出管道

```bash
# JSON 输出 + jq 过滤
opencli bilibili hot --limit 10 -f json | jq '.[] | {title: .title, views: .play}'

# CSV 输出（直接导入 Excel）
opencli bilibili hot --limit 20 -f csv > bilibili_hot.csv

# 批量抓取多个视频评论
for bv in BV1xx1 BV1xx2 BV1xx3; do
  opencli bilibili comments "$bv" --limit 50 -f json > "comments_${bv}.json"
  sleep 3  # 控制频率，避免触发风控
done
```

### 注意事项

- **频率控制**：批量抓取时在命令间添加 `sleep 2-5`，避免触发平台限流
- **登录态**：确保 Chrome 中目标网站已登录，否则需要登录态的命令会返回空数据或报错
- **弹幕数据**：当前版本（v1.8.4）不支持 `danmaku` 命令，B站弹幕数可从 `video` 命令的 `danmaku` 字段获取
- **平台可用性**：部分平台命令因 API 变更可能暂时不可用（如 weibo hot 返回 404、zhihu hot 返回空），建议优先使用搜索功能

## 参考文档

- `references/installation.md` — OpenCLI 详细安装与配置指南
- `references/social-media.md` — 各社媒平台完整命令参考与数据字段说明
- `references/app-stores.md` — 商店平台评分与评论抓取详细方案
