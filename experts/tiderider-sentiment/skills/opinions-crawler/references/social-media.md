# 社媒舆情数据抓取完整参考

本文档按平台列出 OpenCLI 支持的社媒数据抓取命令，覆盖搜索、用户信息、内容列表、详情、评论、弹幕等场景。

## 通用技巧

### 输出格式

```bash
-f json    # JSON（推荐用于数据处理和管道）  ← 抓取时首选
-f table   # 表格（默认，适合人工查看）
-f csv     # CSV（可直接导入 Excel）
-f yaml    # YAML
-f md      # Markdown
```

### 数据量控制

```bash
--limit N       # 返回条数，各命令默认值不同
--pages N       # 翻页数（部分命令支持）
--start DATE    # 起始日期（如 weibo user-posts）
--end DATE      # 结束日期
```

### 频率控制

批量抓取时务必控制频率，避免触发平台风控：

```bash
for id in $(cat ids.txt); do
  opencli <site> <command> "$id" -f json > "data_${id}.json"
  sleep 3  # 间隔 3 秒
done
```

---

## Bilibili（B站） — `opencli bilibili`

### 热搜 & 排行榜

```bash
opencli bilibili hot --limit 10 -f json        # 综合热门
opencli bilibili ranking --limit 10 -f json     # 排行榜
```

**返回字段**（hot）：title, author, play, danmaku（弹幕数）, url 等

### 搜索

```bash
opencli bilibili search "关键词" --limit 20 -f json
```

### 用户相关

```bash
# 用户投稿列表
opencli bilibili user-videos <uid> --limit 20 -f json

# 关注列表
opencli bilibili following <uid> --limit 20 -f json   # 查看他人的关注

# 用户动态
opencli bilibili feed <uid> --limit 10 -f json             # 指定用户动态
opencli bilibili feed 老番茄 --pages 2 --type video        # 按用户名 + 翻页
```

### 视频详情

```bash
# 支持 BV 号、完整 URL、短链接
opencli bilibili video BV1xx411c7mD -f json
opencli bilibili video https://www.bilibili.com/video/BV1xx411c7mD/ -f json
```

**返回字段**：title, author, duration, play（播放量）, danmaku（弹幕总数）, reply（评论总数）, like, coin, favorite, share, pubdate, description 等

### 视频评论

```bash
# 顶层评论（--limit 支持 1-50）
opencli bilibili comments BV1xx411c7mD --limit 50 -f json

# 楼中楼回复（--parent 传入顶层评论的 rpid）
opencli bilibili comments BV1xx411c7mD --parent <rpid> --limit 20 -f json
```

**返回字段**：rpid（评论ID）, content, author, likes, replies（回复数）, time 等

**注意**：
- B站仅支持 1 层嵌套，`--parent` 返回该根评论的直接回复列表（最多 20 条）
- `comments` 输出中每行带 `rpid` 字段，用于楼中楼查询
- 空评论列表会抛出 `EmptyResultError`

### 视频弹幕

```bash
opencli bilibili danmaku --url "https://www.bilibili.com/video/BV1xx411c7mD" -f json
```

**提示**：先用 `video` 命令获取弹幕总量（danmaku 字段），弹幕量大的视频建议关注高弹幕时段。

### 视频字幕

```bash
opencli bilibili subtitle BV1xx411c7mD --lang zh-CN          # CC 人工字幕
opencli bilibili subtitle BV1xx411c7mD --lang ai-zh           # AI 生成字幕
```

### AI 视频摘要

```bash
opencli bilibili summary BV1xx411c7mD -f json
```

**返回**：官方 AI 生成的视频摘要和时间戳大纲

---

## 微博 — `opencli weibo`

### 热搜

```bash
opencli weibo hot --limit 10 -f json
```

**返回字段**：rank, title, hot_value（热度值）, url 等

### 搜索

```bash
opencli weibo search "关键词" --limit 20 -f json
```

### 用户信息

```bash
opencli weibo user <uid> -f json
```

### 用户帖子列表

```bash
# 基础用法
opencli weibo user-posts <uid> --limit 20 -f json

# 指定日期范围
opencli weibo user-posts <uid> --start 2026-06-01 --end 2026-06-25 --limit 20 -f json
```

### 微博详情

```bash
opencli weibo post <id> -f json
```

**注意**：`id` 从 `feed`、`search` 或 `user-posts` 输出中获取。

### 微博评论

```bash
opencli weibo comments <id> --limit 50 -f json
```

### 时间线

```bash
# 推荐流（默认）
opencli weibo feed --limit 20 -f json

# 关注流（严格按时间排序）
opencli weibo feed --type following --limit 20 -f json
```

---

## 小红书 — `opencli xiaohongshu`

### 搜索

```bash
opencli xiaohongshu search "关键词" --limit 20 -f json
```

### 推荐 Feed

```bash
opencli xiaohongshu feed --limit 20 -f json
```

### 笔记详情 & 评论

```bash
# 笔记评论
opencli xiaohongshu comments <note_id> --limit 50 -f json
```

### 用户相关

```bash
# 用户信息
opencli xiaohongshu user <user_id> -f json

# 创作者笔记列表
opencli xiaohongshu creator-notes <user_id> --limit 20 -f json

# 创作者主页信息
opencli xiaohongshu creator-profile <user_id> -f json

# 创作者数据统计
opencli xiaohongshu creator-stats <user_id> -f json
```

---

## 知乎 — `opencli zhihu`

### 热榜

```bash
opencli zhihu hot --limit 10 -f json
```

### 搜索

```bash
opencli zhihu search "关键词" --limit 20 -f json
```

### 问题 & 回答

```bash
opencli zhihu question <question_id> --limit 20 -f json
```

**返回字段**：title, detail, answers（回答列表含作者、内容、点赞数）等

---

## X (Twitter) — `opencli twitter`

### 搜索

```bash
opencli twitter search "关键词" --limit 20 -f json
```

### 热门趋势

```bash
opencli twitter trending -f json
```

### 用户相关

```bash
# 用户信息
opencli twitter profile <username> -f json

# 用户时间线
opencli twitter timeline <username> --limit 20 -f json

# 用户帖子列表
opencli twitter tweets <username> --limit 20 -f json

# 关注 / 粉丝列表
opencli twitter following <username> --limit 20 -f json
opencli twitter followers <username> --limit 20 -f json
```

### 推文详情

```bash
# 查看单条推文
opencli twitter post <tweet_id> -f json
```

### 列表

```bash
opencli twitter lists -f json                    # 列表信息
opencli twitter list-tweets <list_id> -f json    # 列表中的推文
```

---

## YouTube — `opencli youtube`

### 搜索

```bash
opencli youtube search "关键词" --limit 20 -f json
```

### 视频详情

```bash
opencli youtube video <video_id> -f json
```

**返回字段**：title, views, likes, duration, channel, description 等

### 评论

```bash
opencli youtube comments <video_id> --limit 50 -f json
```

### 字幕

```bash
opencli youtube transcript <video_id> -f json
```

### 频道

```bash
opencli youtube channel <channel_id> -f json
```

---

## Reddit — `opencli reddit`

### 热门 / 首页

```bash
opencli reddit hot --limit 20 -f json
opencli reddit frontpage --limit 20 -f json
opencli reddit popular --limit 20 -f json
```

### 搜索

```bash
opencli reddit search "关键词" --limit 20 -f json
```

### 子版块 & 帖子

```bash
# 子版块帖子
opencli reddit subreddit <name> --limit 20 -f json

# 帖子详情
opencli reddit read <post_url> -f json
```

### 用户相关

```bash
opencli reddit user <username> -f json
opencli reddit user-posts <username> --limit 20 -f json
opencli reddit user-comments <username> --limit 20 -f json
```

---

## HackerNews — `opencli hackernews`

```bash
opencli hackernews top --limit 20 -f json
opencli hackernews new --limit 20 -f json
opencli hackernews best --limit 20 -f json
opencli hackernews ask --limit 20 -f json
opencli hackernews show --limit 20 -f json
opencli hackernews search "关键词" --limit 20 -f json
```

---

## 抖音 — `opencli douyin`

> 需登录 `creator.douyin.com`（抖音创作者中心）

```bash
# 账号与作品
opencli douyin profile                                    # 账号信息
opencli douyin videos --limit 10                         # 作品列表

# 搜索与发现
opencli douyin hashtag search "关键词" --limit 10         # 搜索话题
opencli douyin hashtag hot --limit 10                     # 热点词

# 数据统计
opencli douyin stats <video_id>                           # 作品数据分析
```

**前置条件**：Chrome 已登录 creator.douyin.com，账号需有创作者中心权限。

---

## TikTok — `opencli tiktok`

> 需登录 tiktok.com

```bash
# 搜索与发现
opencli tiktok search "关键词" --limit 20 -f json          # 搜索视频
opencli tiktok explore --limit 20 -f json                  # 推荐热门视频

# 用户相关
opencli tiktok profile --username <user> -f json           # 用户信息
opencli tiktok user <username> --limit 20 -f json          # 用户最近视频
opencli tiktok following --limit 20                         # 关注列表

# 直播
opencli tiktok live --limit 10 -f json                     # 直播列表

# 创作者数据（需 TikTok Studio 权限）
opencli tiktok creator-videos --limit 20 -f json           # 创作者视频+指标
```

**输出字段**（explore/user）：id, author, title, plays, likes, comments, shares, createTime, url 等。

---

## Instagram — `opencli instagram`

> 需登录 instagram.com

```bash
# 用户相关
opencli instagram profile <username> -f json               # 用户信息
opencli instagram user <username> --limit 10 -f json       # 最近帖子
opencli instagram search <username> --limit 5              # 搜索用户
opencli instagram followers <username> --limit 20          # 粉丝列表
opencli instagram following <username> --limit 20          # 关注列表

# 发现
opencli instagram explore --limit 20                        # 推荐帖子
```

---

## 百度贴吧 — `opencli tieba`

> 需 Chrome 可访问 tieba.baidu.com

```bash
# 热门
opencli tieba hot --limit 10 -f json                       # 贴吧热议榜

# 搜索
opencli tieba search "关键词" --limit 20                    # 全站搜索帖子

# 帖子列表
opencli tieba posts "吧名" --limit 20                       # 某吧帖子列表

# 帖子详情
opencli tieba read <thread_id> --limit 20                   # 帖子楼中楼
opencli tieba read <thread_id> --page 2 --limit 20          # 翻页
```

---

## 豆瓣 — `opencli douban`

> 需登录 douban.com

```bash
# 搜索（支持电影/图书/音乐三种类型）
opencli douban search "流浪地球"
opencli douban search --type book "三体"
opencli douban search --type music "周杰伦"

# 榜单
opencli douban top250 --limit 10 -f json                   # 电影 Top 250
opencli douban movie-hot --limit 10                         # 电影热门
opencli douban book-hot --limit 10                          # 图书热门

# 详情与评论
opencli douban subject <subject_id> -f json                 # 条目详情
opencli douban subject <subject_id> --type book -f json     # 图书详情
opencli douban reviews                                      # 短评列表
```

---

## 虎扑 — `opencli hupu`

> 部分命令需登录 bbs.hupu.com（hot 公开可用）

```bash
# 热门
opencli hupu hot --limit 10 -f json                        # 虎扑首页热帖

# 搜索
opencli hupu search "湖人" --limit 20                       # 搜索帖子

# 帖子详情与回复
opencli hupu detail <tid> --replies true                    # 帖子+热门回复
opencli hupu detail <tid> -f json                           # JSON 格式
```

**hot 输出字段**：rank, tid, title, lights（亮回复数）, replies, forum, is_hot, url。

---

## 雪球 — `opencli xueqiu`

> 需登录 xueqiu.com

```bash
# 热门内容
opencli xueqiu hot --limit 10 -f json                      # 热门动态
opencli xueqiu feed --limit 20 -f json                      # 首页时间线
opencli xueqiu hot-stock --limit 10                         # 热门股票榜

# 搜索与行情
opencli xueqiu search "茅台"                                # 搜索股票
opencli xueqiu stock SH600519                               # 实时行情

# 讨论与评论
opencli xueqiu comments SH600519 --limit 20                 # 股票讨论动态

# 财报日期
opencli xueqiu earnings-date SH600519 --next                # 预计财报日

# 自选股
opencli xueqiu watchlist -f json                            # 自选股列表
```

---

## 今日头条 — `opencli toutiao`

```bash
# 热搜（公开，无需登录）
opencli toutiao hot --limit 20 -f json

# 创作者后台文章数据（需登录 mp.toutiao.com）
opencli toutiao articles --page 1 -f json
opencli toutiao articles --page 2
```

**hot 输出字段**：rank, group_id, title, query, hot_value, label（热/新/沸）, url。

---

## 即刻 — `opencli jike`

> 需登录 web.okjike.com

```bash
# 动态流
opencli jike feed --limit 20 -f json                        # 首页动态流

# 搜索
opencli jike search "AI" --limit 20                          # 搜索帖子

# 帖子详情与评论
opencli jike post <post_id>                                  # 帖子详情+评论

# 话题
opencli jike topic <topic_id>                                # 话题详情

# 用户
opencli jike user <user_id>                                  # 用户资料
```

**列表输出**：feed/search/user 输出 `id` 字段，可传入 `post` 命令查看详情。

---

## Bluesky — `opencli bluesky`

> 公开 AT Protocol API，无需登录

```bash
# 用户
opencli bluesky profile --handle bsky.app -f json           # 用户信息
opencli bluesky user --handle <handle> --limit 10            # 最近帖子

# 搜索与趋势
opencli bluesky search --query "AI" --limit 10               # 搜索用户
opencli bluesky trending --limit 10                           # 趋势话题

# 社交关系
opencli bluesky followers --handle <handle> --limit 10       # 粉丝
opencli bluesky following --handle <handle>                  # 关注

# 帖子线程
opencli bluesky thread --uri "at://did:.../..."              # 帖子+回复

# Feeds
opencli bluesky feeds --limit 10                             # 热门 Feed 生成器

# Starter Packs
opencli bluesky starter-packs --handle <handle>              # 用户的 Starter Packs
```

---

## V2EX — `opencli v2ex`

> 大部分命令走公开 API，无需登录

```bash
# 热门与最新
opencli v2ex hot --limit 10 -f json                         # 热门主题
opencli v2ex latest --limit 20                               # 最新主题
opencli v2ex daily --limit 10                                # 每日热门（需登录）

# 节点
opencli v2ex node python                                     # 某节点下的主题
opencli v2ex nodes --limit 10                                # 所有节点（按帖子数排序）

# 用户
opencli v2ex user Livid                                      # 用户发的帖子
opencli v2ex member Livid                                    # 用户资料

# 帖子详情与回复
opencli v2ex topic <id>                                      # 帖子详情
opencli v2ex replies <id>                                    # 帖子回复
```

---

## 36氪 — `opencli 36kr`

```bash
# 热榜
opencli 36kr hot --limit 10 -f json                          # 热榜文章
opencli 36kr hot --type renqi --limit 10                     # 人气热榜
opencli 36kr hot --type zonghe --limit 10                    # 综合热榜

# 搜索
opencli 36kr search "AI" --limit 10                          # 搜索文章

# 文章详情
opencli 36kr article <article_id>                            # 文章全文
opencli 36kr article https://36kr.com/p/<article_id>         # 支持 URL

# 最新（公开 RSS，无需浏览器）
opencli 36kr news --limit 20
```

---

## Medium — `opencli medium`

```bash
# 热门 Feed
opencli medium feed --limit 10 -f json                       # 通用热门
opencli medium feed --topic programming -f json              # 按话题过滤

# 搜索
opencli medium search "AI" --limit 10                        # 关键词搜索

# 用户
opencli medium user @username                                # 用户文章

# Tag（公开 RSS，最快）
opencli medium tag programming --limit 10                    # Tag 下最新
opencli medium tag artificial-intelligence --limit 20
```

---

## 大众点评 — `opencli dianping`

> 需登录 dianping.com

```bash
# 搜索商户
opencli dianping search "火锅" --city beijing --limit 10     # 按城市搜索
opencli dianping search "咖啡" --city 上海 -f json            # JSON 输出
opencli dianping search "理发"                               # 使用当前 Cookie 城市

# 商户详情
opencli dianping shop <shop_id>                               # 商户详情
opencli dianping shop https://www.dianping.com/shop/<id>     # 支持 URL
```

**search 输出字段**：rank, shop_id, name, rating, reviews（评论数）, price, cuisine, district, url。

**注意**：网页版搜索限制 1-15 条/页，`--city` 支持中文名/拼音/数字 ID。触发验证码时需手动打开 captcha URL 完成验证后重试。

---

## 电商评论采集

### 淘宝 — `opencli taobao`

> 需登录 taobao.com

```bash
# 搜索商品
opencli taobao search "关键词" --limit 20

# 商品详情
opencli taobao detail <item_id>

# 商品评价
opencli taobao reviews <item_id>
```

### 京东 — `opencli jd`

> 需登录 jd.com

```bash
# 商品详情（价格、店铺、规格）
opencli jd item <sku_id> -f json
opencli jd item <sku_id> --images 5                          # 限制图片数量
```

### 什么值得买 — `opencli smzdm`

> 需登录 smzdm.com

```bash
opencli smzdm search "关键词" --limit 20 -f json             # 搜索商品评测/优惠
```

---

## 图片/创意社区

### Pixiv — `opencli pixiv`

> 需登录 pixiv.net

```bash
# 排行榜
opencli pixiv ranking --limit 20 -f json                     # 日榜
opencli pixiv ranking --mode weekly                          # 周榜
opencli pixiv ranking --mode monthly                         # 月榜

# 搜索
opencli pixiv search "初音ミク" --limit 20                    # 按关键词搜索
opencli pixiv search "風景" --mode safe                       # SFW 过滤
opencli pixiv search "オリジナル" --page 2 --limit 30         # 翻页

# 用户与作品
opencli pixiv user <user_id>                                  # 画师信息
opencli pixiv illusts <user_id> --limit 10                    # 画师作品列表
opencli pixiv detail <illust_id>                              # 作品详情
```

**输出字段示例**（ranking/search）：rank, title, author, user_id, illust_id, pages, bookmarks, tags, url。

---

## 其他值得关注的舆情平台

| 平台 | 站点名 | 关键命令 | 数据策略 | 说明 |
|------|--------|---------|----------|------|
| 掘金 | `juejin` | `hot`, `recommend` | 🌐 Public | 国内技术社区热榜 |
| 牛客网 | `nowcoder` | `hot`, `trending`, `search`, `jobs`, `creators` | 🌐/🔐 | 校招社区，面经讨论 |
| LinkedIn | `linkedin` | `search`, `posts`, `timeline`, `profile-read` | 🔐 Browser | 职业社交，招聘动态 |
| Facebook | `facebook` | `feed`, `profile`, `search`, `groups`, `events` | 🔐 Browser | 国际社交平台 |
| 一亩三分地 | `1point3acres` | `hot`, `latest`, `search`, `thread` | 🌐 Public | 北美华人社区 |
| ProductHunt | `producthunt` | `posts`, `today`, `hot` | 🌐/🔐 | 产品发布社区 |
| IMDb | `imdb` | `search`, `title`, `top`, `trending`, `reviews` | 🌐/🔐 | 电影评分评论 |
| Substack | `substack` | `feed`, `search`, `publication` | 🔐 Browser | Newsletter 平台 |
| 新浪博客 | `sinablog` | `hot`, `search`, `article`, `user` | 🔐 Browser | 博客平台 |
| 微信公众号 | `weixin` | `search`, `download` | 🌐/🔐 | 微信公众平台文章 |
| BOSS直聘 | `boss` | `search`（支持 `--city`） | 🔐 Browser | 招聘舆情 |

查看完整 165+ 平台列表：

```bash
opencli list
opencli <site> --help
```

## 舆情数据实用工作流

### 工作流 1：热点话题全平台追踪

```bash
# 国内热搜
opencli weibo hot --limit 20 -f json > hot_weibo.json
opencli zhihu hot --limit 20 -f json > hot_zhihu.json
opencli bilibili hot --limit 20 -f json > hot_bilibili.json
opencli toutiao hot --limit 20 -f json > hot_toutiao.json
opencli tieba hot --limit 20 -f json > hot_tieba.json
opencli 36kr hot --limit 20 -f json > hot_36kr.json

# 国际热搜
opencli twitter trending -f json > hot_twitter.json
opencli reddit hot --limit 20 -f json > hot_reddit.json
opencli bluesky trending --limit 10 -f json > hot_bluesky.json
```

### 工作流 2：关键词全平台舆情搜索

```bash
KEYWORD="某品牌新品"

# 国内平台
opencli bilibili search "$KEYWORD" --limit 10 -f json > "search_bilibili.json"
opencli weibo search "$KEYWORD" --limit 10 -f json > "search_weibo.json"
opencli xiaohongshu search "$KEYWORD" --limit 10 -f json > "search_xhs.json"
opencli zhihu search "$KEYWORD" --limit 10 -f json > "search_zhihu.json"
opencli toutiao hot --limit 20 -f json > "search_toutiao.json"

# 国际平台
opencli twitter search "$KEYWORD" --limit 10 -f json > "search_twitter.json"
opencli youtube search "$KEYWORD" --limit 10 -f json > "search_youtube.json"
opencli tiktok search "$KEYWORD" --limit 10 -f json > "search_tiktok.json"
opencli reddit search "$KEYWORD" --limit 10 -f json > "search_reddit.json"

# 投资社区
opencli xueqiu search "$KEYWORD" -f json > "search_xueqiu.json"
```

### 工作流 3：视频舆情深度分析

```bash
BV="BV1xx411c7mD"

# 视频基本信息
opencli bilibili video "$BV" -f json > video_info.json

# 弹幕
opencli bilibili danmaku --url "https://www.bilibili.com/video/$BV" -f json > danmaku.json

# 评论（顶层 + 热门楼中楼）
opencli bilibili comments "$BV" --limit 50 -f json > comments.json

# 获取高回复评论的楼中楼
# 从 comments.json 中提取 replies > 0 的 rpid，逐条抓取
```

### 工作流 4：用户画像采集

```bash
# B站 UP 主分析
UID="2"
opencli bilibili user-videos "$UID" --limit 50 -f json > up_videos.json
opencli bilibili feed "$UID" --limit 20 -f json > up_dynamics.json

# 微博用户分析
WEIBO_UID="1670458304"
opencli weibo user "$WEIBO_UID" -f json > weibo_profile.json
opencli weibo user-posts "$WEIBO_UID" --start 2026-01-01 --end 2026-06-25 --limit 50 -f json > weibo_posts.json
```
