# Hashtag Trending 数据查询

> ⚠️ **表路径说明**：本文档中所有 SQL 均使用 `project.dataset.<table>` 占位符，实际 BigQuery 完整路径待确认。  
> 涉及的表名：`marketing_hub_hashtag_trending_exolyt`、`marketing_hub_hashtag_trending_tiktok`、  
> `marketing_hub_hashtag_trending_tiktok_gaming`、`marketing_hub_hashtag_top_video`。  
> 使用前请将 `project.dataset` 替换为正确的 BigQuery 项目和数据集路径。

## 这份文档适合谁

这份文档适合不看代码但需要查数 / 写报告 / 解释榜单的业务或分析同学，以及需要快速回忆接口逻辑的后端维护者。

它能帮你查到 hashtag 热点榜单数据，包括今日榜、7天/30天趋势、gaming 特殊榜单、新上榜 hashtag，以及相关的 rank 变化、趋势数据和补充视频信息。

能解决的问题：今天最热 hashtag 是什么？近7天/30天哪些 hashtag 趋势上升？gaming 领域的热点？哪些 hashtag 是新崛起的？rank 怎么算的？为什么没数据？

---

## 快速判断：你现在想查什么？

- 想看今天最热 hashtag 数据 → 看"场景 1：今日榜单"
- 想看近 7 天 / 30 天 hashtag 趋势 → 看"场景 2：7天/30天趋势榜"
- 想看 gaming / 特殊 source 的榜单 → 看"场景 3：Gaming 榜单"
- 想解释 rank / rank_diff 怎么算 → 看"场景 4：Rank 和 rank_diff 解释"
- 想补充 hashtag 的视频数据 → 看"场景 5：补充视频数据"
- 当前时间范围没数据 → 看"场景 6：无数据兜底"
- 想看新上榜 / 新崛起的 hashtag → 看"场景 7：新上榜 hashtag"

---

## 你可以查什么数据

| 想回答什么问题 | 条件                    | 表                                           | 备注                               |
| -------------- | ----------------------- | -------------------------------------------- | ---------------------------------- |
| 今日榜单       | time_range=today        | marketing_hub_hashtag_trending_exolyt        | 即时榜，基于 Exolyt 数据           |
| 7天趋势        | time_range=last_7_days  | marketing_hub_hashtag_trending_tiktok        | 周趋势，基于 TikTok 数据           |
| 30天趋势       | time_range=last_30_days | marketing_hub_hashtag_trending_tiktok        | 月趋势，基于 TikTok 数据           |
| Gaming 榜单    | source=tiktok_gaming    | marketing_hub_hashtag_trending_tiktok_gaming | 独立口径，gaming 领域              |
| 新上榜 hashtag | newly_listed_only=true  | 对应表                                       | 一年内首次进入 Top 100             |
| Rank 解释      | 任何榜单                | 对应表 + ranking 查询                        | 后端重新计算 rank                  |
| 趋势数据       | 任何榜单                | 对应表                                       | trend 字段，时间序列               |
| 补充视频       | last_7_days 或 gaming   | marketing_hub_hashtag_top_video              | 每个 hashtag+country 的 top 3 视频 |
| 无数据兜底     | 查询为空                | 对应表                                       | 查找最近有数据的日期               |

---

## 查询前先判断

- 是否是特殊 source（如 gaming）：如果是，路由到 gaming 表
- 是否 today vs 7天/30天：today 用 exolyt 表，其他用 tiktok 表
- 是否只看新上榜 hashtag：newly_listed_only=true 时，额外过滤一年内首次进入 Top 100 的
- 是否主榜单 vs 补充数据：主榜单用 hashtag 表，视频用 top_video 表
- 是否存在排序限制：gaming 表只能按 tweets_views 排序
- 是否需要兜底查询：如果主查询无数据，查最近有数据的日期

---

## 按场景怎么查

### 场景 1：想看今日榜单，怎么查？

#### 适合什么场景：
- 需要查看今天实时最热的 hashtag
- 分析当前热点趋势

#### 你会拿它回答什么问题：
- 今天哪个 hashtag 最热门？
- 今天各国的 hashtag 排名如何？

#### 查哪张表：
- `project.dataset.marketing_hub_hashtag_trending_exolyt`

#### 查的时候抓住：
- time_range = 'today'
- date >= start_time AND date <= end_time
- lower(country) in (...)
- lower(source) in (...) （categories 映射到 source）
- 排序字段：tweets_views 或 tweets_posts
- rank 是后端用 ROW_NUMBER() 动态计算的

```sql
SELECT 
  ROW_NUMBER() OVER (ORDER BY tweets_views DESC) AS rank,
  date, source, category, country, time_range, 
  hashtag, tweets_posts, tweets_views
FROM `project.dataset.marketing_hub_hashtag_trending_exolyt` 
WHERE date >= '2026-04-02' 
  AND date <= '2026-04-02'
  AND lower(time_range) = 'today'
  AND lower(country) in ('us', 'jp')
  AND lower(source) in ('all categories')
ORDER BY tweets_views DESC
LIMIT 10 OFFSET 0
```

#### 查数注意点：
- rank 不是表里的字段，是查询时用窗口函数算的
- 没有 rank_diff 和 trend 字段（exolyt 表不提供）
- 搜索时用 lower(hashtag) like '%search%'
- 分页用 LIMIT 和 OFFSET

#### 简短后端逻辑小结：
后端先路由到 exolyt 表，执行 list 和 ranking 查询（排除搜索），用 goroutine 并行跑，然后后处理 rank 和 rank_diff（但 exolyt 没有前一天数据，所以 rank_diff=0）。

### 场景 2：想看近 7 天 / 30 天趋势，怎么查？

#### 适合什么场景：
- 分析 hashtag 的中长期趋势
- 查看哪些 hashtag 正在上升

#### 你会拿它回答什么问题：
- 过去7天/30天哪个 hashtag 增长最快？
- hashtag 的趋势曲线是什么样的？

#### 查哪张表：
- `project.dataset.marketing_hub_hashtag_trending_tiktok`

#### 查的时候抓住：
- time_range = 'last_7_days' 或 'last_30_days'
- date >= start_time AND date <= end_time
- lower(country) in (...)
- lower(source) in (...) （categories 映射到 source）
- 排序字段：tweets_views, tweets_posts, rank_diff 等
- rank 和 rank_diff 是表里的字段，但后端会重新计算
- trend 是 JSON 数组，记录每日值

```sql
SELECT 
  date, source, category, country, time_range, hashtag, 
  tweets_posts, tweets_views, rank_diff, rank, 
  TO_JSON_STRING(trend) as trend, is_promoted
FROM `project.dataset.marketing_hub_hashtag_trending_tiktok` 
WHERE date >= '2026-03-26' 
  AND date <= '2026-04-02'
  AND lower(time_range) = 'last_7_days'
  AND lower(country) in ('us')
  AND lower(source) in ('all categories')
ORDER BY tweets_views DESC
LIMIT 10 OFFSET 0
```

#### 查数注意点：
- rank_diff = 前一天 rank - 当天 rank，正数表示排名上升
- trend 字段是 JSON 字符串，需要解析成数组
- 如果 time_range=last_7_days，会额外查 top_video 表获取视频
- 搜索时排除在 ranking 查询中（ranking 需要原始排名）

#### 简短后端逻辑小结：
路由到 tiktok 表，并行执行 list、total、current ranking、previous ranking 四个查询。后处理时用 ranking 结果覆盖表里的 rank，计算 rank_diff = prev_rank - current_rank。

### 场景 3：想看 gaming / 特殊 source，怎么查？

#### 适合什么场景：
- 分析 gaming 领域的 hashtag 热点
- 查看特定类别的榜单

#### 你会拿它回答什么问题：
- gaming 里最热的 hashtag 是哪些？
- 按 views 或 growth 排序的 gaming 榜？

#### 查哪张表：
- `project.dataset.marketing_hub_hashtag_trending_tiktok_gaming`

#### 查的时候抓住：
- source = 'tiktok_gaming'
- date >= start_time AND date <= end_time
- lower(country) in (...)
- crawl_types in ('by_views', 'by_growth') 映射到 order_by_list 数组
- 只能按 tweets_views 排序
- tweets_views_trend 是数组，最后一个元素是当天值

```sql
SELECT 
  date, country, time_range, hashtag, tweets_views,
  TO_JSON_STRING(tweets_views_trend) as tweets_views_trend
FROM `project.dataset.marketing_hub_hashtag_trending_tiktok_gaming` 
WHERE date >= '2026-03-26' 
  AND date <= '2026-04-02'
  AND lower(country) in ('us')
  AND EXISTS(SELECT 1 FROM UNNEST(order_by_list) AS ob WHERE ob = 'by_views')
ORDER BY tweets_views DESC
LIMIT 10 OFFSET 0
```

#### 查数注意点：
- 没有 tweets_posts、source、category、rank_diff、is_promoted 字段（返回0或空）
- tweets_views_trend 数组转换为 trend 格式：最后一个元素=当天，前面的=前几天
- 总是包含 top_video_list，不管 time_range
- crawl_types 用 UNNEST(order_by_list) 过滤

#### 简短后端逻辑小结：
检测 source='tiktok_gaming' 路由到 gaming 表，执行类似 tiktok 的并行查询，但后处理时转换 trend 格式，设置缺失字段为0。

### 场景 4：想解释 rank / rank_diff，怎么查？

#### 适合什么场景：
- 理解榜单排名逻辑
- 分析排名变化

#### 你会拿它回答什么问题：
- rank 怎么算的？
- rank_diff 正数负数什么意思？

#### 查哪张表：
- 对应主表 + ranking 子查询（排除搜索条件）

#### 查的时候抓住：
- ranking 查询：同主查询条件，但无搜索，无分页，按 sort_item DESC 排序
- rank = 当前日期的排名位置
- rank_diff = 前一天 rank - 当天 rank

```sql
-- 主查询（list）
SELECT hashtag, rank, rank_diff FROM main_table WHERE ... ORDER BY tweets_views DESC

-- ranking 查询（用于计算 rank）
SELECT hashtag, ROW_NUMBER() OVER (ORDER BY tweets_views DESC) AS rank
FROM main_table 
WHERE date = '2026-04-02' AND ... -- 无搜索
ORDER BY tweets_views DESC
```

#### 查数注意点：
- rank 不是直接从表取，是后端用 ranking 查询结果映射算的
- rank_diff 需要前一天数据，如果前一天没数据则为0
- exolyt 表没有前一天 ranking，所以 rank_diff 总是0

#### 简短后端逻辑小结：
并行执行当前日和前一日 ranking 查询（条件同主查询但排除搜索），然后用 map 存储 hashtag-country -> rank，list 结果时匹配计算 rank 和 rank_diff。

### 场景 5：想补充 hashtag 的视频数据，怎么查？

#### 适合什么场景：
- 获取 hashtag 相关的热门视频
- 分析视频内容

#### 你会拿它回答什么问题：
- 这个 hashtag 下最热门的视频是哪些？

#### 查哪张表：
- `project.dataset.marketing_hub_hashtag_top_video`

#### 查的时候抓住：
- hashtag in (...) AND lower(country) in (...)
- date >= end_time - 7天
- 用 ROW_NUMBER() OVER (PARTITION BY hashtag, country) 获取每个组合的 top 3

```sql
SELECT hashtag, country, video_id, video_url, channel_name, 
  ROW_NUMBER() OVER (PARTITION BY hashtag, country ORDER BY views DESC) AS rn
FROM `project.dataset.marketing_hub_hashtag_top_video`
WHERE hashtag in ('#example1', '#example2')
  AND lower(country) in ('us')
  AND date >= '2026-03-26'
  AND date <= '2026-04-02'
QUALIFY ROW_NUMBER() OVER (PARTITION BY hashtag, country ORDER BY views DESC) <= 3
```

#### 查数注意点：
- 每个 hashtag+country 组合独立 top 3，不混排名
- 只在 last_7_days (tiktok) 或 gaming 时触发
- 时间范围固定为 end_time 前7天

#### 简短后端逻辑小结：
主查询后，如果条件满足，收集所有 hashtag+country 对，批量查询 top_video 表，用 partition by 获取每个组的 top 3。

### 场景 6：当前没数据，怎么查？

#### 适合什么场景：
- 查询时间范围没有数据
- 找到最近有数据的日期

#### 你会拿它回答什么问题：
- 最近什么时候有 hashtag 数据？

#### 查哪张表：
- 对应主表（排除时间条件）

#### 查的时候抓住：
- 同主查询条件，但去掉 date 过滤
- 查 MAX(date) 或最新有数据的日期

```sql
SELECT MAX(date) as latest_date
FROM `project.dataset.marketing_hub_hashtag_trending_tiktok`
WHERE lower(time_range) = 'last_7_days'
  AND lower(country) in ('us')
  AND lower(source) in ('all categories')
```

#### 查数注意点：
- 排除 date 条件，找任何时间的有数据日期
- 用于前端显示"最近数据日期"

#### 简短后端逻辑小结：
主查询返回0条时，执行兜底查询找最新日期，返回 has_data_date 字段。

### 场景 7：想看新上榜 hashtag，怎么查？

#### 适合什么场景：
- 分析新兴热点和趋势
- 发现新崛起的 hashtag

#### 你会拿它回答什么问题：
- 哪些 hashtag 是最近新上榜的？
- 一年内首次进入 Top 100 的 hashtag 有哪些？

#### 查哪张表：
- `project.dataset.marketing_hub_hashtag_trending_tiktok` （非 today）
- `project.dataset.marketing_hub_hashtag_trending_exolyt` （today）
- `project.dataset.marketing_hub_hashtag_trending_tiktok_gaming` （gaming）

#### 查的时候抓住：
- newly_listed_only = true
- time_range != 'today' （不支持 today）
- 后端会构建 CTE 查找过去一年内是否出现过
- TikTok 表：用 NOT IN 过滤已出现过的 hashtag
- Exolyt/Gaming 表：用 QUALIFY 计算 Top 100/200，然后 NOT EXISTS 过滤

```sql
-- TikTok 表示例（最简单）
WITH previous_listed_hashtag AS (
  SELECT DISTINCT hashtag
  FROM `project.dataset.marketing_hub_hashtag_trending_tiktok`
  WHERE date >= DATE_SUB('2026-04-02', INTERVAL 365 DAY)
    AND date < '2026-04-02'
    AND lower(time_range) = 'last_7_days'
    AND lower(country) in ('us')
    AND lower(source) in ('all categories')
)
SELECT hashtag, tweets_views, rank
FROM `project.dataset.marketing_hub_hashtag_trending_tiktok`
WHERE hashtag NOT IN (SELECT hashtag FROM previous_listed_hashtag)
  AND date >= '2026-03-26'
  AND date <= '2026-04-02'
  AND lower(time_range) = 'last_7_days'
  AND lower(country) in ('us')
  AND lower(source) in ('all categories')
ORDER BY tweets_views DESC
LIMIT 10 OFFSET 0
```

#### 查数注意点：
- 只适用于非 today 的榜单（today 不支持 newly_listed_only）
- "新上榜"定义为一年内首次进入 Top 100
- TikTok 表基于预过滤数据，性能最好
- Exolyt/Gaming 表动态计算 Top 100/200，性能稍差
- 排序字段受限：Exolyt 只能 tweets_views/tweets_posts，Gaming 只能 tweets_views

#### 简短后端逻辑小结：
根据表类型构建不同 CTE（TikTok 用 NOT IN，Exolyt/Gaming 用 QUALIFY + NOT EXISTS），过滤出一年内首次出现的 hashtag，应用于 list 和 total 查询。