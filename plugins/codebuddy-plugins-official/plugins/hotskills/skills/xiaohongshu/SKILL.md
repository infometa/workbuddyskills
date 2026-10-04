---
name: xiaohongshu
description: |
  小红书（RedNote）内容工具。使用场景：
  - 搜索小红书笔记并获取详情
  - 获取首页推荐列表
  - 获取帖子详情（正文、图片、互动数据、评论）
  - 发表评论 / 回复评论
  - 获取用户主页和笔记列表
  - 点赞、收藏帖子
  - 发布图文或视频笔记
  - 热点话题跟踪与分析报告
  - 帖子导出为长图
  触发词示例：
  - "搜一下小红书上的XX"
  - "跟踪一下小红书上的XX热点"
  - "分析小红书上关于XX的讨论"
  - "小红书XX话题报告"
  - "生成XX的小红书舆情报告"
---

# 小红书 MCP Skill

基于 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 封装的 shell 脚本工具集。

## 前置条件

```bash
cd scripts/
./install-check.sh    # 检查依赖（xiaohongshu-mcp、jq、python3）
./start-mcp.sh        # 启动 MCP 服务（默认端口 18060）
./status.sh           # 确认已登录
```

未登录时需扫码：`mcp-call.sh get_login_qrcode` 获取二维码，用小红书 App 扫码。

服务端口可通过 `MCP_URL` 环境变量覆盖（默认 `http://localhost:18060/mcp`）。

## 核心数据流

**重要：** 大多数操作需要 `feed_id` + `xsec_token` 配对。这两个值从搜索/推荐/用户主页结果中获取，**不可自行构造**。

```
search_feeds / list_feeds / user_profile
        │
        ▼
  返回 feeds 数组，每个 feed 包含:
  ├── id          → 用作 feed_id
  ├── xsecToken   → 用作 xsec_token
  └── noteCard    → 标题、作者、封面、互动数据
        │
        ▼
  get_feed_detail(feed_id, xsec_token)
        │
        ▼
  返回完整笔记: 正文、图片列表、评论列表
  评论中包含 comment_id、user_id（用于回复评论）
```

## 脚本参考

| 脚本 | 用途 | 参数 |
|------|------|------|
| `search.sh <关键词>` | 搜索笔记 | 关键词 |
| `recommend.sh` | 首页推荐 | 无 |
| `post-detail.sh <feed_id> <xsec_token>` | 帖子详情+评论 | 从搜索结果获取 |
| `comment.sh <feed_id> <xsec_token> <内容>` | 发表评论 | 从搜索结果获取 |
| `user-profile.sh <user_id> <xsec_token>` | 用户主页+笔记 | 从搜索结果获取 |
| `track-topic.sh <话题> [选项]` | 热点分析报告 | `--limit N` `--output file` `--feishu` |
| `export-long-image.sh` | 帖子导出长图 | `--posts-file json -o output.jpg` |
| `mcp-call.sh <tool> [json_args]` | 通用 MCP 调用 | 见下方工具表 |
| `start-mcp.sh` | 启动服务 | `--headless=false` `--port=N` |
| `stop-mcp.sh` | 停止服务 | 无 |
| `status.sh` | 检查登录 | 无 |
| `install-check.sh` | 检查依赖 | 无 |

## MCP 工具详细参数

### search_feeds — 搜索笔记

```json
{"keyword": "咖啡", "filters": {"sort_by": "最新", "note_type": "图文", "publish_time": "一周内"}}
```

filters 可选字段：
- `sort_by`: 综合 | 最新 | 最多点赞 | 最多评论 | 最多收藏
- `note_type`: 不限 | 视频 | 图文
- `publish_time`: 不限 | 一天内 | 一周内 | 半年内
- `search_scope`: 不限 | 已看过 | 未看过 | 已关注
- `location`: 不限 | 同城 | 附近

### get_feed_detail — 帖子详情

```json
{"feed_id": "...", "xsec_token": "...", "load_all_comments": true, "limit": 20}
```

- `load_all_comments`: false(默认) 返回前10条，true 滚动加载更多
- `limit`: 加载评论上限（仅 load_all_comments=true 时生效），默认 20
- `click_more_replies`: 是否展开二级回复，默认 false
- `reply_limit`: 跳过回复数超过此值的评论，默认 10
- `scroll_speed`: slow | normal | fast

### post_comment_to_feed — 发表评论

```json
{"feed_id": "...", "xsec_token": "...", "content": "写得真好！"}
```

### reply_comment_in_feed — 回复评论

```json
{"feed_id": "...", "xsec_token": "...", "content": "谢谢！", "comment_id": "...", "user_id": "..."}
```

`comment_id` 和 `user_id` 从 get_feed_detail 返回的评论列表中获取。

### user_profile — 用户主页

```json
{"user_id": "...", "xsec_token": "..."}
```

`user_id` 从 feed 的 `noteCard.user.userId` 获取，`xsec_token` 使用该 feed 的 `xsecToken`。

### like_feed — 点赞/取消

```json
{"feed_id": "...", "xsec_token": "..."}
{"feed_id": "...", "xsec_token": "...", "unlike": true}
```

### favorite_feed — 收藏/取消

```json
{"feed_id": "...", "xsec_token": "..."}
{"feed_id": "...", "xsec_token": "...", "unfavorite": true}
```

### publish_content — 发布图文

```json
{"title": "标题(≤20字)", "content": "正文(≤1000字)", "images": ["/path/to/img.jpg"], "tags": ["美食","旅行"]}
```

- `images`: 至少1张，支持本地路径或 HTTP URL
- `tags`: 可选，话题标签
- `schedule_at`: 可选，定时发布（ISO8601，1小时~14天内）

### publish_with_video — 发布视频

```json
{"title": "标题", "content": "正文", "video": "/path/to/video.mp4"}
```

### 其他工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `check_login_status` | 无 | 检查登录状态 |
| `list_feeds` | 无 | 获取首页推荐 |
| `get_login_qrcode` | 无 | 获取登录二维码（Base64 PNG） |
| `delete_cookies` | 无 | 删除 cookies，重置登录 |

## 热点跟踪

自动搜索 → 拉取详情 → 生成 Markdown 报告。

```bash
./track-topic.sh "DeepSeek" --limit 5
./track-topic.sh "春节旅游" --limit 10 --output report.md
./track-topic.sh "iPhone 16" --limit 5 --feishu    # 导出飞书
```

报告包含：概览统计、热帖详情（正文+热评）、评论关键词、趋势分析。

## 长图导出

将帖子导出为白底黑字的 JPG 长图。

```bash
./export-long-image.sh --posts-file posts.json -o output.jpg
```

posts.json 格式：
```json
[{
  "title": "标题", "author": "作者", "stats": "1.3万赞",
  "desc": "正文摘要", "images": ["https://..."],
  "per_image_text": {"1": "第2张图的说明"}
}]
```

依赖：Python 3.10+、Pillow。

## 注意事项

- Cookies 有效期约 30 天，过期需重新扫码
- 首次启动会下载 headless 浏览器（~150MB）
- 同一账号避免多客户端同时操作
- 发布限制：标题≤20字符，正文≤1000字符，日发布≤50条
- Linux 服务器无桌面环境需安装 xvfb（`apt-get install xvfb`，脚本自动管理）
